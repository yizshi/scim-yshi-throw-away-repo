from typing import Mapping, Iterable, Optional, TypeAlias
from dataclasses import dataclass
from quart import url_for
import uuid
from sync_app import exceptions
from sync_app.parsers.python_filter import (
    PythonFilter,
    AttributePath,
    delete_attribute_in_path,
    get_attribute_from_path,
    set_attribute_in_path,
)

# this is a hack over a real "returned" system
# which would require a real attribute system
REQUIRED_ATTRIBUTES = [["id"], ["schemas"]]


QueryStringMapping: TypeAlias = Mapping[str, str]


@dataclass
class QueryParameters:
    attributes: Optional[Iterable[AttributePath]] = None
    excluded_attributes: Optional[Iterable[AttributePath]] = None
    filter: Optional[str] = None
    resource_id: Optional[uuid.UUID] = None


def parse_query_parameters(query_parameters: Mapping[str, str]) -> QueryParameters:
    parameters = QueryParameters()
    if "attributes" in query_parameters and query_parameters["attributes"]:
        parameters.attributes = parse_attribute_paths(query_parameters["attributes"])
    if "excludedAttributes" in query_parameters:
        parameters.excluded_attributes = parse_attribute_paths(
            query_parameters["excludedAttributes"]
        )
    if "filter" in query_parameters:
        parameters.filter = query_parameters["filter"]

    if "resource_id" in query_parameters:
        try:
            parameters.resource_id = uuid.UUID(query_parameters["resource_id"])
        except ValueError:
            raise exceptions.InvalidResourceID(
                f"{parameters.resource_id} is not a valid id"
            )

    return parameters


class RequestProvider:
    args: QueryParameters
    json_body: Optional[Mapping] = None

    def __init__(
        self,
        args: Optional[QueryStringMapping] = None,
        query_args: Optional[QueryStringMapping] = None,
        json_body: Optional[Mapping] = None,
    ):
        merged_args = {}
        if args is not None:
            merged_args.update(args)

        if query_args is not None:
            # XXX this is a bit of a hack but we shouldn't have arg collisions
            merged_args.update(dict(query_args))

        self.args = parse_query_parameters(merged_args)
        self.json_body = json_body

    def url_for_resource(self, endpoint: str, id: uuid.UUID):
        return url_for(endpoint, resource_id=str(id))


def parse_attribute_paths(raw_paths: str) -> Iterable[AttributePath]:
    paths = raw_paths.split(",")
    return [PythonFilter.parse_filter_to_path(path) for path in paths]


def filter_resource(
    resource: Mapping,
    include: Optional[Iterable[AttributePath]] = None,
    exclude: Optional[Iterable[AttributePath]] = None,
) -> Mapping:
    # yes we do need to handle sub attriutes here
    if include and exclude:
        raise exceptions.InvalidOptions

    if include is not None:
        new_resource: dict = {
            "schemas": resource["schemas"],
            "id": resource["id"],
        }
        for attribute_path in include:
            if attribute_path in REQUIRED_ATTRIBUTES:
                continue
            value = get_attribute_from_path(attribute_path, resource)
            set_attribute_in_path(attribute_path, new_resource, value)

    elif exclude is not None:
        new_resource = dict(resource)
        for attribute_path in exclude:
            if attribute_path in REQUIRED_ATTRIBUTES:
                continue
            delete_attribute_in_path(attribute_path, new_resource)
    else:
        new_resource = dict(resource)

    return new_resource
