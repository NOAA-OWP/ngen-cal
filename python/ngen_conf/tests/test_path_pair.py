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
        assert o.write() == True
        assert p.read_bytes() == o.serialize()
        assert p.is_file()
        assert p.exists()


def test_path_read(path_pair: PosixPathPair[InnerModel]):
    with tempfile.NamedTemporaryFile() as f:
        p = Path(f.name)
        o = path_pair.with_path(p)
        assert o.write() == True
        o2 = PathPair(o, deserializer=path_pair._deserializer)
        assert p.is_file()
        assert p.exists()
        assert o2.read() == True
        assert o2.inner == o.inner == path_pair.inner


@pytest.fixture
def collection() -> PosixPathPairCollection[InnerModel]:
    """Does not try to clean up and created assets."""
    p = Path("id_{id}_data.txt")
    pattern = "{id}"
    models = [InnerModel(foo=i) for i in range(12)]
    ids = list(map(lambda s: str(s), range(12)))

    return PathPairCollection.from_objects(
        models,
        pattern=pattern,
        path=p,
        ids=ids,
        serializer=pydantic_serializer,
        deserializer=pydantic_deserializer(InnerModel),
    )


@pytest.fixture
def temp_collection(
    collection: PosixPathPairCollection[InnerModel],
) -> PosixPathPairCollection[InnerModel]:
    """
    `PathPairCollection` backed by a temp directory. This guarantees that files / dirs created in the
    temp dir will be cleaned up once the test using this fixture has run.

    Only use this if you need to test writing / reading.
    """
    with tempfile.TemporaryDirectory() as dir:
        o = Path(dir) / collection
        yield o
        o.unlink(missing_ok=True)


def test_path_pair_collection_write(
    temp_collection: PosixPathPairCollection[InnerModel],
):
    prefix, _, suffix = temp_collection.name.partition(temp_collection.pattern)
    glob_term = f"{prefix}*{suffix}"

    # assert no files have been written
    assert len(list(temp_collection.parent.glob(glob_term))) == 0

    assert temp_collection.write() == True

    # assert all files have been written
    assert len(list(temp_collection.parent.glob(glob_term))) == len(
        list(temp_collection.inner)
    )


def test_path_pair_collection_read(
    temp_collection: PosixPathPairCollection[InnerModel],
):
    prefix, _, suffix = temp_collection.name.partition(temp_collection.pattern)
    glob_term = f"{prefix}*{suffix}"

    assert len(list(temp_collection.parent.glob(glob_term))) == 0

    assert temp_collection.write() == True

    c2 = PathPairCollection(
        temp_collection,
        pattern=temp_collection.pattern,
        deserializer=temp_collection._deserializer,
    )

    assert c2.read() == True

    # sort inner list[ObjectPosixPathPair] b.c. _get_filenames uses `glob` which is not ordered
    temp_collection._inner.sort()
    c2._inner.sort()

    # this compares Path values, not inner
    assert temp_collection._inner == c2._inner

    for col_item, c2_item in zip(temp_collection._inner, c2._inner):
        assert col_item.inner == c2_item.inner


def test_path_pair_collection_truediv_is_noop(
    collection: PosixPathPairCollection[InnerModel],
):
    o = collection / "test"
    assert o == collection
    assert type(o) == type(collection)


def test_path_pair_collection_with_path_is_noop(
    collection: PosixPathPairCollection[InnerModel],
):
    o = collection.with_path("test")
    assert o == collection
    assert type(o) == type(collection)


def test_path_pair_collection_rtruediv(
    collection: PosixPathPairCollection[InnerModel],
):
    new_root = Path("new/root")
    o = new_root / collection

    assert o == new_root / collection.name
    assert type(o) == type(collection)
    for prev_pair, new_pair in zip(collection.inner_pair, o.inner_pair):
        assert prev_pair.name == new_pair.name
        assert new_pair.parent == new_root


def test_path_pair_serialize(collection: PosixPathPairCollection[InnerModel]):
    serial = [item.serialize() for item in collection.inner_pair]
    assert list(collection.serialize()) == serial


def test_path_pair_deserialize(collection: PosixPathPairCollection[InnerModel]):
    empty_collection = PosixPathPairCollection(
        Path(collection),
        pattern=collection.pattern,
        deserializer=collection._deserializer,
    )
    assert empty_collection.deserialize(collection.serialize()) == True
    for item in empty_collection.inner_pair:
        # assert item's path == collection's path
        assert item == collection


def test_path_pair_deserialize_provide_path(
    collection: PosixPathPairCollection[InnerModel],
):
    empty_collection = PosixPathPairCollection(
        Path(collection),
        pattern=collection.pattern,
        deserializer=collection._deserializer,
    )
    collection_paths = (Path(item) for item in collection.inner_pair)
    assert (
        empty_collection.deserialize(collection.serialize(), paths=collection_paths)
        == True
    )
    assert list(empty_collection.inner_pair) == list(collection.inner_pair)


def test_path_pair_deserialize_raises_when_iterators_have_different_stopping_points(
    collection: PosixPathPairCollection[InnerModel],
):
    empty_collection = PosixPathPairCollection(
        Path(collection),
        pattern=collection.pattern,
        deserializer=collection._deserializer,
    )
    collection_paths = (Path(item) for item in [])
    with pytest.raises(ValueError):
        empty_collection.deserialize(collection.serialize(), paths=collection_paths)


def test_path_pair_unlink(
    temp_collection: PosixPathPairCollection[InnerModel],
):
    for path in temp_collection._get_filenames():
        assert not path.exists()

    assert temp_collection.write() == True

    for path in temp_collection._get_filenames():
        assert path.exists()

    temp_collection.unlink()

    for path in temp_collection._get_filenames():
        assert not path.exists()
