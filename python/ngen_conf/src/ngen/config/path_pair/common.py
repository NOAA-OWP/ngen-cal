from __future__ import annotations

from pydantic import BaseModel

from .protocol import Deserializer

from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

M = TypeVar("M", bound=BaseModel)


def path_reader(p: Path) -> bytes:
    return p.read_bytes()


def path_writer(p: Path, data: bytes) -> None:
    p.write_bytes(data)


def pydantic_serializer(o: BaseModel) -> bytes:
    return o.json(by_alias=True).encode()


def pydantic_deserializer(m: type[M]) -> Deserializer[M]:
    def deserialize(data: bytes) -> M:
        return m.parse_raw(data)

    return deserialize
