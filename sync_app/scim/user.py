from sync_app.scim.resource import ResourceWithMeta, ResourceMeta, ResourceRef
from typing import Iterable, OrderedDict, Optional, TypeAlias, Mapping, List
from dataclasses import dataclass, asdict
from uuid import UUID

USER_RESOURCE_TYPE = "User"
USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"


@dataclass
class Email:
    value: Optional[str] = None
    type: Optional[str] = None
    primary: Optional[bool] = None
    display: Optional[str] = None


@dataclass
class Name:
    formatted: Optional[str] = None
    familyName: Optional[str] = None
    givenName: Optional[str] = None


class User(ResourceWithMeta):
    active: bool
    userName: str
    emails: Optional[Iterable[Email]] = None
    name: Optional[Name] = None
    groups: Optional[Iterable[ResourceRef]] = None
    displayName: Optional[str] = None

    def __init__(
        self,
        meta: ResourceMeta,
        user_id: UUID,
        displayName: Optional[str],
        active: bool,
        userName: str,
        name: Optional[Name],
        emails: Optional[Iterable[Email]],
        groups: Optional[Iterable[ResourceRef]] = None,
    ):
        super().__init__([USER_SCHEMA], meta, user_id)
        self.displayName = displayName
        self.active = active
        self.userName = userName
        self.name = name
        self.emails = emails
        self.groups = groups

    @staticmethod
    def from_dict(resource: Mapping) -> "User":
        assert resource["meta"]["resourceType"] == USER_RESOURCE_TYPE

        # account for weird core schema into a sub-attribute behavior
        user = resource.get(USER_SCHEMA, None)
        if user is None:
            user = resource

        if "emails" in user:
            emails = [Email(**e) for e in user["emails"]]
        else:
            emails = []

        if "name" in user:
            name = Name(**user["name"])
        else:
            name = None

        if "groups" in user:
            groups = [ResourceRef.from_dict(g) for g in user["groups"]]
        else:
            groups = None

        return User(
            meta=ResourceMeta(**resource["meta"]),
            user_id=UUID(resource["id"]),
            displayName=user.get("displayName", None),
            active=user.get("active", True),
            userName=user["userName"],
            name=name,
            emails=emails,
            groups=groups,
        )

    def get_id(self) -> UUID:
        return self.id

    def compare_unique(self, other: "User") -> bool:
        return all([self.id != other.id, self.userName != other.userName])

    def to_dict(self):
        resource_common = super().to_dict()
        result = {
            **resource_common,
            "active": self.active,
            "userName": self.userName,
        }
        if self.emails is not None:
            result.update({"emails": [asdict(e) for e in self.emails]})
        if self.name is not None:
            result.update({"name": asdict(self.name)})
        if self.displayName is not None:
            result.update({"displayName": self.displayName})

        return result


class NewUser(User):

    def __init__(
        self,
        meta: ResourceMeta,
        user_id: UUID,
        displayName: Optional[str],
        active: bool,
        userName: str,
        name: Optional[Name],
        emails: Optional[Iterable[Email]],
        groups: Optional[Iterable[ResourceRef]] = None,
    ):
        super().__init__(
            meta, user_id, displayName, active, userName, name, emails, groups
        )
        self.password = password
