import logging
#supress geopandas debug logs
logging.disable(logging.DEBUG)
import json
json.encoder.FLOAT_REPR = str #lambda x: format(x, '%.09f')
import geopandas as gpd
import pandas as pd
import shutil
from pathlib import Path
from typing import Sequence, TYPE_CHECKING
from hypy.hydrolocation import NWISLocation # type: ignore
from hypy.nexus import Nexus # type: ignore

if TYPE_CHECKING:
    from pathlib import Path

from .calibration_cathment import CalibrationCatchment

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S")


class Configuration:
    """

    """

    def __init__(self, config_file: 'Path', catchment_data: 'Path', nexus_data: 'Path', cross_walk: 'Path', workdir: 'Path'):
        """

        """
        self._catchments = []
        self._config_file_path = config_file
        #Make a copy of the config file, just in case
        shutil.copy(config_file, str(config_file)+'_original')

        #Read the catchment hydrofabric data
        catchment_hydro_fabric = gpd.read_file(catchment_data)
        catchment_hydro_fabric = catchment_hydro_fabric.rename(columns=str.lower)
        catchment_hydro_fabric.set_index('id', inplace=True)
        nexus_hydro_fabric = gpd.read_file(nexus_data)
        nexus_hydro_fabric = nexus_hydro_fabric.rename(columns=str.lower)
        nexus_hydro_fabric.set_index('id', inplace=True)

        x_walk = pd.read_json(cross_walk, dtype=str)

        #Read the calibration specific info
        with open(config_file) as fp:
            data = json.load(fp)
        try:
            start_t = data['time']['start_time']
            end_t = data['time']['end_time']
        except KeyError as e:
            raise(RuntimeError("Invalid time configuration: {} key missing from {}".format(e.args[0], config_file)))
        #Setup each calibration catchment
        for id, catchment in data['catchments'].items():
            if 'calibration' in catchment.keys():
                try:
                    fabric = catchment_hydro_fabric.loc[id]
                except KeyError:
                    #TODO log WARNING:
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
                self._catchments.append(CalibrationCatchment(workdir, id, nexus, start_t, end_t, fabric, catchment))

    @property
    def config_file(self) -> Path:
        """
            Path to the configuration file for this calibration
        """
        return self._config_file_path

    @property
    def catchments(self) -> Sequence['CalibrationCatchment']:
        """
            A list of Catchments for calibration holding information about the
            parameters/calibration data for that catchment
        """
        return self._catchments
