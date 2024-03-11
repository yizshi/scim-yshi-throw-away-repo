from quart import url_for
from sync_app.schema import ResourceValidator
from sync_app.scim.resource import ResourceMeta
from sync_app.server import SCIMServer
from sync_app.parsers.python_filter import (
    PythonFilter,
)
from sync_app.scim.group import Group
from sync_app.scim.list_response import ListResponse
from sync_app.store import Store
from typing import Mapping
from sync_app.handlers import common
from sync_app import exceptions
import uuid


def validate_group(validator: ResourceValidator, resource: Mapping) -> Group:
    validation_result = validator.validate(resource)
    if validation_result.valid:
        return Group.from_dict(resource)
    else:
        for error in validation_result.errors:
            if "is a required property" in error.message:
                raise exceptions.InvalidValue("Resource is missing a required value")
        raise exceptions.ResourceValidationError("Could not validate resource as group")


def handle_post_groups(
    store: Store[Group],
    validator: ResourceValidator,
    scim_server: SCIMServer,
    request_data: common.RequestProvider,
) -> Group:
    assert (
        request_data.json_body is not None
    ), "JSON body cannot be None for post groups"
    new_id = uuid.uuid1()

    creating_resource = dict(request_data.json_body)
    creating_resource["id"] = str(new_id)
    creating_resource["meta"] = ResourceMeta.create_meta(
        "Group", location=request_data.url_for_resource("get_group", new_id)
    ).to_dict()
    resource = validate_group(validator, creating_resource)

    store.create(resource)

    new_group = store.get_by_id(resource.id)
    scim_server.handle_resource_change("add", new_group)

    return new_group


def handle_get_group(
    group_store: Store[Group],
    request_data: common.RequestProvider,
) -> Mapping:
    assert (
        request_data.args.resource_id is not None
    ), "Resource ID cannot be None for get group"
    group = group_store.get_by_id(request_data.args.resource_id)
    if request_data.args.attributes or request_data.args.excluded_attributes:
        return common.filter_resource(
            group.to_dict(),
            include=request_data.args.attributes,
            exclude=request_data.args.excluded_attributes,
        )
    return group.to_dict()


def handle_get_groups(store: Store[Group], request_provider: common.RequestProvider):
    # process input
    all_groups = store.get_all()

    if request_provider.args.filter:
        query_filter = PythonFilter.parse_filter_to_predicate(
            request_provider.args.filter
        )
        filtered = [group for group in all_groups if query_filter(group.to_dict())]
    else:
        filtered = list(all_groups)

    # generate response
    result = ListResponse.from_list(filtered).to_dict()

    # filter output
    if request_provider.args.attributes or request_provider.args.excluded_attributes:
        if "Resources" in result:
            modified_resources = [
                common.filter_resource(
                    f,
                    include=request_provider.args.attributes,
                    exclude=request_provider.args.excluded_attributes,
                )
                for f in result["Resources"]
            ]
            result["Resources"] = modified_resources

    return result


def handle_put_group(
    group_store: Store[Group],
    validator: ResourceValidator,
    scim_server: SCIMServer,
    request_data: common.RequestProvider,
) -> Group:
    assert (
        request_data.json_body is not None
    ), "JSON body must not be none for PUT group"
    group = validate_group(validator, request_data.json_body)
    if group.get_id() != request_data.args.resource_id:
        raise exceptions.ResourceIdentifierMismatch(
            "Resource ID specified in request didn't match ID in resource"
        )
    group_store.update(group)

    updated_group = group_store.get_by_id(group.get_id())
    scim_server.handle_resource_change("replace", updated_group)

    return updated_group


def handle_patch_group(
    group_store: Store[Group],
    validator: ResourceValidator,
    request_data: common.RequestProvider,
) -> Group:
    raise NotImplementedError("Patch is not yet supported on this server")
