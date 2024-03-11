#!/usr/bin/env python

import traceback
from quart import (
    Quart,
    request,
    jsonify,
)
from quart.typing import ResponseValue
import os
import toml
from sync_app.schema import ResourceValidator
from sync_app.scim.user import User
from sync_app.scim.group import Group
from sync_app.handlers import users, groups, common
from sync_app import exceptions
from sync_app.memory_store import MemoryStore, ObjectAlreadyInStore, ObjectNotFound
from sync_app.server import ServerConfiguration, SCIMServer
from typing import Mapping, Tuple

app = Quart(__name__)
config = toml.load(os.path.join(os.path.dirname(__file__), "..", "configuration.toml"))
validator = ResourceValidator.load(
    [
        os.path.join(os.path.dirname(__file__), "..", "schemas", f)
        for f in [
            "common.schema.json",
            "enterpriseUser.schema.json",
            "group.schema.json",
            "patch.schema.json",
            "resourceType.schema.json",
            "schemas.schema.json",
            "serviceProviderConfig.schema.json",
            "user.schema.json",
        ]
    ]
)
user_store = MemoryStore[User]()
group_store = MemoryStore[Group]()
scim_server = SCIMServer(
    ServerConfiguration(config["outbound_server_url"], config["auth_token"])
)

# TODO add Location handling


def handle_exceptions(e: Exception) -> Tuple[ResponseValue, int]:
    if isinstance(e, exceptions.SCIMException):
        new_exception = e
    else:
        new_exception = exceptions.UnknownSCIMException(e)

    traceback.print_exception(e)
    return jsonify(new_exception.to_dict()), new_exception.code


@app.route("/")
async def hello():
    return jsonify({"hello": "world"})


@app.route("/scim/v2/Users", methods=["GET"])
async def get_users() -> Tuple[ResponseValue, int]:
    try:
        request_provider = common.RequestProvider(request.view_args, request.args)
        list_response = users.handle_get_users(user_store, request_provider)
        return jsonify(list_response), 200
    except Exception as e:
        return handle_exceptions(e)


@app.route("/scim/v2/Users", methods=["POST"])
async def post_users() -> Tuple[ResponseValue, int]:
    json_data = await request.get_json(force=True)

    request_provider = common.RequestProvider(
        request.view_args, request.args, json_data
    )
    try:
        new_user = users.handle_post_users(
            user_store, validator, scim_server, request_provider
        )
        return jsonify(new_user.to_dict()), 201
    except Exception as e:
        return handle_exceptions(e)


@app.route("/scim/v2/Users/<resource_id>", methods=["PATCH"])
async def patch_user(resource_id) -> Tuple[ResponseValue, int]:
    request_data: Mapping = await request.get_json(force=True)
    try:
        patched_resource = users.handle_patch_user(
            user_store, validator, resource_id, request_data, scim_server
        )
        return jsonify(patched_resource), 200
    except Exception as e:
        return handle_exceptions(e)


@app.route("/scim/v2/Users/<resource_id>", methods=["GET"])
def get_user(resource_id) -> Tuple[ResponseValue, int]:
    try:
        user = users.handle_get_user(
            user_store, common.RequestProvider(request.view_args, request.args)
        )
        return jsonify(user), 200
    except Exception as e:
        return handle_exceptions(e)


@app.route("/scim/v2/Users/<resource_id>", methods=["PUT"])
async def put_user(resource_id) -> Tuple[ResponseValue, int]:
    json_data: Mapping = await request.get_json(force=True)
    try:
        request_provider = common.RequestProvider(
            request.view_args, request.args, json_data
        )
        user = users.handle_put_user(
            user_store, validator, scim_server, request_provider
        )
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return handle_exceptions(e)


@app.route("/scim/v2/Groups", methods=["GET"])
async def get_groups() -> Tuple[ResponseValue, int]:
    try:
        request_provider = common.RequestProvider(request.view_args, request.args)
        list_response = groups.handle_get_groups(group_store, request_provider)
        return jsonify(list_response), 200
    except Exception as e:
        return handle_exceptions(e)


@app.route("/scim/v2/Groups", methods=["POST"])
async def post_groups() -> Tuple[ResponseValue, int]:
    # TODO handle .search?
    request_data: Mapping = await request.get_json(force=True)
    try:
        request_provider = common.RequestProvider(
            request.view_args, request.args, request_data
        )
        new_group = groups.handle_post_groups(
            group_store, validator, scim_server, request_provider
        )
        return jsonify(new_group.to_dict()), 201
    except Exception as e:
        return handle_exceptions(e)


@app.route("/scim/v2/Groups/<resource_id>", methods=["PATCH"])
async def patch_group(resource_id) -> Tuple[ResponseValue, int]:
    request_data: Mapping = await request.get_json(force=True)
    try:
        request_provider = common.RequestProvider(
            request.view_args, request.args, request_data
        )
        patched_resource = groups.handle_patch_group(
            group_store, validator, request_provider
        )
        return jsonify(patched_resource), 200
    except Exception as e:
        return handle_exceptions(e)


@app.route("/scim/v2/Groups/<resource_id>", methods=["GET"])
def get_group(resource_id) -> Tuple[ResponseValue, int]:
    try:
        request_provider = common.RequestProvider(request.view_args, request.args)
        resource = groups.handle_get_group(group_store, request_provider)
        return jsonify(resource), 200
    except Exception as e:
        return handle_exceptions(e)


@app.route("/scim/v2/Groups/<resource_id>", methods=["PUT"])
async def put_group(resource_id):
    request_data: Mapping = await request.get_json(force=True)
    try:
        request_provider = common.RequestProvider(request.view_args, request.args)
        group = groups.handle_put_group(
            group_store, validator, scim_server, request_provider
        )
        return jsonify(group.to_dict()), 200
    except Exception as e:
        return handle_exceptions(e)


if __name__ == "__main__":
    app.run()
