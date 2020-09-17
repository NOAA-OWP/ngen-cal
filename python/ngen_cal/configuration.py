import json
from pathlib import Path
from typing import Iterable

from hypy.catchment import Catchment

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S")

class Configuration():
    """

    """

    def __init__(self, config_file: Path):
        """

        """
        self.data = None
        self._catchments = []
        with open(config_file) as fp:
            self.data = json.load(fp)
        for id, params in self.data['catchments'].items():
            logging.debug(id)
            logging.debug(params)
            self._catchments.append(Catchment(id, params))


    @property
    def catchments(self) -> Iterable['Catchment']:
        """FIXME
            A list of Catchments for calibration
            currently just a list of str ids, but ultimately should be encapsulated catchments holding
            information about the parameters/calibration data for that catchment
        """
        return self._catchments
