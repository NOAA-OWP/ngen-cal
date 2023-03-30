from itertools import zip_longest
from pathlib import Path

from typing import Generic, Optional, Union, Iterator, Iterable, TYPE_CHECKING
from typing_extensions import Self
from .typing import StrPath, T

if TYPE_CHECKING:
    from .path_pair import PosixPathPair, WindowsPathPair, PathPairCollection


class PathPairMixin(Generic[T]):
    def __truediv__(self, key: StrPath) -> Self:
        return self.with_path(Path(self).joinpath(Path(key)))

    def __rtruediv__(self, key: StrPath) -> Self:
        return self.with_path(Path(key).joinpath(self))

    @property
    def parent(self) -> Path:
        return Path(self).parent

    @property
    def inner(self) -> Optional[T]:
        return self._inner

    def with_path(self, *args: StrPath) -> Self:
        return self.from_object(
            self.inner,
            path=Path(*args),
            reader=self._reader,
            writer=self._writer,
            serializer=self._serializer,
            deserializer=self._deserializer,
        )

    def serialize(self) -> Optional[bytes]:
        if self._serializer is None or self._inner is None:
            return None

        return self._serializer(self.inner)

    def deserialize(self, data: bytes) -> bool:
        if self._deserializer is None or self._reader is None:
            return False

        self._inner = self._deserializer(data)
        return True

    def read(self) -> bool:
        return self.deserialize(self._reader(self))

    def write(self) -> bool:
        if self._serializer is None or self._inner is None:
            return False

        self._writer(self, self.serialize())
        return True


class PathPairCollectionMixin(PathPairMixin[T]):
    def __truediv__(self, key: StrPath) -> Self:
        # noop
        return self

    def __rtruediv__(self, key: StrPath) -> Self:
        # avoid circular import
        from .path_pair import PathPairCollection

        inner = [key / item for item in self._inner]
        new_path = Path(key).joinpath(self)
        return PathPairCollection(
            new_path,
            pattern=self._pattern,
            inner=inner,
            reader=self._reader,
            writer=self._writer,
            serializer=self._serializer,
            deserializer=self._deserializer,
        )

    def _get_filenames(self) -> Iterator[Path]:
        prefix, _, suffix = self.name.partition(self.pattern)
        glob_term = f"{prefix}*{suffix}"
        yield from self.parent.glob(glob_term)

    def with_path(self, *args: StrPath) -> Self:
        # TODO: this seems like the _right_ thing to do here, but this could change in the future.
        # noop
        return self

    @property
    def pattern(self) -> str:
        return self._pattern

    @property
    def inner(self) -> Iterable[T]:
        for item in self._inner:
            yield item.inner

    @property
    def inner_pair(
        self,
    ) -> Union[Iterator["PosixPathPair[T]"], Iterable["WindowsPathPair[T]"]]:
        for item in self._inner:
            yield item

    def with_path(self, *args: StrPath) -> Self:
        # noop
        return self

    def with_pattern(self, pattern: str) -> "PathPairCollection[T]":
        # avoid circular import
        from .path_pair import PathPairCollection

        return PathPairCollection[T](
            self,
            pattern=pattern,
            inner=self._inner,
            reader=self._reader,
            writer=self._writer,
            serializer=self._serializer,
            deserializer=self._deserializer,
        )

    def serialize(self) -> Iterable[bytes]:
        if self._serializer is None or self._inner is None:
            return None

        for item in self.inner:
            yield self._serializer(item)

    def deserialize(
        self, data: Iterable[bytes], *, paths: Optional[Iterable[StrPath]] = None
    ) -> bool:
        """
        Deserialize collection of bytes into T's and wrap each T as a `PathPair[T]`. Replace
        `self`'s inner collection with the deserialized collection. Returns `False` if there is no
        deserializer on `self`.

        If `paths` is None, the inner `PathPair[T]`'s have `self`'s path.
        """
        # avoid circular import
        from .path_pair import PathPair

        if self._deserializer is None:
            return False

        if paths is None:
            deserialized_path = Path(self)
            deserialized = [
                PathPair.from_object(
                    self._deserializer(item),
                    path=deserialized_path,
                    reader=self._reader,
                    writer=self._writer,
                    serializer=self._serializer,
                    deserializer=self._deserializer,
                )
                for item in data
            ]
        else:
            error_message = (
                "Iterators `data` and `paths` have different stopping points."
            )
            deserialized = []
            for item, path in zip_longest(data, paths, fillvalue=ValueError):
                if item == ValueError or path == ValueError:
                    raise ValueError(error_message)

                path_pair = PathPair.from_object(
                    self._deserializer(item),
                    path=path,
                    reader=self._reader,
                    writer=self._writer,
                    serializer=self._serializer,
                    deserializer=self._deserializer,
                )
                deserialized.append(path_pair)

        self._inner = deserialized
        return True

    def read(self) -> bool:
        data = (self._reader(path) for path in self._get_filenames())
        return self.deserialize(data, paths=self._get_filenames())

    def write(self) -> bool:
        if self._serializer is None or self._inner is None or self._writer is None:
            return False

        for item in self._inner:
            self._writer(item, item.serialize())

        return True

    def unlink(self, missing_ok: bool = False):
        for item in self._inner:
            item.unlink(missing_ok=missing_ok)
