import sys

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from pathlib import Path

from .typing import T, S


class Writer(Protocol):
    """
    Function that writes data to a path or elsewhere (e.g. network).
    """
    def __call__(self, p: Path, data: bytes) -> None:
        ...


class Reader(Protocol):
    """
    Function that reads data from a file path or elsewhere (e.g. network).
    """
    def __call__(self, p: Path) -> bytes:
        ...


class Deserializer(Protocol[T]):
    """
    Function that given bytes returns a T.
    """
    def __call__(self, data: bytes) -> T:
        ...


class Serializer(Protocol[S]):
    """
    Function that given a T returns bytes.
    """
    def __call__(self, o: S) -> bytes:
        ...
