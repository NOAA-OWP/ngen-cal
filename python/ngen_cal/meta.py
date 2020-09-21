from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

class CalibrationMeta(object):
    """
        Structure for holding calibration meta data

        ###TODO can we hold enough `configuration` information to make it possible to update global config
    """

    def __init__(self, config, workdir, bin, args, id):
        """

        """
        self._config = config #This is the Configuration object that knows how to operate on model configuration files
        self._workdir = workdir
        self._best_score = -1
        self._best_param_iteration = '0' #String representation of interger iteration
        self._bin = bin
        self._args = args
        self._log_file = self._workdir/"{}_log_file".format(bin)
        self._id = id #a unique identifier to prepend to log files

        self._param_log_file = self._workdir/"{}_best_params.log".format(self._id)
        self._objective_log_file = self._workdir/"{}_objective.log".format(self._id)

    def update_config(self, i):
        """
            For a given calibration iteration, i, update the input files/configuration to prepare for that iterations
            calibration run.
        """
        pass

    @property
    def workdir(self) -> 'Path':
        return self._workdir

    @property
    def best_score(self) -> float:
        """
            Best score known to the current calibration
        """
        return self._best_score

    @property
    def best_params(self) -> str:
        """
            The integer iteration that contains the best parameter values, as a string
        """
        return self._best_param_iteration

    @property
    def cmd(self) -> str:
        """

        """
        return "{} {}".format(self._bin, self._args)

    @property
    def log_file(self) -> 'Path':
        """

        """
        return self._workdir/self._log_file

    def update(self, i: int, score: int, log: bool):
        """
            Update the meta state for iteration `i` having score `score`
            logs parameter and objective information if log=True
        """
        if score <= self.best_score:
            self.best_params = i
            self.best_score = score

        if log:
            self.write_param_log_file(i)
            self.write_objective_log_file(i, score)

    def write_objective_log_file(self, i, score):
        with open(self._objective_log_file, 'a') as log_file:
            log_file.write('{}, '.format(i))
            log_file.write('{}\n'.format(score))

    def write_param_log_file(self, i):
        with open(self._param_log_file, 'w') as log_file:
            log_file.write('{}\n'.format(i))
            log_file.write('{}\n'.format(self.best_params))
            log_file.write('{}\n'.format(self.best_score))

    def read_param_log_file(self):
        with open(self._param_log_file, 'r') as log_file:
            iteration = int(log_file.readline())
            best_params = int(log_file.readline())
            best_score = float(log_file.readline())
        return iteration, best_params, best_score
