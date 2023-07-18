from pydantic import BaseModel
from pathlib import Path

from .protocol import Deserializer

from typing import Type, TypeVar

M = TypeVar("M", bound=BaseModel)


def path_reader(p: Path) -> bytes:
    return p.read_bytes()


def path_writer(p: Path, data: bytes) -> None:
    p.write_bytes(data)


def pydantic_serializer(o: BaseModel) -> bytes:
    return o.json(by_alias=True).encode()


def pydantic_deserializer(m: Type[M]) -> Deserializer[M]:
    def deserialize(data: bytes) -> M:
        return m.parse_raw(data)

    return deserialize
