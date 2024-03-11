#!/usr/bin/env python
from sync_app.schema import ResourceValidator
from sync_app.server import SCIMServer
import pytest
from unittest import mock
from sync_app.handlers import users
from sync_app import exceptions
from sync_app.handlers.common import RequestProvider
from sync_app.memory_store import MemoryStore, ObjectNotFound
from sync_app.schema import ValidatorResult
from sync_app.scim.user import User, Name
from datetime import datetime
import uuid


@pytest.fixture
def valid_user_resource():
    return {
        "id": str(uuid.uuid1()),
        "meta": {
            "resourceType": "User",
            "created": datetime.now(),
            "lastModified": datetime.now(),
            "version": "1",
            "location": "http://example.com",
        },
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "displayName": "test",
        "active": True,
        "userName": "foo",
        "name": {
            "formatted": "test",
            "familyName": "example",
            "givenName": "test",
        },
        "emails": [],
    }


@pytest.fixture
def populated_user_store(valid_user_resource):
    store = MemoryStore[User]()
    store.create(User.from_dict(valid_user_resource))

    user_two = dict(valid_user_resource)
    user_two.update({"id": str(uuid.uuid1()), "userName": "two"})
    store.create(User.from_dict(user_two))

    user_three = dict(valid_user_resource)
    user_three.update({"id": str(uuid.uuid1()), "userName": "three"})
    store.create(User.from_dict(user_three))

    return store


def test_handle_post_users(valid_user_resource):
    validator = mock.MagicMock(spec=ResourceValidator)
    server = mock.MagicMock(spec=SCIMServer)
    provider = mock.MagicMock(spec=RequestProvider)
    provider.json_body = valid_user_resource
    provider.url_for_resource.return_value = "http://example.com"
    user_store = MemoryStore[User]()
    new_user = users.handle_post_users(user_store, validator, server, provider)
    stored_user = user_store.get_by_id(new_user.id).to_dict()

    for i in ["displayName", "name", "userName", "active"]:
        assert (
            stored_user[i] == valid_user_resource[i]
        ), "POSTed user must match retrieved user for basic attributes"

    assert (
        stored_user["meta"]["created"] != valid_user_resource["meta"]["created"]
    ), "Created must store the time the resource was created in that service"
    assert (
        stored_user["id"] != valid_user_resource["id"]
    ), "Created user must have an ID assigned by that service"


def test_handle_post_users_failed_validation(valid_user_resource):
    validator = mock.MagicMock(spec=ResourceValidator)
    server = mock.MagicMock(spec=SCIMServer)
    provider = mock.MagicMock(spec=RequestProvider)
    provider.json_body = valid_user_resource
    provider.url_for_resource.return_value = "http://example.com"
    validator.validate.return_value = ValidatorResult(valid=False, errors=[])
    user_store = MemoryStore[User]()

    with pytest.raises(exceptions.ResourceValidationError):
        users.handle_post_users(
            user_store,
            validator,
            server,
            provider,
        )


def test_handle_get_user(populated_user_store, valid_user_resource):
    result = users.handle_get_user(
        populated_user_store,
        RequestProvider(args={"resource_id": valid_user_resource["id"]}),
    )
    assert result == valid_user_resource


def test_handle_get_missing_user(populated_user_store, valid_user_resource):
    with pytest.raises(exceptions.ResourceMissing):
        users.handle_get_user(
            populated_user_store,
            RequestProvider(
                args={
                    "resource_id": str(uuid.uuid1()),
                }
            ),
        )


def test_handle_get_user_with_attribute_filter(
    populated_user_store, valid_user_resource
):
    result = users.handle_get_user(
        populated_user_store,
        RequestProvider(
            args={"resource_id": valid_user_resource["id"], "attributes": "displayName"}
        ),
    )
    assert result["displayName"] == valid_user_resource["displayName"]
    assert result["id"] == valid_user_resource["id"]


def test_handle_get_user_with_exclusion_filter(
    populated_user_store, valid_user_resource
):
    result = users.handle_get_user(
        populated_user_store,
        RequestProvider(
            args={
                "resource_id": valid_user_resource["id"],
                "excludedAttributes": "name.givenName",
            }
        ),
    )
    assert result["displayName"] == valid_user_resource["displayName"]
    assert "givenName" not in result["name"]


def test_handle_get_users_with_filter(populated_user_store):
    user_list = users.handle_get_users(
        populated_user_store, RequestProvider(args={"filter": 'userName eq "foo"'})
    )
    assert len(user_list["Resources"]) == 1


def test_handle_get_users_with_attribute_filter(populated_user_store):
    user_list = users.handle_get_users(
        populated_user_store,
        RequestProvider(
            args={"filter": 'userName eq "foo"', "attributes": "displayName"}
        ),
    )
    first_result = user_list["Resources"][0]
    assert "displayName" in first_result
    assert not "userName" in first_result


def test_handle_get_users_with_exclusion_filter(populated_user_store):
    user_list = users.handle_get_users(
        populated_user_store,
        RequestProvider(
            args={"filter": 'userName eq "foo"', "excludedAttributes": "displayName"}
        ),
    )
    first_result = user_list["Resources"][0]
    assert not "displayName" in first_result
    assert "userName" in first_result
    assert "active" in first_result
    assert "name" in first_result


def test_handle_get_users_with_filter_multiple(populated_user_store):
    user_list = users.handle_get_users(
        populated_user_store,
        RequestProvider(args={"filter": 'meta.resourceType eq "User"'}),
    )
    assert len(user_list["Resources"]) == 3


def test_handle_put_user(populated_user_store, valid_user_resource):
    validator = mock.MagicMock(spec=ResourceValidator)
    server = mock.MagicMock(spec=SCIMServer)
    valid_user_resource.update({"displayName": "different name"})
    updated_user = users.handle_put_user(
        populated_user_store,
        validator,
        server,
        RequestProvider(
            args={
                "resource_id": valid_user_resource["id"],
            },
            json_body=valid_user_resource,
        ),
    )
    assert updated_user.displayName == "different name"


def test_handle_put_user_missing(populated_user_store, valid_user_resource):
    validator = mock.MagicMock(spec=ResourceValidator)
    server = mock.MagicMock(spec=SCIMServer)
    with pytest.raises(exceptions.ResourceIdentifierMismatch):
        users.handle_put_user(
            populated_user_store,
            validator,
            server,
            RequestProvider(
                args={"resource_id": str(uuid.uuid1())},
                json_body=valid_user_resource,
            ),
        )


def test_handle_get_users_with_no_results_filter(populated_user_store):
    user_list = users.handle_get_users(
        populated_user_store,
        RequestProvider(
            args={
                "filter": 'displayName eq "doesnt exist"',
                "excludedAttributes": "displayName",
            }
        ),
    )
    assert not "Resources" in user_list
