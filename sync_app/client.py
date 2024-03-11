import json
from typing import Optional, Literal, Mapping, Sequence
from sync_app.scim.user import User
from sync_app.scim.group import Group
from sync_app.scim.patchop import PatchOp
from sync_app.scim.list_response import ListResponse
from dataclasses import dataclass
from sync_app.parsers.python_filter import PythonFilter
import requests


class InvalidFilter(Exception):
    pass


class Sort:
    attribute: str
    order: Literal["ascending"] | Literal["descending"]


class PageRequest:
    start_index: int
    results_per_page: int = 20


class Filter:
    filter: str

    @staticmethod
    def is_filter_valid(filter: str):
        try:
            Filter(filter)
        except InvalidFilter:
            return False

        return True

    def __init__(self, filter: str):
        PythonFilter.parse_filter_to_predicate(filter)
        # Assign filter only if it parses without an exception
        self.filter = filter


@dataclass
class ClientConfiguration:
    server_url: str
    auth_token: str

    def __init__(self, server_url: str, auth_token: str):
        self.server_url = server_url.rstrip("/")
        self.auth_token = auth_token


class SCIMClient:
    root_scim_endpoint: str

    def __init__(self, config: ClientConfiguration):
        self.config = config

    def request_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.config.auth_token,
            "Accept": "application/scim+json; charset=utf-8",
        }

    def get_user(
        self,
        id: str,
        attributes: Optional[list[str]] = None,
        excludedAttributes: Optional[list[str]] = None,
    ) -> User:
        response = self._get_resource(f"/Users/{id}", attributes, excludedAttributes)
        raw_user = response.json()
        return User.from_dict(raw_user)

    def get_users(
        self,
        filter: Optional[Filter] = None,
        attributes: Optional[list[str]] = None,
        excludedAttributes: Optional[list[str]] = None,
        sorting: Optional[Sort] = None,
        page: Optional[PageRequest] = None,
    ) -> ListResponse:
        response = self._get_resource(
            "/Users", attributes, excludedAttributes, filter, sorting, page
        )
        raw_list = response.json()
        return ListResponse.from_dict(raw_list, User)

    def get_group(
        self,
        id: str,
        attributes: Optional[list[str]] = None,
        excludedAttributes: Optional[list[str]] = None,
    ):
        response = self._get_resource(f"/Groups/{id}", attributes, excludedAttributes)
        raw_group = response.json()
        return Group.from_dict(raw_group)

    def get_groups(
        self,
        filter: Optional[Filter] = None,
        attributes: Optional[list[str]] = None,
        excludedAttributes: Optional[list[str]] = None,
        sorting: Optional[Sort] = None,
        page: Optional[PageRequest] = None,
    ) -> ListResponse:
        response = self._get_resource(
            "/Groups", attributes, excludedAttributes, filter, sorting, page
        )
        raw_list = response.json()
        return ListResponse.from_dict(raw_list, Group)

    def _get_resource(
        self,
        endpoint: str,
        attributes: Optional[list[str]] = None,
        excludedAttributes: Optional[list[str]] = None,
        filter: Optional[Filter] = None,
        sorting: Optional[Sort] = None,
        page: Optional[PageRequest] = None,
    ):
        params = {}
        if attributes:
            params["attributes"] = ",".join(attributes)

        if excludedAttributes:
            params["excludedAttributes"] = ",".join(excludedAttributes)

        if filter:
            params["filter"] = filter.filter

        if sorting:
            params["sortBy"] = sorting.attribute
            params["sortOrder"] = sorting.order

        if page:
            params["startIndex"] = page.start_index
            params["count"] = page.results_per_page

        return self._request("get", endpoint, params=params)

    def create_user(self, user: User) -> User:
        response = self._post_resource(f"/Users", user.to_dict())
        raw_user = response.json()
        return User.from_dict(raw_user)

    def create_group(self, group: Group) -> Group:
        assert (
            group.members == []
        ), "scim.dev doesn't handle creating groups with members"
        response = self._post_resource(f"/Groups", group.to_dict())
        raw_group = response.json()
        return Group.from_dict(raw_group)

    def _post_resource(self, endpoint: str, resource: Mapping):
        posted_resource = dict(resource)
        if "id" in resource:
            del posted_resource["id"]
            posted_resource["externalId"] = resource["id"]

        return self._request("post", endpoint, data=posted_resource)

    def update_user(self, id: str, ops: PatchOp) -> User:
        response = self._patch_resource(f"/Users/{id}", ops)
        raw_user = response.json()
        return User.from_dict(raw_user)

    def update_group(self, id: str, ops: PatchOp) -> Group:
        response = self._patch_resource(f"/Groups/{id}", ops)
        raw_group = response.json()
        return Group.from_dict(raw_group)

    def _patch_resource(self, endpoint: str, ops: PatchOp):
        return self._request("patch", endpoint, data=ops.to_dict())

    def replace_user(self, id: str, user: User) -> User:
        response = self._put_resource(f"/Users/{id}", user.to_dict())
        raw_user = response.json()
        return User.from_dict(raw_user)

    def replace_group(self, id: str, group: Group) -> Group:
        response = self._put_resource(f"/Groups/{id}", group.to_dict())
        raw_group = response.json()
        return Group.from_dict(raw_group)

    def _put_resource(self, endpoint: str, resource: Mapping):
        return self._request("put", endpoint, data=resource)

    def delete_user(self, id: str) -> None:
        self._delete_resource(f"/Users/{id}")

    def delete_group(self, id: str) -> None:
        self._delete_resource(f"/Groups/{id}")

    def _delete_resource(self, endpoint: str):
        return self._request("delete", endpoint)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Mapping] = None,
        data: Optional[Mapping] = None,
    ):
        url = self.config.server_url + endpoint
        if data is not None:
            request_data = json.dumps(data)
        else:
            request_data = None
        response = requests.request(
            method=method, url=url, headers=self.request_headers(), data=request_data, params=params
        )

        if not response.ok:
            print(response.text)
            response.raise_for_status()

        return response
