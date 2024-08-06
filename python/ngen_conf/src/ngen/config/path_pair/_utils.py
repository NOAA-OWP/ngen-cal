from __future__ import annotations

import sys
from pathlib import Path


def path_unlink_37(p: Path, missing_ok: bool):
    # see: https://docs.python.org/3.8/library/pathlib.html#pathlib.Path.unlink
    # > _Changed_ in version 3.8: The _missing_ok_ parameter was added.
    # TODO: remove once we drop 3.7 support
    if sys.version_info >= (3, 8):
        p.unlink(missing_ok=missing_ok)
        return
    if missing_ok and not p.exists():
        return
    p.unlink()
