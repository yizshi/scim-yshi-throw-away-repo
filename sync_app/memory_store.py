from typing import Protocol, TypeVar, Iterable, Generic, Sequence
from sync_app.store import HasId
from sync_app import exceptions
from uuid import UUID


class ObjectAlreadyInStore(Exception):
    pass


class ObjectNotFound(Exception):
    pass


T = TypeVar("T", bound="HasId")


class MemoryStore(Generic[T]):
    datastore: dict[UUID, T]

    def __init__(self):
        self.datastore = {}
        pass

    def create(self, new_record: T) -> None:
        id = new_record.get_id()
        if not all([new_record.compare_unique(x) for x in self.datastore.values()]):
            raise exceptions.ResourceConflict(
                "Could not create record {record}".format(record=new_record)
            )

        self.datastore[id] = new_record

    def get_by_id(self, key: UUID) -> T:
        if key not in self.datastore:
            raise exceptions.ResourceMissing(f"Could not find {key} in store")

        return self.datastore[key]

    def update(self, updated_record: T) -> None:
        if not updated_record.get_id() in self.datastore:
            raise exceptions.ResourceMissing()
        self.delete_by_id(updated_record.get_id())
        self.create(updated_record)

    def delete_by_id(self, key: UUID) -> None:
        if not key in self.datastore:
            raise exceptions.ResourceMissing()

        del self.datastore[key]

    def get_all(self) -> Sequence[T]:
        return list(self.datastore.values())
