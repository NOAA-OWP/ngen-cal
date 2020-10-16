import json
import shutil
from pathlib import Path
from typing import Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from .calibration_cathment import Catchment, CalibrationCatchment

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S")


class Configuration:
    """

    """

    def __init__(self, config_file: 'Path'):
        """

        """
        self._catchments = []
        self._config_file_path = config_file
        #Make a copy of the config file, just in case
        shutil.copy(config_file, str(config_file)+'_original')
        with open(config_file) as fp:
            data = json.load(fp)
        #Read the calibration specific info

        for id, catchment in data['catchments'].items():
            if 'calibration' in catchment.keys():
                self._catchments.append(CalibrationCatchment(id, catchment))

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
