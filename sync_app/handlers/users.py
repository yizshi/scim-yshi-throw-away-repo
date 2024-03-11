from quart import url_for
from sync_app.schema import ResourceValidator
from sync_app.scim.resource import ResourceMeta
from sync_app.server import SCIMServer
from sync_app.parsers.python_filter import (
    PythonFilter,
)
from sync_app.scim.user import User
from sync_app.scim.list_response import ListResponse
from sync_app.store import Store
from typing import Mapping, Optional, TypeAlias
from sync_app.handlers import common
from sync_app import exceptions
import uuid


def validate_user(validator: ResourceValidator, resource: Mapping) -> User:
    validation_result = validator.validate(resource)
    if validation_result.valid:
        return User.from_dict(resource)
    else:
        print(validation_result.errors)
        for error in validation_result.errors:
            if "is a required property" in error.message:
                raise exceptions.InvalidValue("Resource is missing a required value")
        raise exceptions.ResourceValidationError("Could not validate resource as user")


def handle_post_users(
    store: Store[User],
    validator: ResourceValidator,
    scim_server: SCIMServer,
    request_data: common.RequestProvider,
) -> User:
    assert (
        request_data.json_body is not None
    ), "JSON body must not be None for POST users"
    new_id = uuid.uuid1()

    creating_resource = dict(request_data.json_body)
    creating_resource["id"] = str(new_id)
    creating_resource["meta"] = ResourceMeta.create_meta(
        "User", location=request_data.url_for_resource("get_user", new_id)
    ).to_dict()
    resource = validate_user(validator, creating_resource)

    store.create(resource)

    new_user = store.get_by_id(resource.id)
    scim_server.handle_resource_change("add", new_user)

    return new_user


def handle_get_user(
    user_store: Store[User],
    request_data: common.RequestProvider,
) -> Mapping:
    assert (
        request_data.args.resource_id is not None
    ), "Resource ID must not be None for GET user"
    user = user_store.get_by_id(request_data.args.resource_id)

    # filter output
    if request_data.args.attributes or request_data.args.excluded_attributes:
        return common.filter_resource(
            user.to_dict(),
            include=request_data.args.attributes,
            exclude=request_data.args.excluded_attributes,
        )

    return user.to_dict()


def handle_get_users(
    user_store: Store[User],
    request_data: common.RequestProvider,
) -> Mapping:
    all_users = user_store.get_all()

    if request_data.args.filter:
        query_filter = PythonFilter.parse_filter_to_predicate(request_data.args.filter)
        filtered = [user for user in all_users if query_filter(user.to_dict())]
    else:
        filtered = list(all_users)

    result = ListResponse.from_list(filtered).to_dict()

    # filter output
    if request_data.args.attributes or request_data.args.excluded_attributes:
        if "Resources" in result:
            modified_resources = [
                common.filter_resource(
                    f,
                    include=request_data.args.attributes,
                    exclude=request_data.args.excluded_attributes,
                )
                for f in result["Resources"]
            ]
            result["Resources"] = modified_resources

    return result


def handle_put_user(
    user_store: Store[User],
    validator: ResourceValidator,
    scim_server: SCIMServer,
    request_data: common.RequestProvider,
) -> User:
    assert request_data.json_body is not None, "JSON body must not be None for PUT user"
    user = validate_user(validator, request_data.json_body)
    if user.get_id() != request_data.args.resource_id:
        raise exceptions.ResourceIdentifierMismatch(
            "Resource ID specified in request didn't match ID in resource"
        )
    user_store.update(user)

    updated_user = user_store.get_by_id(user.get_id())
    scim_server.handle_resource_change("replace", updated_user)

    return updated_user


def handle_patch_user(
    user_store: Store[User],
    validator: ResourceValidator,
    userId: str,
    resource: Mapping,
    scim_server: SCIMServer,
) -> User:
    raise NotImplementedError("Patch is not yet supported on this server")
