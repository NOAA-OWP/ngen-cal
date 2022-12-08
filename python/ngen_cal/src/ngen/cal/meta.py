import json
import pandas as pd # type: ignore
from pathlib import Path
from tempfile import mkdtemp
from typing import TYPE_CHECKING
from .configuration import General, Model

if TYPE_CHECKING:
    from pathlib import Path
    from pandas import DataFrame

class JobMeta:
    """
        Structure for holding model job meta data
    """

    def __init__(self, name: str, parent_workdir: Path, workdir: Path=None, log=False):
        """Create a job meta data structure

        Args:
            name (str): name of the job, is used to construct log files
            workdir (Path): working directory to stage the job under
            log (bool, optional): Whether or not to create a log file for the job. Defaults to False.
        """
        if(workdir is None):
            self._workdir = Path( mkdtemp(dir=parent_workdir, prefix=name+"_", suffix="_worker") ).resolve()
        else:
            self._workdir = workdir

        self._log_file = None
        if(log):
            self._log_file = self._workdir/Path(name+".log")

    @property
    def workdir(self) -> 'Path':
        return self._workdir
    
    @workdir.setter
    def workdir(self, path: 'Path') -> None:
        self._workdir = path
        if(self._log_file is not None):
            self._log_file = self._workdir/Path(self._log_file.name)

    @property
    def log_file(self) -> 'Path':
        """
            Path to the job's log file, or None.
        """
        return self._log_file
