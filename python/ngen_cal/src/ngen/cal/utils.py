from contextlib import contextmanager
from os import getcwd, chdir
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path

@contextmanager
def pushd(path: 'Path') -> None:
    """Change working directory to `path` for duration of the context

    Args:
        path (Path): path to cd to
    """
    #save current working dir
    cwd = getcwd()
    #change to new path
    chdir(path)
    try:
        yield #yield context
    finally:
        #when finished, return to original working dir
        chdir(cwd)