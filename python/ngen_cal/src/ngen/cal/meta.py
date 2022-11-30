import json
import pandas as pd # type: ignore
from pathlib import Path
from typing import TYPE_CHECKING
from .configuration import General, Model

if TYPE_CHECKING:
    from pathlib import Path
    from pandas import DataFrame

class JobMeta:
    """
        Structure for holding calibration meta data

        ###TODO can we hold enough `configuration` information to make it possible to update global config
    """

    def __init__(self, model: Model, general: General):
        """

        """
        self._workdir = general.workdir #FIXME workdir...?????
        self._log_file = general.log_file #FIXME move log file to job specific log, not general
        #self._general = general
        if(self._log_file is not None):
            self._log_file = self._workdir/self._log_file
            #FIXME make all log file names generated, but allow path differentiation?
        self._model = model #This is the Model Configuration object that knows how to operate on model configuration files
        self._bin = model.get_binary()
        self._args = model.get_args()

    def update_config(self, i: int, params: 'DataFrame', id: str):
        """
            For a given calibration iteration, i, update the input files/configuration to prepare for that iterations
            calibration run.

            parameters
            ---------
            i: int
                current iteration of calibration
            params: pandas.DataFrame
                DataFrame containing the parameter name in `param` and value in `i` columns
        """
        return self._model.update_config(i, params, id)

    @property
    def workdir(self) -> 'Path':
        return self._workdir

    @property
    def cmd(self) -> str:
        """

        """
        return "{} {}".format(self._bin, self._args)

    @property
    def log_file(self) -> 'Path':
        """

        """
        return self._log_file

    @log_file.setter
    def log_file(self, path: 'Path') -> None:
        self._log_file = path
