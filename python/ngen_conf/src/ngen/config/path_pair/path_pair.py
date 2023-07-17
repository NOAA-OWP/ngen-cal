import os
from pathlib import Path, PosixPath, WindowsPath

from .protocol import Reader, Writer, Serializer, Deserializer
from .common import path_reader, path_writer
from ._abc_mixins import AbstractPathPairMixin, AbstractPathPairCollectionMixin
from ._mixins import PathPairMixin, PathPairCollectionMixin

from typing import Any, Dict, Generic, Optional, Union, List
from typing_extensions import Self
from .typing import StrPath, T


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

    def __new__(
        cls,
        *args: StrPath,
        inner: Optional[T] = None,
        reader: Reader = path_reader,
        writer: Writer = path_writer,
        serializer: Optional[Serializer[T]] = None,
        deserializer: Optional[Deserializer[T]] = None,
        **kwargs: Any,
    ) -> Union["WindowsPathPair[T]", "PosixPathPair[T]"]:
        cls = WindowsPathPair[T] if os.name == "nt" else PosixPathPair[T]
        self: Union[WindowsPathPair[T], PosixPathPair[T]] = Path.__new__(
            cls, *args, **kwargs
        )
        self._inner = inner
        self._serializer = serializer
        self._deserializer = deserializer
        self._reader = reader
        self._writer = writer
        return self

    @classmethod
    def with_object(
        cls,
        obj: T,
        *,
        path: StrPath = "",
        reader: Reader = path_reader,
        writer: Writer = path_writer,
        serializer: Optional[Serializer[T]] = None,
        deserializer: Optional[Deserializer[T]] = None,
    ) -> Union["PosixPathPair[T]", "WindowsPathPair[T]"]:
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
    def __modify_schema__(cls, field_schema: Dict[str, Any]):
        field_schema.clear()
        field_schema["format"] = "path"
        field_schema["type"] = "string"

    @classmethod
    def validate(cls, value: Any) -> Self:
        if isinstance(value, PathPair):
            return value

        return PathPair(value)


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

    def __new__(
        cls,
        *args: StrPath,
        pattern: str,
        inner: Optional[List["PosixPathPair[T]"]] = None,
        reader: Reader = path_reader,
        writer: Writer = path_writer,
        serializer: Optional[Serializer[T]] = None,
        deserializer: Optional[Deserializer[T]] = None,
        **kwargs: Any,
    ) -> Union["WindowsPathPairCollection[T]", "PosixPathPairCollection[T]"]:
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

        self: Union[
            WindowsPathPairCollection[T], PosixPathPairCollection[T]
        ] = Path.__new__(
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
        p: "PosixPathPair[T]",
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
        objs: List[T],
        *,
        path: Path,
        pattern: str,
        ids: List[str],
        reader: Optional[Reader] = path_reader,
        writer: Optional[Writer] = path_writer,
        serializer: Optional[Serializer[T]] = None,
        deserializer: Optional[Deserializer[T]] = None,
    ) -> Union["PosixPathPairCollection[T]", "WindowsPathPairCollection[T]"]:
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
    def __modify_schema__(cls, field_schema: Dict[str, Any]):
        field_schema.clear()
        field_schema["format"] = "path"
        field_schema["type"] = "string"

    @classmethod
    def validate(cls, value: Any) -> Self:
        if isinstance(value, PathPairCollection):
            return value

        return PathPairCollection(value, pattern="")


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
