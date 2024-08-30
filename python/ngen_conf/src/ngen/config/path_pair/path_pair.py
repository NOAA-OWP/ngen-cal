from __future__ import annotations

import os
from pathlib import Path, PosixPath, WindowsPath

from .protocol import Reader, Writer, Serializer, Deserializer
from .common import path_reader, path_writer
from ._abc_mixins import AbstractPathPairMixin, AbstractPathPairCollectionMixin
from ._mixins import PathPairMixin, PathPairCollectionMixin

from typing import TYPE_CHECKING, Any, Generic, List, Optional, TypeVar
from typing_extensions import Self
from .typing import StrPath, T

from pydantic.generics import GenericModel
from pydantic.validators import path_validator

if TYPE_CHECKING:
    from pydantic.fields import ModelField
    from pydantic.typing import CallableGenerator
    from typing import ClassVar


class _MaybeInner(GenericModel, Generic[T]):
    """
    Model used in `PathPair` and `PathPairCollection` overrides of `__new__` to
    validate their inner `T`.
    """

    inner: Optional[T]


class PathPair(AbstractPathPairMixin[T], Path, Generic[T]):
    """A `pathlib.Path` subclass that encapsulates some inner `T` and methods for reading, writing,
    and de/serializing to and from a `T`. Similarly to `pathlib.Path`, creating a `PathPair` will
    return a OS specific subclass (`PosixPathPair` or `WindowsPathPair`).

    The default reader and writer implementations operate on disk. Alternative reader and writer
    types can be provided assuming they following the `ngen.config.path_pair.protocol` `Reader` and
    `Writer` protocols (interfaces). This could, for example, enable reading and writing from the
    network.

    serializer's and deserializer's are type specific, and thus have no default. However,
    `ngen.config.path_pair.common` contains generic serializers and deserializer that may be of
    interest (e.g. `pydantic_serializer` and `pydantic_deserializer`). Alternative serializer and
    deserializer types can be provided assuming they follow the `ngen.config.path_pair.protocol`
    `Serializer` and `Deserializer` protocols (interfaces).
    """

    @classmethod
    def __class_getitem__(
        cls: type[Self], params: type[Any] | tuple[type[Any], ...]
    ) -> type[Any]:
        # if `params` contains all 'concrete' types (no TypeVars), return a
        # subclass of `cls` with a class attribute, `_parameters`, containing a
        # tuple of the concrete types. otherwise, return `cls`
        #
        # see https://peps.python.org/pep-0560/ for __class_getitem__ details
        return _maybe_subclass_with_bound_generic_type_info(cls, params)

    def __new__(  # type: ignore
        cls,
        *args: StrPath,
        inner: T | None = None,
        reader: Reader = path_reader,
        writer: Writer = path_writer,
        serializer: Serializer[T] | None = None,
        deserializer: Deserializer[T] | None = None,
        **kwargs: Any,
    ) -> WindowsPathPair[T] | PosixPathPair[T]:
        # `cls` can either be 'unbound' or 'concrete'
        # 'unbound': some generic parameters have not been specified
        # 'concrete': all generic parameters are concrete types
        #
        # in the 'concrete' case, `__class_getitem__` will have returned a
        # subtype of `cls` with a class attribute, `_parameters`, containing
        # the bound generic parameter types.
        # Here, we use the 'bound' concrete parameter type to parametrize a
        # generic pydantic model. An instance of the model is created with the
        # passed in `inner` to perform validation. If validation succeeds, we
        # can safely move the validated and coerced `inner` into `self._inner`.
        if inner is not None and hasattr(cls, "_parameters"):
            assert len(cls._parameters) == 1, "only expected 1 bound parameter"  # type: ignore
            inner = _MaybeInner[cls._parameters[0]](inner=inner).inner  # type: ignore
        cls = WindowsPathPair[T] if os.name == "nt" else PosixPathPair[T]
        self: WindowsPathPair[T] | PosixPathPair[T] = Path.__new__(cls, *args, **kwargs)
        self._inner = inner  # type: ignore
        self._serializer = serializer  # type: ignore
        self._deserializer = deserializer  # type: ignore
        self._reader = reader  # type: ignore
        self._writer = writer  # type: ignore
        return self

    @classmethod
    def with_object(
        cls,
        obj: T,
        *,
        path: StrPath = "",
        reader: Reader = path_reader,
        writer: Writer = path_writer,
        serializer: Serializer[T] | None = None,
        deserializer: Deserializer[T] | None = None,
    ) -> PosixPathPair[T] | WindowsPathPair[T]:
        return cls(
            Path(path),
            inner=obj,
            reader=reader,
            writer=writer,
            serializer=serializer,
            deserializer=deserializer,
        )  # type: ignore

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]):
        field_schema.clear()
        field_schema["format"] = "path"
        field_schema["type"] = "string"

    @classmethod
    def validate(cls: type[PathPair[T]], value: Any) -> PathPair[T]:
        if isinstance(value, PathPair):
            return cls(
                Path(value),  # type: ignore
                inner=value.inner,  # type: ignore
                reader=value._reader,  # type: ignore
                writer=value._writer,  # type: ignore
                serializer=value._serializer,  # type: ignore
                deserializer=value._deserializer,  # type: ignore
            )

        return cls(path_validator(value))


class PathPairCollection(AbstractPathPairCollectionMixin[T], Path, Generic[T]):
    """A `pathlib.Path` subclass that encapsulates a collection of `T`'s and methods for reading,
    writing, and de/serializing to and from a the collection of `T`'s. This type enables treating a
    collection of paths, that follow some naming convention, as a single path object. Similarly to
    `pathlib.Path`, creating a `PathPairCollection` will return a OS specific subclass
    (`PosixPathPairCollection` or `WindowsPathPairCollection`).

    The default reader and writer implementations operate on disk. Alternative reader and writer
    types can be provided assuming they following the `ngen.config.path_pair.protocol` `Reader` and
    `Writer` protocols (interfaces). This could, for example, enable reading and writing from the
    network.

    serializer's and deserializer's are type specific, and thus have no default. However,
    `ngen.config.path_pair.common` contains generic serializers and deserializer that may be of
    interest (e.g. `pydantic_serializer` and `pydantic_deserializer`). Alternative serializer and
    deserializer types can be provided assuming they follow the `ngen.config.path_pair.protocol`
    `Serializer` and `Deserializer` protocols (interfaces).
    """

    @classmethod
    def __class_getitem__(
        cls: type[Self], params: type[Any] | tuple[type[Any], ...]
    ) -> type[Any]:
        # if `params` contains all 'concrete' types (no TypeVars), return a
        # subclass of `cls` with a class attribute, `_parameters`, containing a
        # tuple of the concrete types. otherwise, return `cls`
        #
        # see https://peps.python.org/pep-0560/ for __class_getitem__ details
        return _maybe_subclass_with_bound_generic_type_info(cls, params)

    def __new__(  # type: ignore
        cls,
        *args: StrPath,
        pattern: str,
        inner: list[PosixPathPair[T]] | None = None,
        reader: Reader = path_reader,
        writer: Writer = path_writer,
        serializer: Serializer[T] | None = None,
        deserializer: Deserializer[T] | None = None,
        **kwargs: Any,
    ) -> WindowsPathPairCollection[T] | PosixPathPairCollection[T]:
        # `cls` can either be 'unbound' or 'concrete'
        # 'unbound': some or all generic parameters have not been specified
        # 'concrete': all generic parameters are bound
        #
        # in the 'concrete' case, `__class_getitem__` will have returned a
        # subtype of `cls` with a class attribute, `_parameters`, containing
        # the bound generic parameter types.
        # Here, we use the bound, realized, parameter type to parametrize a
        # generic pydantic model. An instance of the model is created with the
        # passed in `inner` to perform validation. If validation succeeds, we
        # can safely move the validated and coerced `inner` into `self._inner`.
        if inner is not None and hasattr(cls, "_parameters"):
            assert len(cls._parameters) == 1, "only expected 1 bound parameter"  # type: ignore
            inner = _MaybeInner[List[PathPair[cls._parameters[0]]]](inner=inner).inner  # type: ignore

        cls = (
            WindowsPathPairCollection[T]
            if os.name == "nt"
            else PosixPathPairCollection[T]
        )

        template_str = Path(*args)

        if inner is None:
            inner = []

        prefix, _, suffix = template_str.name.partition(pattern)
        for item in inner:
            if PathPairCollection._get_id(item, prefix, suffix) == "":
                raise ValueError(
                    f"Filename not derived from template and pattern, {template_str.name!r} {pattern!r}: {item}"
                )

        self: WindowsPathPairCollection[T] | PosixPathPairCollection[T] = Path.__new__(
            cls,
            *args,
            inner=inner,
            reader=reader,
            writer=writer,
            serializer=serializer,
            deserializer=deserializer,
            **kwargs,
        )
        self._inner = inner
        self._serializer = serializer
        self._deserializer = deserializer
        self._reader = reader
        self._writer = writer
        self._pattern = pattern
        return self

    @staticmethod
    def _get_id(
        p: PosixPathPair[T],
        prefix: str,
        suffix: str,
    ) -> str:
        assert prefix != "" and suffix != ""

        return p.name[len(prefix) : -len(suffix)]

    @classmethod
    def cwd(cls) -> Path:
        return Path.cwd()

    @classmethod
    def home(cls) -> Path:
        return Path.home()

    @classmethod
    def with_objects(
        cls,
        objs: list[T],
        *,
        path: Path,
        pattern: str,
        ids: list[str],
        reader: Reader | None = path_reader,
        writer: Writer | None = path_writer,
        serializer: Serializer[T] | None = None,
        deserializer: Deserializer[T] | None = None,
    ) -> PosixPathPairCollection[T] | WindowsPathPairCollection[T]:
        assert len(objs) == len(ids)
        prefix, _, suffix = path.name.partition(pattern)
        assert prefix != "" and suffix != ""

        pairs = []
        for idx, item in enumerate(objs):
            fp = path.parent / f"{prefix}{ids[idx]}{suffix}"
            pair = PathPair.with_object(
                item,
                path=fp,
                reader=reader,
                writer=writer,
                serializer=serializer,
                deserializer=deserializer,
            )
            pairs.append(pair)

        return cls(
            path,
            pattern=pattern,
            inner=pairs,
            reader=reader,
            writer=writer,
            serializer=serializer,
            deserializer=deserializer,
        )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]):
        field_schema.clear()
        field_schema["format"] = "path"
        field_schema["type"] = "string"

    @classmethod
    def validate(cls, value: Any) -> Self:
        if isinstance(value, PathPairCollection):
            # NOTE: `PathPairCollection[Foo]` and `PathPairCollection[Bar]`
            # are both _instances_ of `PathPairCollection`.
            # Thus, `value` must be revalidated against `cls`'s validators.
            return cls(
                Path(value),
                inner=value.inner,  # type: ignore
                serializer=value._serializer,  # type: ignore
                deserializer=value._deserializer,  # type: ignore
                reader=value.reader,  # type: ignore
                writer=value.writer,  # type: ignore
                pattern=value.pattern,  # type: ignore
            )

        return PathPairCollection(path_validator(value), pattern="")


_bound_generic_type_cache: dict[tuple[type, tuple[Any, ...]], type] = {}
"""
mapping from (cls, bound generic Ts) -> subtype(cls) w/ ref to bound generics
see `_maybe_subclass_with_bound_generic_type_info` for implementation details
"""


def _maybe_subclass_with_bound_generic_type_info(
    cls: type[T], params: type[Any] | tuple[type[Any], ...]
) -> type[T]:
    """
    NOTE: ONLY CALL FROM IN A CLASS'S `__class_getitem__` CLASS METHOD!

    two cases:
    - returns `cls` if `params` contains an 'unbound' generic (i.e. `TypeVar` instance)
    - returns a subclass of `cls` with a class attribute, `_parameters`, that
      contains a tuple of concrete type's 'bound' to `cls`

    see https://peps.python.org/pep-0560/ for details
    """
    # see https://peps.python.org/pep-0560/ for details
    if not isinstance(params, tuple):
        params = (params,)
    # skip types with 'unbound' generics
    if any(isinstance(p, TypeVar) for p in params):
        return cls

    # returns a subtype of `cls` with a class variable `_parameters` of
    # concrete types bound that are 'bound' to the generic `TypeVar`s
    class WithBoundParams(cls):
        _parameters: tuple[type[Any], ...] = params

    # patch __name__ to 'hide' `WithBoundParams` subclass indirection
    # if this type were embedded in a pydantic model and we _did not_ do
    # this, the `ModelField.type_` attribute would _incorrectly_ point to
    # the `WithBoundParams` type instead of `cls`.
    # see `test_path_pair.test_model_field_dunder_name_is_correctly_patched`
    WithBoundParams.__qualname__ = PathPair.__qualname__

    if (cls, params) not in _bound_generic_type_cache:
        _bound_generic_type_cache[(cls, params)] = WithBoundParams
    return _bound_generic_type_cache[(cls, params)]


class PosixPathPair(PathPairMixin[T], PathPair[T], PosixPath):
    __slots__ = (
        "_inner",  # Optional[T]
        "_serializer",  # Serializer[T]
        "_deserializer",  # Deserializer[T]
        "_reader",  # Reader
        "_writer",  # Writer
    )


class WindowsPathPair(PathPairMixin[T], PathPair[T], WindowsPath):
    __slots__ = (
        "_inner",  # Optional[T]
        "_serializer",  # Serializer[T]
        "_deserializer",  # Deserializer[T]
        "_reader",  # Reader
        "_writer",  # Writer
    )


class PosixPathPairCollection(
    PathPairCollectionMixin[T], PathPairCollection[T], PosixPath
):
    __slots__ = (
        "_inner",  # Union[List[ObjectPosixPathPair[T], List[ObjectWindowsPathPair[T]]]]
        "_serializer",  # Serializer[T]
        "_deserializer",  # Deserializer[T]
        "_reader",  # Reader
        "_writer",  # Writer
        "_pattern",  # str
    )


class WindowsPathPairCollection(
    PathPairCollectionMixin[T], PathPairCollection[T], WindowsPath
):
    __slots__ = (
        "_inner",  # Union[List[ObjectPosixPathPair[T], List[ObjectWindowsPathPair[T]]]]
        "_serializer",  # Serializer[T]
        "_deserializer",  # Deserializer[T]
        "_reader",  # Reader
        "_writer",  # Writer
        "_pattern",  # str
    )
