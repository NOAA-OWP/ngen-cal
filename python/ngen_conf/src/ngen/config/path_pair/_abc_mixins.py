from abc import ABC, abstractmethod

from typing import Generic, Iterable, Optional
from typing_extensions import Self

from .typing import StrPath, T


class AbstractPathPairMixin(ABC, Generic[T]):
    @property
    @abstractmethod
    def inner(self) -> Optional[T]:
        ...

    @abstractmethod
    def with_path(self, *args: StrPath) -> Self:
        ...

    @abstractmethod
    def serialize(self) -> Optional[bytes]:
        ...

    @abstractmethod
    def deserialize(self, data: bytes) -> bool:
        ...

    @abstractmethod
    def read(self) -> bool:
        ...

    @abstractmethod
    def write(self) -> bool:
        ...


class AbstractPathPairCollectionMixin(ABC, Generic[T]):
    @property
    @abstractmethod
    def pattern(self) -> str:
        ...

    @property
    @abstractmethod
    def inner(self) -> Iterable[T]:
        ...

    @property
    @abstractmethod
    def inner_pair(
        self,
    ) -> Iterable[AbstractPathPairMixin[T]]:
        ...

    @abstractmethod
    def with_pattern(self, pattern: str) -> Self:
        ...

    @abstractmethod
    def serialize(self) -> Iterable[bytes]:
        ...

    @abstractmethod
    def deserialize(
        self, data: Iterable[bytes], *, paths: Optional[Iterable[StrPath]] = None
    ) -> bool:
        ...

    @abstractmethod
    def read(self) -> bool:
        ...

    @abstractmethod
    def write(self) -> bool:
        ...
