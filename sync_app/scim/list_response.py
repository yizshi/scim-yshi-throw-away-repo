from typing import (
    Iterable,
    OrderedDict,
    Optional,
    TypeAlias,
    Type,
    Mapping,
    Sequence,
    List,
    TypeVar,
)
from sync_app.scim.resource import Resource, ResourceWithMeta


T = TypeVar("T", bound="Resource")

LIST_RESPONSE_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:ListResponse"


class ListResponse(Resource):
    schemas: Iterable[str]
    totalResults: int
    resources: Sequence[Resource]
    startIndex: int
    itemsPerPage: int

    def __init__(
        self,
        totalResults: int,
        resources: Sequence[Resource],
        startIndex: int,
        itemsPerPage: int,
    ):
        super().__init__(["urn:ietf:params:scim:api:messages:2.0:ListResponse"])
        self.totalResults = totalResults
        self.resources = resources
        self.startIndex = startIndex
        self.itemsPerPage = itemsPerPage

    def to_dict(self):
        result: dict = {
            "schemas": self.schemas,
            "totalResults": self.totalResults,
        }
        if self.totalResults == 0:
            return result
        else:
            result["Resources"] = [r.to_dict() for r in self.resources]

        # if len(list(self.resources)) == self.totalResults:
        #     # assume this is not a partial result
        #     return result

        result["itemsPerPage"] = self.itemsPerPage
        result["startIndex"] = self.startIndex
        return result

    @staticmethod
    def from_list(
        l: Sequence[T], startIndex: int = 1, itemsPerPage=20
    ) -> "ListResponse":
        return ListResponse(
            totalResults=len(l),
            resources=l[startIndex - 1 : itemsPerPage],
            startIndex=startIndex,
            itemsPerPage=itemsPerPage,
        )

    @staticmethod
    def from_dict(resource: Mapping, list_type: Type[Resource]) -> "ListResponse":
        assert (
            LIST_RESPONSE_SCHEMA in resource["schemas"]
        ), "object is not a list response"

        return ListResponse(
            totalResults=resource["totalResults"],
            resources=[list_type.from_dict(r) for r in resource["Resources"]],
            startIndex=resource["startIndex"],
            itemsPerPage=resource["itemsPerPage"],
        )
