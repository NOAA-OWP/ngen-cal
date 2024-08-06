from __future__ import annotations

from pydantic import FilePath, root_validator, BaseModel, Field
from typing import Optional, Sequence, Dict, Mapping, Union
try: #to get literal in python 3.7, it was added to typing in 3.8
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from pathlib import Path
import logging
import warnings
#supress geopandas debug logs
logging.disable(logging.DEBUG)
import json
json.encoder.FLOAT_REPR = str #lambda x: format(x, '%.09f')
import geopandas as gpd
import pandas as pd
import shutil
from enum import Enum
import re
from ngen.config.realization import NgenRealization, Realization, CatchmentRealization
from ngen.config.multi import MultiBMI
from .model import ModelExec, PosInt, Configurable
from .parameter import Parameter, Parameters
from .calibration_cathment import CalibrationCatchment, AdjustableCatchment
from .calibration_set import CalibrationSet, UniformCalibrationSet
from .ngen_hooks.ngen_output import TrouteOutput, NgenSaveOutput
#HyFeatures components
from hypy.hydrolocation import NWISLocation
from hypy.nexus import Nexus
from hypy.catchment import Catchment


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
    hydrofabric: Optional[FilePath]
    eval_feature: Optional[str]
    catchments: Optional[FilePath]
    nexus: Optional[FilePath]
    crosswalk: Optional[FilePath]
    ngen_realization: Optional[NgenRealization]
    routing_output: Path = Path("flowveldepth_Ngen.csv")
    #optional fields
    partitions: Optional[FilePath]
    parallel: Optional[PosInt]
    params: Optional[ Mapping[str, Parameters] ]
    #dependent fields
    binary: str = 'ngen'
    args: Optional[str]

    #private, not validated
    _catchments: Sequence[CalibrationCatchment] = []
    _catchment_hydro_fabric: gpd.GeoDataFrame
    _nexus_hydro_fabric: gpd.GeoDataFrame
    _flowpath_hydro_fabric: gpd.GeoDataFrame
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
        # Register the default ngen output hook
        self._plugin_manager.register(TrouteOutput(self.routing_output))
        #Make a copy of the config file, just in case
        shutil.copy(self.realization, str(self.realization)+'_original')
       
        # Read the catchment hydrofabric data
        if self.hydrofabric is not None:
            if self._is_legacy_gpkg_hydrofabric(self.hydrofabric):
                self._read_legacy_gpkg_hydrofabric()
            else:
                self._read_gpkg_hydrofabric()
        else:
            self._read_legacy_geojson_hydrofabric()

        #Read the calibration specific info
        with open(self.realization) as fp:
            data = json.load(fp)
        self.ngen_realization = NgenRealization(**data)

    @staticmethod
    def _is_legacy_gpkg_hydrofabric(hydrofabric: Path) -> bool:
        """Return True if legacy (<=v2.1) gpkg hydrofabric."""
        import sqlite3
        connection = sqlite3.connect(hydrofabric)
        # hydrofabric <= 2.1 use 'flowpaths'
        # hydrofabric > 2.1 use 'flowlines'
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name='flowpaths';"
        try:
            cursor = connection.execute(query)
            value = cursor.fetchone()
        finally:
            connection.close()
        return value is not None

    def _read_gpkg_hydrofabric(self) -> None:
        # Read geopackage hydrofabric
        self._catchment_hydro_fabric = gpd.read_file(self.hydrofabric, layer='divides')
        self._catchment_hydro_fabric.set_index('divide_id', inplace=True)

        self._nexus_hydro_fabric = gpd.read_file(self.hydrofabric, layer='nexus')
        self._nexus_hydro_fabric.set_index('id', inplace=True)

        # hydrofabric > 2.1 use 'flowlines'
        self._flowpath_hydro_fabric = gpd.read_file(self.hydrofabric, layer='flowlines')
        self._flowpath_hydro_fabric.set_index('id', inplace=True)

        # hydrofabric > 2.1 use 'flowpath-attributes'
        attributes = gpd.read_file(self.hydrofabric, layer="flowpath-attributes")
        attributes.set_index("id", inplace=True)

        self._x_walk = pd.Series( attributes[ ~ attributes['rl_gages'].isna() ]['rl_gages'] )

    def _read_legacy_gpkg_hydrofabric(self) -> None:
        # Read geopackage hydrofabric
        self._catchment_hydro_fabric = gpd.read_file(self.hydrofabric, layer='divides')
        self._catchment_hydro_fabric.set_index('divide_id', inplace=True)

        self._nexus_hydro_fabric = gpd.read_file(self.hydrofabric, layer='nexus')
        self._nexus_hydro_fabric.set_index('id', inplace=True)

        # hydrofabric <= 2.1 use 'flowpaths'
        self._flowpath_hydro_fabric = gpd.read_file(self.hydrofabric, layer='flowpaths')
        self._flowpath_hydro_fabric.set_index('id', inplace=True)

        # hydrofabric <= 2.1 use 'flowpath_attributes'
        attributes = gpd.read_file(self.hydrofabric, layer="flowpath_attributes")
        attributes.set_index("id", inplace=True)

        self._x_walk = pd.Series( attributes[ ~ attributes['rl_gages'].isna() ]['rl_gages'] )

    def _read_legacy_geojson_hydrofabric(self) -> None:
        # Legacy geojson support
        assert self.catchments is not None, "missing geojson catchments file"
        assert self.nexus is not None, "missing geojson nexus file"
        assert self.crosswalk is not None, "missing crosswalk file"
        self._catchment_hydro_fabric = gpd.read_file(self.catchments)
        self._catchment_hydro_fabric = self._catchment_hydro_fabric.rename(columns=str.lower)
        self._catchment_hydro_fabric.set_index('id', inplace=True)
        self._nexus_hydro_fabric = gpd.read_file(self.nexus)
        self._nexus_hydro_fabric = self._nexus_hydro_fabric.rename(columns=str.lower)
        self._nexus_hydro_fabric.set_index('id', inplace=True)

        self._x_walk = pd.Series(dtype=object)
        with open(self.crosswalk) as fp:
            data = json.load(fp)
            for id, values in data.items():
                gage = values.get('Gage_no')
                if gage:
                    if not isinstance(gage, str):
                        gage = gage[0]
                    if gage != "":
                        self._x_walk[id] = gage

    @property
    def config_file(self) -> Path:
        """Path to the configuration file for this calibration

        Returns:
            Path: to ngen realization configuration file
        """
        return self.realization

    @property
    def adjustables(self) -> Sequence[CalibrationCatchment]:
        """A list of Catchments for calibration
        
        These catchments hold information about the parameters/calibration data for that catchment

        Returns:
            Sequence[CalibrationCatchment]: A list like container of CalibrationCatchment objects
        """
        return self._catchments

    @root_validator
    def set_defaults(cls, values: dict):
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
        hydrofabric = values.get('hydrofabric')

        custom_args = False
        if args is None:
            if hydrofabric is not None:
                args = f'{hydrofabric.resolve()} "all" {hydrofabric.resolve()} "all" {realization.name}'
            else:
                args = f'{catchments.resolve()} "all" {nexus.resolve()} "all" {realization.name}'
            values['args'] = args
        else:
            custom_args = True

        if parallel is not None and partitions is not None:
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
        if parallel is not None and parallel > 1 and partitions is None:
            raise ValueError("Must provide partitions if using parallel")
        return values

    @root_validator
    def _validate_model(cls, values: dict) -> dict:
        NgenBase._verify_hydrofabric(values)
        realization: Optional[NgenRealization] = values.get("ngen_realization")
        NgenBase._verify_ngen_realization(realization)
        return values

    @staticmethod
    def _verify_hydrofabric(values: dict) -> None:
        """
        Verify hydrofabric information is provided either as (deprecated) GeoJSON
        or (preferred) GeoPackage files.

        Args:
            values: root validator dictionary

        Raises:
            ValueError: If a geopackage hydrofabric or set of geojsons are not found

        Returns:
            None
        """
        hf: FilePath = values.get('hydrofabric')
        cats: FilePath = values.get("catchments")
        nex: FilePath = values.get("nexus")
        x: FilePath = values.get("crosswalk")

        if hf is None and cats is None and nex is None and x is None:
            msg = "Must provide a geopackage input with the hydrofabric key"\
                  "or proide catchment, nexus, and crosswalk geojson files."  
            raise ValueError(msg)
        
        if cats is not None or nex is not None or x is not None:
            warnings.warn("GeoJSON support will be deprecated in a future release, use geopackage hydrofabric.", DeprecationWarning)

    @staticmethod
    def _verify_ngen_realization(realization: Optional[NgenRealization]) -> None:
        """
        Verify `ngen_realization` uses supported features.

        Args:
            realization: maybe an `NgenRealization` instance

        Raises:
            UnsupportedFeatureError: If `realization.output_root` is not None.
                                     Feature not supported.

        Returns:
            None
        """
        if realization is None:
            return None

        if realization.output_root is not None:
            from .errors import UnsupportedFeatureError
            raise UnsupportedFeatureError(
                "ngen realization `output_root` field is not supported by ngen.cal. will be removed in future; see https://github.com/NOAA-OWP/ngen-cal/issues/150"
            )

    def update_config(self, i: int, params: pd.DataFrame, id: str = None, path=Path("./")):
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
        with open(path/self.realization.name, 'w') as fp:
                fp.write( self.ngen_realization.json(by_alias=True, exclude_none=True, indent=4))
        # Cleanup any t-route parquet files between runs
        # TODO this may not be _the_ best place to do this, but for now,
        # it works, so here it be...
        for file in Path(path).glob("*NEXOUT.parquet"):
            file.unlink()
    
class NgenExplicit(NgenBase):
    
    strategy: Literal[NgenStrategy.explicit] = NgenStrategy.explicit

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
                    raise(RuntimeError(f"Cannot establish mapping of catchment {id} to nwis location in cross walk"))
                try:
                    nexus_data = self._nexus_hydro_fabric.loc[fabric['toid']]
                except KeyError:
                    raise(RuntimeError(f"No suitable nexus found for catchment {id}"))

                #establish the hydro location for the observation nexus associated with this catchment
                location = NWISLocation(nwis, nexus_data.name, nexus_data.geometry)
                nexus = Nexus(nexus_data.name, location, (), Catchment(id, {}))
                output_var = catchment.formulations[0].params.main_output_variable
                #read params from the realization calibration definition
                params = {model:[Parameter(**p) for p in params] for model, params in catchment.calibration.items()}
                params = _map_params_to_realization(params, catchment)
                #TODO define these extra params in the realization config and parse them out explicity per catchment, cause why not?
                eval_params = self.eval_params.copy()
                eval_params.id = id
                self._catchments.append(CalibrationCatchment(self.workdir, id, nexus, start_t, end_t, fabric, output_var, eval_params, params))

    def update_config(self, i: int, params: pd.DataFrame, id: str, **kwargs):
        """_summary_

        Args:
            i (int): _description_
            params (pd.DataFrame): _description_
            id (str): _description_
        """

        if id is None:
            raise RuntimeError("NgenExplicit calibration must recieve an id to update, not None")
        
        super().update_config(i, params, id, **kwargs)

class NgenIndependent(NgenBase):
    # TODO Error if not routing block in ngen_realization
    strategy: Literal[NgenStrategy.independent] = NgenStrategy.independent
    params: Mapping[str, Parameters] #required in this case...

    def __init__(self, **kwargs):
        #Let pydantic work its magic
        super().__init__(**kwargs)
        # FIXME cannot strip all global params cause things like sloth depend on them
        # but the global params may have defaults in place that are not the same as the requested
        # calibration params.  This shouldn't be an issue since each catchment overrides the global config
        # and it won't actually be used, but the global config definition may not be correct.
        #self._strip_global_params()
        #now we work ours
        start_t = self.ngen_realization.time.start_time
        end_t = self.ngen_realization.time.end_time
        #Setup each calibration catchment
        catchments = []
        eval_nexus = []
        catchment_realizations = {}
        g_conf = self.ngen_realization.global_config.copy(deep=True).dict(by_alias=True)
        for id in self._catchment_hydro_fabric.index:
            #Copy the global configuration into each catchment
            catchment_realizations[id] = CatchmentRealization(**g_conf)
            #Need to fix the forcing definition or ngen will not work
            #for individual catchment configs, it doesn't apply pattern resolution
            #and will read the directory `path` key as the file key and will segfault
            path = catchment_realizations[id].forcing.path
            pattern = catchment_realizations[id].forcing.file_pattern
            catchment_realizations[id].forcing.file_pattern = None
            # case when we have a pattern
            if pattern is not None:
                pattern = pattern.replace("{{id}}", id)
                pattern = re.compile(pattern.replace("{{ID}}", id))
                for f in path.iterdir():
                    if pattern.match(f.name):
                        catchment_realizations[id].forcing.path = f.resolve()
            

        self.ngen_realization.catchments = catchment_realizations
        
        for id, catchment in self.ngen_realization.catchments.items():#data['catchments'].items():
            try:
                fabric = self._catchment_hydro_fabric.loc[id]
            except KeyError: # This probaly isn't strictly required since we built these from the index
                continue
            try:
                nexus_data = self._nexus_hydro_fabric.loc[fabric['toid']]
            except KeyError:
                raise(RuntimeError(f"No suitable nexus found for catchment {id}"))
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
                nexus = Nexus(nexus_data.name, location, (), Catchment(id, {}))
                eval_nexus.append( nexus ) # FIXME why did I make this a tuple???
            else:
                #in this case, we don't care if all nexus are observable, just need one downstream
                #FIXME use the graph to work backwards from an observable nexus to all upstream catchments
                #and create independent "sets"
                nexus = Nexus(nexus_data.name, None, (), Catchment(id, {}))
            #FIXME pick up params per catchmment somehow???
            params = _map_params_to_realization(self.params, catchment)
            catchments.append(AdjustableCatchment(self.workdir, id, nexus, params))
        
        if self.eval_feature:
            for n in eval_nexus:
                wb = self._flowpath_hydro_fabric[ self._flowpath_hydro_fabric['toid'] == n.id ]
                key = wb.iloc[0].name
                if key == self.eval_feature:
                    eval_nexus = [n]
                    break

        if len(eval_nexus) != 1:
            raise RuntimeError( "Currently only a single nexus in the hydrfabric can be gaged, set the eval_feature key to pick one.")     
        self._catchments.append(CalibrationSet(catchments, eval_nexus[0], self._plugin_manager.hook, start_t, end_t, self.eval_params))

    def _strip_global_params(self) -> None:
        module = self.ngen_realization.global_config.formulations[0].params
        if isinstance(module, MultiBMI):
            for m in module.modules:
                m.params.model_params = None
        else:
            module.model_params = None
            

class NgenUniform(NgenBase):
    """
        Uses a global ngen configuration and permutes just this global parameter space
        which is applied to each catchment in the hydrofabric being simulated.
    """
    # TODO Error if not routing block in ngen_realization
    strategy: Literal[NgenStrategy.uniform] = NgenStrategy.uniform
    params: Mapping[str, Parameters] #required in this case...

    def __init__(self, **kwargs):
        #Let pydantic work its magic
        super().__init__(**kwargs)
        #now we work ours
        start_t = self.ngen_realization.time.start_time
        end_t = self.ngen_realization.time.end_time
        eval_nexus = []
        
        for id, toid in self._catchment_hydro_fabric['toid'].items():
            assert isinstance(id, str), f"id expected to be str subtype. is type: {type(id)}"
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
            nexus = Nexus(nexus_data.name, location, (), Catchment(id, {}))
            eval_nexus.append( nexus )
        
        if self.eval_feature:
            for n in eval_nexus:
                wb = self._flowpath_hydro_fabric[ self._flowpath_hydro_fabric['toid'] == n.id ]
                key = wb.iloc[0].name
                if key == self.eval_feature:
                    eval_nexus = [n]
                    break

        if len(eval_nexus) != 1:
            raise RuntimeError( "Currently only a single nexus in the hydrfabric can be gaged, set the eval_feature key to pick one.")
        params = _params_as_df(self.params)
        self._catchments.append(UniformCalibrationSet(eval_nexus=eval_nexus[0], hooks=self._plugin_manager.hook, start_time=start_t, end_time=end_t, eval_params=self.eval_params, params=params))
            
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
    def adjustables(self):
        return self.__root__._catchments

    @property
    def strategy(self):
        return self.__root__.strategy
    
    def restart(self) -> int:
        starts = []
        for catchment in self.adjustables:
            starts.append(catchment.restart())
        if starts and all( x == starts[0] for x in starts):
            #if everyone agress on the iteration...
            return starts[0]
        else:
            #starts is empty or someone disagress on the starting iteration...
            return 0

    @property
    def type(self):
        return self.__root__.type

    def resolve_paths(self, relative_to: Path | None=None):
        """resolve any possible relative paths in the realization
        """
        if self.__root__.ngen_realization != None:
            self.__root__.ngen_realization.resolve_paths(relative_to)

    @property
    def best_params(self):
        return self.__root__.eval_params.best_params
