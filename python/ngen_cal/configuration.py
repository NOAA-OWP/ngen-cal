import json
from pathlib import Path
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from ngen_cal.calibration_cathment import CalibrationCatchment

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S")

class Configuration():
    """

    """

    def __init__(self, config_file: 'Path', calibration_input: 'Path'):
        """

        """
        self.data = None
        self._catchments = []
        with open(config_file) as fp:
            self.data = json.load(fp)
        #Read the calibration specific info
        #with open(calibration_input) as fp:
        #    data = json.load(fp)
        #    for id, params in data.items():
        #        catchment = CalibrationCatchment(id, self.data['catchments'][id])

        for id, params in self.data['catchments'].items():
            logging.debug(id)
            logging.debug(params)
            if 'calibration' in params.keys():
                self._catchments.append(CalibrationCatchment(id, self.data['catchments']))


    @property
    def catchments(self) -> Iterable['Catchment']:
        """FIXME
            A list of Catchments for calibration
            currently just a list of str ids, but ultimately should be encapsulated catchments holding
            information about the parameters/calibration data for that catchment
        """
        return self._catchments
