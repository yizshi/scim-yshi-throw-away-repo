from typing import TypedDict, Literal
import json
from sync_app.scim.resource import ResourceWithMeta, Resource
import requests
from dataclasses import dataclass


Operation = Literal["add", "remove", "replace"]


@dataclass
class ServerConfiguration:
    server_url: str
    auth_token: str


class SCIMServer:
    config: ServerConfiguration

    def __init__(self, config: ServerConfiguration):
        self.config = config

    def request_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.config.auth_token,
            "Accept": "application/scim+json; charset=utf-8",
        }

    def handle_resource_change(self, operation: Operation, resource: ResourceWithMeta):
        assert resource.meta.resourceType in [
            "Group",
            "User",
        ], "Only groups and users can be sent on change"

        response = None

        # issue a PUT request downstream
        if operation == "replace":
            response = requests.put(
                f"{self.config.server_url}/{resource.meta.resourceType}s/{resource.id}",
                data=json.dumps(resource.to_dict()),
                headers=self.request_headers(),
            )

        # issue a POST request downstream
        elif operation == "add":
            resource_as_dict = resource.to_dict()
            resource_as_dict.update({"entitlements": [{"value": "00eao000000cSL6"}]})
            response = requests.post(
                f"{self.config.server_url}/{resource.meta.resourceType}s",
                data=json.dumps(resource_as_dict),
                headers=self.request_headers(),
            )

        if response is not None:
            print(response.request.headers)
            print(response.request.url)
            print(json.dumps(response.request.body, indent=2))
