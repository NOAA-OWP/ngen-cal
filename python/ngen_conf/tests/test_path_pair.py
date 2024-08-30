from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Union, Protocol, TYPE_CHECKING

import pytest
from pydantic import BaseModel, ValidationError, validator

from ngen.config.path_pair.path_pair import path_pair
from ngen.config.path_pair import (
    PathPair,
    PathPairCollection,
    PosixPathPair,
    PosixPathPairCollection,
)
from ngen.config.path_pair.common import pydantic_deserializer, pydantic_serializer


class InnerModel(BaseModel):
    foo: int


class Model(BaseModel):
    p: Path


@pytest.fixture
def path_pair_model() -> PosixPathPair[InnerModel]:
    m = InnerModel(foo=12)
    return PathPair(
        "",
        inner=m,
        serializer=pydantic_serializer,
        deserializer=pydantic_deserializer(InnerModel),
    )


def test_path_pair_from_object():
    m = InnerModel(foo=12)
    o = PathPair.with_object(m, serializer=pydantic_serializer)
    assert o == Path("")
    assert o.inner == m


def test_path_pair_with_path(path_pair_model: PosixPathPair[InnerModel]):
    assert path_pair_model != Path("/")

    o2 = path_pair_model.with_path("/")
    assert o2 == Path("/")
    assert o2.inner == path_pair_model.inner


def test_path_truediv(path_pair_model: PosixPathPair[InnerModel]):
    assert path_pair_model != Path("test")

    o = path_pair_model / "test"

    assert o == Path("test")
    assert o.inner == path_pair_model.inner

    o /= "test"
    assert o == Path("test/test")
    assert o.inner == path_pair_model.inner


def test_path_rtruediv(path_pair_model: PosixPathPair[InnerModel]):
    o = "test/test" / path_pair_model
    assert o == Path("test/test")
    assert o.inner == path_pair_model.inner


def test_path_serialize(path_pair_model: PosixPathPair[InnerModel]):
    assert path_pair_model.serialize() == path_pair_model.inner.json().encode()


def test_path_deserialize(path_pair_model: PosixPathPair[InnerModel]):
    data = path_pair_model.serialize()
    o = PosixPathPair(path_pair_model, deserializer=path_pair_model._deserializer)
    assert o.deserialize(data) == True
    assert o.inner == path_pair_model.inner


def test_path_write(path_pair_model: PosixPathPair[InnerModel]):
    with tempfile.NamedTemporaryFile() as f:
        p = Path(f.name)
        o = path_pair_model.with_path(p)
        assert o.write() == True
        assert p.read_bytes() == o.serialize()
        assert p.is_file()
        assert p.exists()


def test_path_read(path_pair_model: PosixPathPair[InnerModel]):
    with tempfile.NamedTemporaryFile() as f:
        p = Path(f.name)
        o = path_pair_model.with_path(p)
        assert o.write() == True
        o2 = PathPair(o, deserializer=path_pair_model._deserializer)
        assert p.is_file()
        assert p.exists()
        assert o2.read() == True
        assert o2.inner == o.inner == path_pair_model.inner


@pytest.fixture
def collection() -> PosixPathPairCollection[InnerModel]:
    """Does not try to clean up and created assets."""
    p = Path("id_{id}_data.txt")
    pattern = "{id}"
    models = [InnerModel(foo=i) for i in range(12)]
    ids = list(map(lambda s: str(s), range(12)))

    return PathPairCollection.with_objects(
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


class Inner(BaseModel):
    foo: int


class Outer(BaseModel):
    path: PathPair[Inner]

    @validator("path", pre=True)
    def _coerce_path(cls, value: Union[PathPair[Inner], str]) -> PathPair[Inner]:
        if isinstance(value, PathPair):
            return value
        value = PathPair(
            value,
            serializer=pydantic_serializer,
            deserializer=pydantic_deserializer(Inner),
        )
        try:
            # read and deserialize from path into Inner
            value.read()
        except:
            ...
        return value


def test_integration_with_pydantic_model():
    with tempfile.NamedTemporaryFile() as file:
        path_to_file = Path(file.name)

        inner = Inner(foo=12)
        inner_path_pair = PathPair.with_object(
            inner,
            path=path_to_file,
            serializer=pydantic_serializer,
            deserializer=pydantic_deserializer(Inner),
        )
        # serialize inner T, Inner and write to disc
        assert inner_path_pair.write() == True

        # when pydanatic validates this, we will read in and deserialize into the Inner type
        outer = Outer(path=path_to_file)
        assert outer.path == path_to_file
        assert outer.path.inner == inner


@pytest.mark.parametrize("input", (42, True, "1"))
def test_bound_generics(input: Any):
    P = PathPair[int]
    P.with_object(input)


@pytest.mark.parametrize("input", ("not a number", (1,), {"key": "value"}))
def test_bound_generics_negative(input: Any):
    P = PathPair[int]
    with pytest.raises(ValidationError):
        P.with_object(input)

    with pytest.raises(ValidationError):
        P("", inner=input)  # type: ignore


def test_embedded_bound_generics():
    class M(BaseModel):
        field: PathPair[int]

    assert M(field=PathPair[int].with_object(42)).field.inner == 42
    # NOTE: `bool` is coerced to `int`
    assert M(field=PathPair[bool].with_object(True)).field.inner == 1


def test_no_binding_is_supported():
    assert PathPair("").inner is None  # type: ignore
    assert PathPair("", inner=True).inner is True  # type: ignore
    assert PathPair.with_object(True).inner is True

    p = PathPair.with_object(True)
    assert p.with_path("path") == Path("path")
    assert p.with_path("path").inner is True


class Subscribable(Protocol):
    @classmethod
    def __class_getitem__(
        cls: type, params: type[Any] | tuple[type[Any], ...]
    ) -> type[Any]: ...


def test_model_field_dunder_name_is_correctly_patched():
    # NOTE: could not use pytest parametrize here b.c. of
    # __future__ annotations type hinting
    class M(BaseModel):
        field: PathPair[int]

    assert M.__fields__["field"].type_ == PathPair[int]
    assert M.__fields__["field"].outer_type_ == PathPair[int]

    class N(BaseModel):
        field: PathPairCollection[int]

    assert N.__fields__["field"].type_ == PathPairCollection[int]
    assert N.__fields__["field"].outer_type_ == PathPairCollection[int]


def test_path_pair_collection_fails_to_init_with_wrong_inner_t():
    P = PathPairCollection[int]
    path = Path("file_{id}")
    with pytest.raises(ValidationError):
        # "a", "b", "c" cannot be coerced into `int`s
        P.with_objects(
            ["a", "b", "c"],  # type: ignore
            path=path,
            pattern="{id}",
            ids=["1", "2", "3"],
        )


def test_path_pair_collection_bound_generic():
    P = PathPairCollection[int]
    path = Path("file_{id}")
    P.with_objects(
        [1, 2, 3],
        path=path,
        pattern="{id}",
        ids=["1", "2", "3"],
    )


class InnerTypeHintModel(BaseModel):
    field: int


class TypeHintModel(BaseModel):
    # make static type checkers happy
    if TYPE_CHECKING:
        path: PathPair[InnerTypeHintModel]
    else:
        path: path_pair(
            InnerTypeHintModel,
            serializer=pydantic_serializer,
            deserializer=pydantic_deserializer(InnerTypeHintModel),
        )


def test_using_path_pair_fn_as_type_hint():
    o = TypeHintModel(**{"path": ""})  # type: ignore
    assert o.path == Path("")

    o = TypeHintModel.parse_obj({"path": ""})
    assert o.path == Path("")

    m = InnerTypeHintModel(field=42)
    o = TypeHintModel(path=PathPair[InnerTypeHintModel].with_object(m, path=""))
    assert o.path == Path("")
    assert o.path.inner == m


@pytest.mark.parametrize("ty", (PathPair[InnerTypeHintModel], PathPair))
def test_using_path_pair_fn_as_type_hint_reading_and_writing(ty: type[PathPair[Any]]):
    # test with bound an unbound type
    m = InnerTypeHintModel(field=42)
    with tempfile.TemporaryDirectory() as dir:
        model_path = Path(dir) / "model"
        o = TypeHintModel(path=ty.with_object(m, path=model_path))
        assert o.path == model_path
        assert o.path.inner is not None
        assert o.path.serialize() == pydantic_serializer(o.path.inner)

        assert o.path.write()
        assert model_path.is_file()

        r = TypeHintModel(path=model_path)  # type: ignore
        assert r.path.read()
        assert r.path.inner == o.path.inner


def test_using_path_pair_fn_as_type_hint_custom_options_respected():
    m = InnerTypeHintModel(field=42)

    def marker(): ...

    p = PathPair[InnerTypeHintModel].with_object(
        m,
        reader=marker,  # type: ignore
        writer=marker,  # type: ignore
        serializer=marker,  # type: ignore
        deserializer=marker,  # type: ignore
    )
    o = TypeHintModel(path=p)
    # TODO: these properties should likely be exposed publicly.
    #       this test will need to be updated when that happens.
    assert o.path._reader == marker  # type: ignore
    assert o.path._writer == marker  # type: ignore
    assert o.path._serializer == marker  # type: ignore
    assert o.path._deserializer == marker  # type: ignore
