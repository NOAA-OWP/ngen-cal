from abc import ABC, abstractmethod

from typing import Generic, Iterable, Optional
from typing_extensions import Self

from .typing import StrPath, T


class AbstractPathPairMixin(ABC, Generic[T]):
    """
    API that should be mixed in with a `pathlib.Path` subclass to expose methods for reading,
    writing, and de/serializing to and from a wrapped inner type `T`.

    Additionally, this abstraction serves to improve _factory classes_ type hints by denoting that
    all subtypes of the factory implement the API. This follows suit with the factory class
    `pathlib.Path` that returns an OS dependent subtype (e.g. `pathlib.WindowsPath` or
    `pathlib.PosixPath`) that implements `pathlib.Path`'s API.
    """

    @property
    @abstractmethod
    def inner(self) -> Optional[T]:
        """Return the inner object if it exists."""

    @abstractmethod
    def with_path(self, *args: StrPath) -> Self:
        """
        Return a _new_ `PathPair` instance with the same reader, writer, and de/serializer as the
        current instance but with a different path.

        Returns
        -------
        Self
        """

    @abstractmethod
    def serialize(self) -> Optional[bytes]:
        """
        If the inner `T` exists, return a serialized version.

        Returns
        -------
        Optional[bytes]
        """

    @abstractmethod
    def deserialize(self, data: bytes) -> bool:
        """
        Try to deserialize the provided bytes into an inner encapsulated `T`. Throw if
        deserialization fails. If an inner `T` already exists and it deserializes correctly,
        replace the inner `T` with the new instance. Return `True` if success and `False` if there
        is not enough information to attempt deserialization.

        Parameters
        ----------
        data : bytes

        Returns
        -------
        bool
            True if successful, False if there is not enough information to attempt deserialization.
        """

    @abstractmethod
    def read(self):
        """
        Try to read the current path and deserialize into an inner encapsulated `T`. If an inner `T`
        already exists and it deserializes correctly, replace the inner `T` with the new instance.
        Throw if deserialization or reading fails.  Return `True` if success and `False` if there is
        not enough information to attempt deserialization.

        Returns
        -------
        bool
            True if successful, False if there is not enough information to attempt deserialization.
        """

    @abstractmethod
    def write(self) -> bool:
        """
        Try to serialize the inner `T` and write to the current path. Throw if serialization or
        writing fails. Return `True` if is success and `False` if there is not enough
        information to attempt deserialization.

        Returns
        -------
        bool
            True if successful, False if there is not enough information to attempt serialization.
        """


class AbstractPathPairCollectionMixin(ABC, Generic[T]):
    """
    API that should be mixed in with a `pathlib.Path` subclass to expose methods for reading,
    writing, and de/serializing to and from a collection of wrapped inner `AbstractPathPairMixin[T]`s.
    """

    @property
    @abstractmethod
    def pattern(self) -> str:
        """
        String that should be replaced within the path to build the collection of files.

        Example:
            path: "/domain_files/domain_{id}.geojson"
            pattern: "{id}"
        """

    @property
    @abstractmethod
    def inner(self) -> Iterable[T]:
        """
        An iterable that returns inner `T`s
        """

    @property
    @abstractmethod
    def inner_pair(
        self,
    ) -> Iterable[AbstractPathPairMixin[T]]:
        """
        An iterable that returns inner `AbstractPathPairMixin[T]`s
        """

    @abstractmethod
    def with_pattern(self, pattern: str) -> Self:
        """
        Return a _new_ `PathPairCollection` instance with the same reader, writer, and de/serializer
        as the current instance but with a different pattern.

        Returns
        -------
        Self
        """

    @abstractmethod
    def serialize(self) -> Iterable[bytes]:
        """
        Return an iterable of serialized inner `T`'s
        """

    @abstractmethod
    def deserialize(
        self, data: Iterable[bytes], *, paths: Optional[Iterable[StrPath]] = None
    ) -> bool:
        """
        Deserialize iterable of bytes into `T`'s and wrap each `T` as a `PathPair[T]`. Replace
        `self`'s inner collection with the deserialized collection. Return `True` if success and
        `False` if there is not enough information to attempt deserialization.

        If `paths` is None, the inner `PathPair[T]`'s have `self`'s path.

        If `paths` is provided, each _i_th inner `PathPair[T]` will have the path at the _i_th
        iteration. Likewise, `data` and `paths` must iterate _k_ times.

        Parameters
        ----------
        data : Iterable[bytes]
        paths : Optional[Iterable[StrPath]], optional
            If provided, inner _i_th `PathPair[T]`s will have the associated _i_th path, by default None

        Returns
        -------
        bool
            True if successful, False if there is not enough information to attempt deserialization
        """

    @abstractmethod
    def read(self) -> bool:
        """
        Try to read and deserialize files on the current path that follow the current prefix.
        Throw if deserialization or reading fails. If an inner collection already exists and read
        is successful, the previous collection is *replaced*. Return `True` if success and `False`
        if there is not enough information to attempt deserialization.

        Returns
        -------
        bool
            True if successful, False if there is not enough information to attempt reading or deserialization
        """

    @abstractmethod
    def write(self) -> bool:
        """
        Try to serialize and write the inner collection of `PathPair[T]`s to their pathname. Throw
        if serialization or writing fails. Does not ensure cleanup. Return `True` if is success and
        `False` if there is not enough information to attempt serialization or writing.

        Returns
        -------
        bool
            True if is successful, False if there is not enough information to attempt serialization or writing
        """
