from pathlib import Path

from typing import Protocol
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
