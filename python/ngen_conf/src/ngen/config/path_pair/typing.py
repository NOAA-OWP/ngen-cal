from pathlib import Path
from typing import Union, TypeVar
from typing_extensions import TypeAlias

T = TypeVar("T", bound=object, covariant=True)
"""Some type T or a subtype of T"""
S = TypeVar("S", bound=object, contravariant=True)
"""Some type S or a _supertype_ of S"""

StrPath: TypeAlias = Union[Path, str]
