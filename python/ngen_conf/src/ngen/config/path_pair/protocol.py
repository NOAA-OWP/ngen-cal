import sys

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from pathlib import Path

from .typing import T, S


class Writer(Protocol):
    def __call__(self, p: Path, data: bytes) -> None:
        ...


class Reader(Protocol):
    def __call__(self, p: Path) -> bytes:
        ...


class Deserializer(Protocol[T]):
    def __call__(self, data: bytes) -> T:
        ...


class Serializer(Protocol[S]):
    def __call__(self, o: S) -> bytes:
        ...
