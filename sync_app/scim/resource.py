import json
from typing import (
    Iterable,
    OrderedDict,
    Optional,
    TypeAlias,
    Mapping,
    List,
    TypeVar,
    Protocol,
)
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Literal
from uuid import UUID

ResourceType = Literal[
    "User", "Group", "ServiceProviderConfig", "ResourceType", "Schema"
]


@dataclass
class ResourceMeta:
    resourceType: ResourceType
    created: datetime
    lastModified: datetime
    location: str  # url
    version: Optional[str] = None

    def to_dict(self):
        d = {
            "resourceType": self.resourceType,
            "create": str(self.created),
            "lastModified": str(self.lastModified),
            "location": self.location,
        }
        if self.version:
            d.update({"version": self.version})

        return d

    @staticmethod
    def create_meta(resource_type: ResourceType, location: str) -> "ResourceMeta":
        return ResourceMeta(
            resourceType=resource_type,
            created=datetime.now(),
            lastModified=datetime.now(),
            version="1",
            location=location,
        )


class Resource:
    schemas: Iterable[str]

    def __init__(self, schemas: Iterable[str]):
        self.schemas = schemas

    @staticmethod
    def from_dict(d):
        raise NotImplementedError

    def to_json(self):
        json.dumps(self.to_dict())

    def to_dict(self):
        return {"schemas": self.schemas}


class ResourceWithMeta(Resource):
    meta: ResourceMeta
    id: UUID

    def __init__(self, schemas: Iterable[str], meta: ResourceMeta, resource_id: UUID):
        super().__init__(schemas)
        self.meta = meta
        self.id = resource_id

    def get_id(self) -> UUID:
        return self.id

    def to_json(self):
        json.dumps(self.to_dict())

    def to_dict(self):
        resource_common = super().to_dict()
        return {**resource_common, "meta": self.meta.to_dict(), "id": str(self.id)}


@dataclass
class ResourceRef:
    ref: str
    value: str
    display: str

    # We can't use dict expansion here because the "$" prefix in $ref causes problems
    @staticmethod
    def from_dict(d: Mapping):
        return ResourceRef(ref=d["$ref"], value=d["value"], display=d["display"])

    def to_dict(self):
        return {
            "$ref": self.ref,
            "value": self.value,
            "display": self.display,
        }


T = TypeVar("T", bound="Resource")


class SerializableResource(Protocol):
    def to_dict(self) -> Mapping:
        ...
