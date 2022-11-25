import json
import pandas as pd # type: ignore
from pathlib import Path
from typing import TYPE_CHECKING
from .configuration import General, Model

if TYPE_CHECKING:
    from pathlib import Path
    from pandas import DataFrame


class CalibrationMeta:
    """
        Structure for holding calibration meta data

        ###TODO can we hold enough `configuration` information to make it possible to update global config
    """

    def __init__(self, model: Model, general: General):
        """

        """
        self._workdir = general.workdir
        self._log_file = general.log_file
        self._general = general
        if(self._log_file is not None):
            self._log_file = self._workdir/self._log_file
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

    def read_param_log_file(self):
        with open(self._param_log_file, 'r') as log_file:
            iteration = int(log_file.readline())
            best_params = int(log_file.readline())
            best_score = float(log_file.readline())
        return iteration, best_params, best_score

    def restart(self) -> int:
        """
            Attempt to restart a calibration from a previous state.
            If no previous state is available, start from 0

            Returns
            -------
            int iteration to start calibration at
        """
        #TODO how much meta info is catchment specific vs global?  Might want to wrap this up per catchment?
        try:
            last_iteration, best_params, best_score = self.read_param_log_file()
            self._best_params_iteration = str(best_params)
            self._best_score = best_score
            start_iteration = last_iteration + 1

            for catchment in self._model.hy_catchments:
                catchment.load_df(self._workdir)
            #TODO verify that loaded calibration info aligns with iteration?  Anther reason to consider making this meta
            #per catchment???

        except FileNotFoundError:
            start_iteration = 0

        return start_iteration
