from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

class JobMeta:
    """
        Structure for holding model job meta data
    """

    def __init__(self, name: str, parent_workdir: Path, workdir: Path=None, log=False):
        """Create a job meta data structure

        Args:
            name (str): name of the job, is used to construct log files
            workdir (Path): working directory to stage the job under.  If workdir is None, a temporary directory following the pattern
                            YYYYMMDDHHmm_name_worker is created.  Once created, it is left to the user to cleanup if needed.
            log (bool, optional): Whether or not to create a log file for the job. Defaults to False.
        """
        if workdir is None:
            self._workdir = Path( mkdtemp(dir=parent_workdir, prefix=f"{datetime.now().strftime('%Y%m%d%H%M')}_{name}_", suffix="_worker") ).resolve()
        else:
            self._workdir = workdir

        self._log_file = None
        if log:
            self._log_file = self._workdir/Path(name+".log")

    @property
    def workdir(self) -> Path:
        return self._workdir

    @workdir.setter
    def workdir(self, path: Path) -> None:
        self._workdir = path
        if self._log_file is not None:
            self._log_file = self._workdir/Path(self._log_file.name)

    @property
    def log_file(self) -> Path:
        """
            Path to the job's log file, or None.
        """
        return self._log_file
