from pydantic import FilePath, root_validator, BaseModel, Field
from typing import Optional, Sequence, Dict, Mapping, Union
try: #to get literal in python 3.7, it was added to typing in 3.8
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from pathlib import Path
import logging
#supress geopandas debug logs
logging.disable(logging.DEBUG)
import json
json.encoder.FLOAT_REPR = str #lambda x: format(x, '%.09f')
import geopandas as gpd
import pandas as pd
import shutil
from enum import Enum
from ngen.config.realization import NgenRealization, Realization, CatchmentRealization
from ngen.config.multi import MultiBMI
from .model import ModelExec, PosInt, Configurable
from .parameter import Parameter, Parameters
from .calibration_cathment import CalibrationCatchment, AdjustableCatchment
from .calibration_set import CalibrationSet, UniformCalibrationSet
#HyFeatures components
from hypy.hydrolocation import NWISLocation # type: ignore
from hypy.nexus import Nexus # type: ignore

class NgenStrategy(str, Enum):
    """
    """
    #multiplier = "multiplier"
    uniform = "uniform"
    explicit = "explicit"
    independent = "independent"

def _params_as_df(params: Mapping[str, Parameters], name: str = None):
    if not name:
        dfs = []
        for k,v in params.items():
            df = pd.DataFrame([s.__dict__ for s in v])
            df['model'] = k
            df.rename(columns={'name':'param'}, inplace=True)
            dfs.append(df)
        return pd.concat(dfs)
    else:
        p = params.get(name, [])
        df = pd.DataFrame([s.__dict__ for s in p])
        df['model'] = name
        df.rename(columns={'name':'param'}, inplace=True)
        return df

def _map_params_to_realization(params: Mapping[str, Parameters], realization: Realization):
    # don't even think about calibration multiple formulations at once just yet..
    module = realization.formulations[0].params
    
    if isinstance(module, MultiBMI):
        dfs = []
        for m in module.modules:
            dfs.append(_params_as_df(params, m.params.model_name))
        return pd.concat(dfs)
    else:
        return _params_as_df(params, module.model_name)

class NgenBase(ModelExec):
    """
        Data class specific for Ngen
        
        Inherits the ModelParams attributes and Configurable interface
    """
    type: Literal['ngen']
    #required fields
    # TODO with the ability to generate realizations programaticaly, this may not be
    # strictly required any longer...for now it "works" so we are using info from
    # an existing realization to build various calibration realization configs
    # but we should probably take a closer look at this in the near future
    realization: FilePath
    catchments: FilePath
    nexus: FilePath
    crosswalk: FilePath
    ngen_realization: Optional[NgenRealization]
    #optional fields
    partitions: Optional[FilePath]
    parallel: Optional[PosInt]
    params: Optional[ Mapping[str, Parameters] ] 
    #dependent fields
    binary: str = 'ngen'
    args: Optional[str]

    #private, not validated
    _catchments: Sequence['CalibrationCatchment'] = []
    _catchment_hydro_fabric: gpd.GeoDataFrame
    _nexus_hydro_fabric: gpd.GeoDataFrame
    _x_walk: pd.Series

    class Config:
        """Override configuration for pydantic BaseModel
        """
        underscore_attrs_are_private = True
        use_enum_values = True
        smart_union = True

    def __init__(self, **kwargs):
        #Let pydantic work its magic
        super().__init__(**kwargs)
        #now we work ours
        #Make a copy of the config file, just in case
        shutil.copy(self.realization, str(self.realization)+'_original')
       
        #Read the catchment hydrofabric data
        self._catchment_hydro_fabric = gpd.read_file(self.catchments)
        self._catchment_hydro_fabric = self._catchment_hydro_fabric.rename(columns=str.lower)
        self._catchment_hydro_fabric.set_index('id', inplace=True)
        self._nexus_hydro_fabric = gpd.read_file(self.nexus)
        self._nexus_hydro_fabric = self._nexus_hydro_fabric.rename(columns=str.lower)
        self._nexus_hydro_fabric.set_index('id', inplace=True)

        self._x_walk = pd.Series()
        with open(self.crosswalk) as fp:
            data = json.load(fp)
            for id, values in data.items():
                gage = values.get('Gage_no')
                if gage:
                    if not isinstance(gage, str):
                        gage = gage[0]
                    if gage != "":
                        self._x_walk[id] = gage

        #Read the calibration specific info
        with open(self.realization) as fp:
            data = json.load(fp)
        self.ngen_realization = NgenRealization(**data)

    @property
    def config_file(self) -> Path:
        """Path to the configuration file for this calibration

        Returns:
            Path: to ngen realization configuration file
        """
        return self.realization

    @property
    def hy_catchments(self) -> Sequence['CalibrationCatchment']:
        """A list of Catchments for calibration
        
        These catchments hold information about the parameters/calibration data for that catchment

        Returns:
            Sequence[CalibrationCatchment]: A list like container of CalibrationCatchment objects
        """
        return self._catchments

    @root_validator
    def set_defaults(cls, values: Dict):
        """Compose default values 

            This validator will set/adjust the following data values for the class
            args: if not explicitly configured, ngen args default to
                  catchments "all" nexus "all" realization
            binary: if parallel is defined and valid then the binary command is adjusted to
                    mpirun -n parallel binary
                    also, if parallel is defined the args are adjusted to include the partition field
                    catchments "" nexus "" realization partitions
        Args:
            values (dict): mapping of key/value pairs to validate

        Returns:
            Dict: validated key/value pairs with default values set for known keys
        """
        parallel = values.get('parallel')
        partitions = values.get('partitions')
        binary = values.get('binary')
        args = values.get('args')
        catchments = values.get('catchments')
        nexus = values.get('nexus')
        realization = values.get('realization')

        custom_args = False
        if( args is None ):
            args = '{} "all" {} "all" {}'.format(catchments, nexus, realization)
            values['args'] = args
        else:
            custom_args = True

        if( parallel is not None and partitions is not None):
            binary = f'mpirun -n {parallel} {binary}'
            if not custom_args:
                # only append this if args weren't already custom defined by user
                args += f' {partitions}'
            values['binary'] = binary
            values['args'] = args

        return values

    @root_validator(pre=True) #pre-check, don't validate anything else if this fails
    def check_for_partitions(cls, values: dict):
        """Validate that if parallel is used and valid that partitions is passed (and valid)

        Args:
            values (dict): values to validate

        Raises:
            ValueError: If no partition field is defined and parallel support (greater than 1) is requested.

        Returns:
            dict: Values valid for this rule
        """
        parallel = values.get('parallel')
        partitions = values.get('partitions')
        if(parallel is not None and parallel > 1 and partitions is None):
            raise ValueError("Must provide partitions if using parallel")
        return values

    def update_config(self, i: int, params: 'pd.DataFrame', id: str = None):
        """_summary_

        Args:
            i (int): _description_
            params (pd.DataFrame): _description_
            id (str): _description_
        """
        
        if id is None: #Update global
            module = self.ngen_realization.global_config.formulations[0].params
        else: #update specific catchment
            module = self.ngen_realization.catchments[id].formulations[0].params

        groups = params.set_index('param').groupby('model')
        if isinstance(module, MultiBMI):
            for m in module.modules:
                name = m.params.model_name
                if name in groups.groups:
                    p = groups.get_group(name)
                    m.params.model_params = p[str(i)].to_dict()
        else:
            p = groups.get_group(module.model_name)
            module.model_params = p[str(i)].to_dict()
        
        with open(self.realization, 'w') as fp:
                fp.write( self.ngen_realization.json(by_alias=True, exclude_none=True, indent=4))
    
class NgenExplicit(NgenBase):
    
    strategy: Literal[NgenStrategy.explicit]

    def __init__(self, **kwargs):
        #Let pydantic work its magic
        super().__init__(**kwargs)
        #now we work ours
        start_t = self.ngen_realization.time.start_time
        end_t = self.ngen_realization.time.end_time
        #Setup each calibration catchment
        for id, catchment in self.ngen_realization.catchments.items():
            
            if hasattr(catchment, 'calibration'):
                try:
                    fabric = self._catchment_hydro_fabric.loc[id]
                except KeyError:
                    continue
                try:
                    nwis = self._x_walk[id]
                except KeyError:
                    raise(RuntimeError("Cannot establish mapping of catchment {} to nwis location in cross walk".format(id)))
                try:
                    nexus_data = self._nexus_hydro_fabric.loc[fabric['toid']]
                except KeyError:
                    raise(RuntimeError("No suitable nexus found for catchment {}".format(id)))

                #establish the hydro location for the observation nexus associated with this catchment
                location = NWISLocation(nwis, nexus_data.name, nexus_data.geometry)
                nexus = Nexus(nexus_data.name, location, (), id)
                output_var = catchment.formulations[0].params.main_output_variable
                #read params from the realization calibration definition
                params = {model:[Parameter(**p) for p in params] for model, params in catchment.calibration.items()}
                params = _map_params_to_realization(params, catchment)
                self._catchments.append(CalibrationCatchment(self.workdir, id, nexus, start_t, end_t, fabric, output_var, params))

    def update_config(self, i: int, params: 'pd.DataFrame', id: str):
        """_summary_

        Args:
            i (int): _description_
            params (pd.DataFrame): _description_
            id (str): _description_
        """

        if id is None:
            raise RuntimeError("NgenExplicit calibration must recieve an id to update, not None")
        
        super().update_config(i, params, id)

class NgenIndependent(NgenBase):
    
    strategy: Literal[NgenStrategy.independent]
    params: Mapping[str, Parameters] #required in this case...

    def __init__(self, **kwargs):
        #Let pydantic work its magic
        super().__init__(**kwargs)
        #now we work ours
        start_t = self.ngen_realization.time.start_time
        end_t = self.ngen_realization.time.end_time
        #Setup each calibration catchment
        catchments = []
        eval_nexus = []
        catchment_realizations = {}
        g_conf = self.ngen_realization.global_config.dict(by_alias=True)
        g_conf.pop('forcing')
        for id in self._catchment_hydro_fabric.index:
            #Copy the global configuration into each catchment
            catchment_realizations[id] = CatchmentRealization(**g_conf)
        self.ngen_realization.catchments = catchment_realizations
        
        for id, catchment in self.ngen_realization.catchments.items():#data['catchments'].items():
            try:
                fabric = self._catchment_hydro_fabric.loc[id]
            except KeyError: # This probaly isn't strictly required since we built these from the index
                continue
            try:
                nexus_data = self._nexus_hydro_fabric.loc[fabric['toid']]
            except KeyError:
                raise(RuntimeError("No suitable nexus found for catchment {}".format(id)))
            nwis = None
            try:
                nwis = self._x_walk.loc[id.replace('cat', 'wb')]
            except KeyError:
                try: 
                    nwis = self._x_walk.loc[id]
                except KeyError:
                    nwis = None
            if nwis is not None:
                #establish the hydro location for the observation nexus associated with this catchment
                location = NWISLocation(nwis, nexus_data.name, nexus_data.geometry)
                nexus = Nexus(nexus_data.name, location, (), id)
                eval_nexus.append( nexus ) # FIXME why did I make this a tuple???
            else:
                #in this case, we don't care if all nexus are observable, just need one downstream
                #FIXME use the graph to work backwards from an observable nexus to all upstream catchments
                #and create independent "sets"
                nexus = Nexus(nexus_data.name, None, (), id)
            #FIXME pick up params per catchmment somehow???
            params = _map_params_to_realization(self.params, catchment)
            catchments.append(AdjustableCatchment(self.workdir, id, nexus, params))

        if len(eval_nexus) != 1:
            raise RuntimeError( "Currently only a single nexus in the hydrfabric can be gaged")
        # FIXME hard coded routing file name...
        self._catchments.append(CalibrationSet(catchments, eval_nexus[0], "flowveldepth_Ngen1.h5", start_t, end_t))

class NgenUniform(NgenBase):
    """
        Uses a global ngen configuration and permutes just this global parameter space
        which is applied to each catchment in the hydrofabric being simulated.
    """
    strategy: Literal[NgenStrategy.uniform]
    params: Mapping[str, Parameters] #required in this case...

    def __init__(self, **kwargs):
        #Let pydantic work its magic
        super().__init__(**kwargs)
        #now we work ours
        start_t = self.ngen_realization.time.start_time
        end_t = self.ngen_realization.time.end_time
        eval_nexus = []
        
        for id, toid in self._catchment_hydro_fabric['toid'].iteritems():
            #look for an observable nexus
            nexus_data = self._nexus_hydro_fabric.loc[toid]
            nwis = None
            try:
                nwis = self._x_walk.loc[id.replace('cat', 'wb')]
            except KeyError:
                try: 
                    nwis = self._x_walk.loc[id]
                except KeyError:
                    #not an observable nexus, try the next one
                    continue
                #establish the hydro location for the observation nexus associated with this catchment
            location = NWISLocation(nwis, nexus_data.name, nexus_data.geometry)
            nexus = Nexus(nexus_data.name, location, (), id)
            eval_nexus.append( nexus )
        if len(eval_nexus) != 1:
            raise RuntimeError( "Currently only a single nexus in the hydrfabric can be gaged")
        # FIXME hard coded routing file name...
        params = _params_as_df(self.params)
        self._catchments.append(UniformCalibrationSet(eval_nexus=eval_nexus[0], routing_output="flowveldepth_Ngen1.h5", start_time=start_t, end_time=end_t, params=params))
            
class Ngen(BaseModel, Configurable, smart_union=True):
    __root__: Union[NgenExplicit, NgenIndependent, NgenUniform] = Field(discriminator="strategy")

    #proxy methods for Configurable
    def get_args(self) -> str:
        return self.__root__.get_args()
    def get_binary(self) -> str:
        return self.__root__.get_binary()
    def update_config(self, *args, **kwargs):
        return self.__root__.update_config(*args, **kwargs)
    #proxy methods for model
    @property
    def hy_catchments(self):
        return self.__root__.hy_catchments

    @property
    def strategy(self):
        return self.__root__.strategy
