from pathlib import Path
from typing import Union, TypeVar
from typing_extensions import TypeAlias

T = TypeVar("T", bound=object, covariant=True)
S = TypeVar("S", bound=object, contravariant=True)

StrPath: TypeAlias = Union[Path, str]
