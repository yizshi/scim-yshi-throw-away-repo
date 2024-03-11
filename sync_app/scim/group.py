from sync_app.scim.resource import ResourceWithMeta, ResourceMeta, ResourceRef
from typing import Iterable, OrderedDict, Optional, TypeAlias, Mapping, List
from dataclasses import dataclass, asdict
from uuid import UUID

GROUP_RESOURCE_TYPE = "Group"
GROUP_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"


class Group(ResourceWithMeta):
    displayName: str
    members: List[ResourceRef]

    def __init__(
        self,
        meta: ResourceMeta,
        group_id: UUID,
        displayName: str,
        members: Optional[List[ResourceRef]] = None,
    ):
        super().__init__([GROUP_SCHEMA], meta, group_id)
        self.displayName = displayName

        if members:
            self.members = members
        else:
            self.members = []

    @staticmethod
    def from_dict(resource: Mapping) -> "Group":
        assert (
            resource["meta"]["resourceType"] == GROUP_RESOURCE_TYPE
        ), "Group must have matching resource type"
        # account for weird core schema into a sub-attribute behavior
        group = resource.get(GROUP_SCHEMA, None)
        if group is None:
            group = resource

        if "members" in group:
            members = [ResourceRef.from_dict(m) for m in group["members"]]
        else:
            members = None

        return Group(
            meta=ResourceMeta(**resource["meta"]),
            group_id=UUID(resource["id"]),
            displayName=group["displayName"],
            members=members,
        )

    def to_dict(self):
        resource_common = super().to_dict()
        d = {
            **resource_common,
            "displayName": self.displayName,
            # compatibility with some SCIM services
            "name": self.displayName,
        }
        if self.members and len(self.members) > 0:
            d.update({"members": [m.to_dict() for m in self.members]})

        return d

    def compare_unique(self, other: "Group") -> bool:
        # Returns true if pair is unique
        return self.id != other.id
