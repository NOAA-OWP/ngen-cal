import os
from pathlib import Path, PosixPath, WindowsPath

from .protocol import Reader, Writer, Serializer, Deserializer
from .common import path_reader, path_writer
from ._mixins import PathPairMixin, PathPairCollectionMixin

from typing import (
    Any,
    Generic,
    Optional,
    Union,
    List,
)
from .typing import StrPath, T


class PathPair(Path, Generic[T]):
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
    def from_object(
        cls,
        o: T,
        *,
        path: StrPath = "",
        reader: Optional[Reader] = path_reader,
        writer: Optional[Writer] = path_writer,
        serializer: Optional[Serializer[T]] = None,
        deserializer: Optional[Deserializer[T]] = None,
    ) -> Union["PosixPathPair[T]", "WindowsPathPair[T]"]:
        return cls(
            Path(path),
            inner=o,
            reader=reader,
            writer=writer,
            serializer=serializer,
            deserializer=deserializer,
        )


class PathPairCollection(Path, Generic[T]):
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
    def from_objects(
        cls,
        o: List[T],
        *,
        path: Path,
        pattern: str,
        ids: List[str],
        reader: Optional[Reader] = path_reader,
        writer: Optional[Writer] = path_writer,
        serializer: Optional[Serializer[T]] = None,
        deserializer: Optional[Deserializer[T]] = None,
    ) -> Union["PosixPathPairCollection[T]", "WindowsPathPairCollection[T]"]:
        assert len(o) == len(ids)
        prefix, _, suffix = path.name.partition(pattern)
        assert prefix != "" and suffix != ""

        pairs = []
        for idx, item in enumerate(o):
            fp = path.parent / f"{prefix}{ids[idx]}{suffix}"
            pair = PathPair.from_object(
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
