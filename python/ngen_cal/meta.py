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
    def best_params(self) -> int:
        """
            The integer iteration that contains the best parameter values
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

        """
        return self._workdir+self._log_file

    def write_objective_log_file(self, i, score):
        with open(os.path.join(self._workdir, 'objective.log'), 'a') as log_file:
            log_file.write('{}, '.format(i))
            log_file.write('{}\n'.format(score))

    def write_param_log_file(self, i, best, score):
        with open(os.path.join(self._workdir, 'best_params.log'), 'w') as log_file:
            log_file.write('{}\n'.format(i))
            log_file.write('{}\n'.format(best))
            log_file.write('{}\n'.format(score))

    def read_param_log_file(self):
        with open(os.path.join(self._workdir, 'best_params.log'), 'r') as log_file:
            iteration = int(log_file.readline())
            best_params = int(log_file.readline())
            best_score = float(log_file.readline())
        return iteration, best_params, best_score
