from typing import TypeVar, Sequence
from typing import Protocol, TypeVar, Iterable
from uuid import UUID


S = TypeVar("S")


class HasId(Protocol):
    def get_id(self) -> UUID:
        ...

    def compare_unique(self: S, other: S) -> bool:
        ...


T = TypeVar("T", bound="HasId")


class Store(Protocol[T]):
    datastore: dict[UUID, T]

    def create(self, new_record: T) -> None:
        ...

    def get_by_id(self, key: UUID) -> T:
        ...

    def update(self, updated_record: T) -> None:
        ...

    def delete_by_id(self, key: UUID) -> None:
        ...

    def get_all(self) -> Sequence[T]:
        ...
