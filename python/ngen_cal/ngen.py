from pydantic import FilePath, root_validator
from typing import Optional, Literal, Sequence, Dict
from pathlib import Path
import logging
#supress geopandas debug logs
logging.disable(logging.DEBUG)
import json
json.encoder.FLOAT_REPR = str #lambda x: format(x, '%.09f')
import geopandas as gpd
import pandas as pd
import shutil
from .model import ModelExec, PosInt
from .calibration_cathment import CalibrationCatchment
#HyFeatures components
from hypy.hydrolocation import NWISLocation # type: ignore
from hypy.nexus import Nexus # type: ignore

class Ngen(ModelExec):
    """
        Data class specific for Ngen
        
        Inherits the ModelParams attributes and Configurable interface
    """
    type: Literal['ngen']
    #required fields
    realization: FilePath
    catchments: FilePath
    nexus: FilePath
    crosswalk: FilePath
    #optional fields
    partitions: Optional[FilePath]
    parallel: Optional[PosInt]
    #dependent fields
    binary: str = 'ngen'
    args: Optional[str]

    #private, not validated
    _catchments: Sequence['CalibrationCatchment'] = []

    class Config:
        """Override configuration for pydantic BaseModel
        """
        underscore_attrs_are_private = True

    def __init__(self, **kwargs):
        #Let pydantic work its magic
        super().__init__(**kwargs)
        #now we work ours
        #Make a copy of the config file, just in case
        shutil.copy(self.realization, str(self.realization)+'_original')

        #Read the catchment hydrofabric data
        catchment_hydro_fabric = gpd.read_file(self.catchments)
        catchment_hydro_fabric = catchment_hydro_fabric.rename(columns=str.lower)
        catchment_hydro_fabric.set_index('id', inplace=True)
        nexus_hydro_fabric = gpd.read_file(self.nexus)
        nexus_hydro_fabric = nexus_hydro_fabric.rename(columns=str.lower)
        nexus_hydro_fabric.set_index('id', inplace=True)

        x_walk = pd.read_json(self.crosswalk, dtype=str)

        #Read the calibration specific info
        with open(self.realization) as fp:
            data = json.load(fp)
        try:
            #FIXME validate sim time with eval time in general config
            start_t = data['time']['start_time']
            end_t = data['time']['end_time']
        except KeyError as e:
            raise(RuntimeError("Invalid time configuration: {} key missing from {}".format(e.args[0], self.realization)))
        #Setup each calibration catchment
        for id, catchment in data['catchments'].items():
            if 'calibration' in catchment.keys():
                try:
                    fabric = catchment_hydro_fabric.loc[id]
                except KeyError:
                    continue
                try:
                    nwis = x_walk[id]['site_no']
                except KeyError:
                    raise(RuntimeError("Cannot establish mapping of catchment {} to nwis location in cross walk".format(id)))
                try:
                    nexus_data = nexus_hydro_fabric.loc[fabric['toid']]
                except KeyError:
                    raise(RuntimeError("No suitable nexus found for catchment {}".format(id)))

                #establish the hydro location for the observation nexus associated with this catchment
                location = NWISLocation(nwis, nexus_data.name, nexus_data.geometry)
                nexus = Nexus(nexus_data.name, location, id)
                self._catchments.append(CalibrationCatchment(self.workdir, id, nexus, start_t, end_t, fabric, catchment))
        print(self._catchments)

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