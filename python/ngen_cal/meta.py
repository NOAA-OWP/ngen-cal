class CalibraitonMeta(object):
    """
        Structure for holding calibration meta data

        ###TODO can we hold enough `configuration` information to make it possible to update global config
    """

    def __init__(self, workdir, bin, cmd, cmd_args):
        """

        """
        self._workdir = workdir
        self._best_score = -1
        self._best_param_iteration = 1
        self._bin = bin
        self._args = cmd
        self._cmd = cmd_args
        self._log_file = "{}_log_file".format(bin)

    @property
    def cmd(self) -> str:
        """

        """
        return "{} {}".format(self._bin, self._args)

    @property
    def log_file(self) -> Path:
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
