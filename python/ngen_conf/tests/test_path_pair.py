import inspect
import pytest
import tempfile
from pydantic import BaseModel
from pathlib import Path

from ngen.config.path_pair import (
    PathPair,
    PosixPathPair,
    PathPairCollection,
    PosixPathPairCollection,
)
from ngen.config.path_pair.common import pydantic_deserializer, pydantic_serializer


class InnerModel(BaseModel):
    foo: int


class Model(BaseModel):
    p: Path


@pytest.fixture
def path_pair() -> PosixPathPair[InnerModel]:
    m = InnerModel(foo=12)
    return PathPair(
        "",
        inner=m,
        serializer=pydantic_serializer,
        deserializer=pydantic_deserializer(InnerModel),
    )


def test_path_pair_from_object():
    m = InnerModel(foo=12)
    o = PathPair.from_object(m, serializer=pydantic_serializer)
    assert o == Path("")
    assert o.inner == m


def test_path_pair_with_path(path_pair: PosixPathPair[InnerModel]):
    assert path_pair != Path("/")

    o2 = path_pair.with_path("/")
    assert o2 == Path("/")
    assert o2.inner == path_pair.inner


def test_path_truediv(path_pair: PosixPathPair[InnerModel]):
    assert path_pair != Path("test")

    o = path_pair / "test"

    assert o == Path("test")
    assert o.inner == path_pair.inner

    o /= "test"
    assert o == Path("test/test")
    assert o.inner == path_pair.inner


def test_path_rtruediv(path_pair: PosixPathPair[InnerModel]):
    o = "test/test" / path_pair
    assert o == Path("test/test")
    assert o.inner == path_pair.inner


def test_path_serialize(path_pair: PosixPathPair[InnerModel]):
    assert path_pair.serialize() == path_pair.inner.json().encode()


def test_path_deserialize(path_pair: PosixPathPair[InnerModel]):
    data = path_pair.serialize()
    o = PosixPathPair(path_pair, deserializer=path_pair._deserializer)
    assert o.deserialize(data) == True
    assert o.inner == path_pair.inner


def test_path_write(path_pair: PosixPathPair[InnerModel]):
    with tempfile.NamedTemporaryFile() as f:
        p = Path(f.name)
        o = path_pair.with_path(p)
        o.write()
        assert p.read_bytes() == o.serialize()
        assert p.is_file()
        assert p.exists()


def test_path_read(path_pair: PosixPathPair[InnerModel]):
    with tempfile.NamedTemporaryFile() as f:
        p = Path(f.name)
        o = path_pair.with_path(p)
        o.write()
        o2 = PathPair(o, deserializer=path_pair._deserializer)
        assert p.is_file()
        assert p.exists()
        assert o2.read() == True
        assert o2.inner == o.inner == path_pair.inner
