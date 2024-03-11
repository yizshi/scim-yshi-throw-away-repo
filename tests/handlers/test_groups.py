#!/usr/bin/env python
from sync_app.schema import ResourceValidator
import pytest
from sync_app.server import SCIMServer
from unittest import mock
from sync_app.handlers import groups
from sync_app import exceptions
from sync_app.handlers.common import RequestProvider
from sync_app.memory_store import MemoryStore, ObjectNotFound
from sync_app.schema import ValidatorResult
from sync_app.scim.group import Group, Member
from datetime import datetime
from uuid import uuid1


@pytest.fixture
def valid_group_resource():
    return {
        "id": str(uuid1()),
        "meta": {
            "resourceType": "Group",
            "created": str(datetime.now()),
            "lastModified": str(datetime.now()),
            "version": "1",
            "location": "http://example.com",
        },
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "test group",
        "members": [],
    }


@pytest.fixture
def populated_group_store(valid_group_resource):
    store = MemoryStore[Group]()
    store.create(Group.from_dict(valid_group_resource))

    group_two = dict(valid_group_resource)
    group_two.update({"id": str(uuid1()), "displayName": "two"})
    store.create(Group.from_dict(group_two))

    group_three = dict(valid_group_resource)
    group_three.update({"id": str(uuid1()), "displayName": "three"})
    store.create(Group.from_dict(group_three))

    return store


def test_handle_post_groups(valid_group_resource):
    validator = mock.MagicMock(spec=ResourceValidator)
    server = mock.MagicMock(spec=SCIMServer)
    group_store = MemoryStore[Group]()

    provider = mock.MagicMock(spec=RequestProvider)
    provider.json_body = valid_group_resource
    provider.url_for_resource.return_value = "http://example.com"

    new_group = groups.handle_post_groups(group_store, validator, server, provider)
    stored_group = group_store.get_by_id(new_group.id).to_dict()

    for i in ["displayName", "members"]:
        assert (
            stored_group[i] == valid_group_resource[i]
        ), "POSTed group must match retrieved group for basic attributes"

    assert (
        stored_group["meta"]["created"] != valid_group_resource["meta"]["created"]
    ), "Created must store the time the resource was created in that service"
    assert (
        stored_group["id"] != valid_group_resource["id"]
    ), "Created group must have an ID assigned by that service"


def test_handle_post_group_without_meta(valid_group_resource):
    validator = mock.MagicMock(spec=ResourceValidator)
    server = mock.MagicMock(spec=SCIMServer)
    group_store = MemoryStore[Group]()
    post_group_resource = valid_group_resource
    del post_group_resource["meta"]

    provider = mock.MagicMock(spec=RequestProvider)
    provider.json_body = post_group_resource
    provider.url_for_resource.return_value = "http://example.com"

    new_group = groups.handle_post_groups(group_store, validator, server, provider)
    stored_group = group_store.get_by_id(new_group.id).to_dict()

    del stored_group["id"]
    del valid_group_resource["id"]
    assert "meta" in stored_group


def test_handle_post_groups_failed_validation(valid_group_resource):
    validator = mock.MagicMock(spec=ResourceValidator)
    server = mock.MagicMock(spec=SCIMServer)
    validator.validate.return_value = ValidatorResult(valid=False, errors=[])
    group_store = MemoryStore[Group]()
    provider = mock.MagicMock(spec=RequestProvider)
    provider.json_body = valid_group_resource
    provider.url_for_resource.return_value = "http://example.com"

    with pytest.raises(exceptions.ResourceValidationError):
        groups.handle_post_groups(
            group_store,
            validator,
            server,
            provider,
        )


def test_handle_get_group(populated_group_store, valid_group_resource):
    result = groups.handle_get_group(
        populated_group_store,
        RequestProvider(args={"resource_id": valid_group_resource["id"]}),
    )
    assert result == valid_group_resource


def test_handle_get_missing_group(populated_group_store):
    with pytest.raises(exceptions.ResourceMissing):
        groups.handle_get_group(
            populated_group_store, RequestProvider(args={"resource_id": str(uuid1())})
        )


def test_handle_get_group_with_attribute_filter(
    populated_group_store, valid_group_resource
):
    result = groups.handle_get_group(
        populated_group_store,
        RequestProvider(
            args={
                "resource_id": valid_group_resource["id"],
                "attributes": "displayName",
            }
        ),
    )
    assert result["displayName"] == valid_group_resource["displayName"]
    assert result["id"] == valid_group_resource["id"]


def test_handle_get_group_with_exclusion_filter(
    populated_group_store, valid_group_resource
):
    result = groups.handle_get_group(
        populated_group_store,
        RequestProvider(
            args={
                "resource_id": valid_group_resource["id"],
                "excludedAttributes": "meta.version",
            }
        ),
    )
    assert result["displayName"] == valid_group_resource["displayName"]
    assert "version" not in result["meta"]


def test_handle_get_groups_with_filter(populated_group_store):
    group_list = groups.handle_get_groups(
        populated_group_store,
        RequestProvider(args={"filter": 'displayName eq "test group"'}),
    )
    assert len(group_list["Resources"]) == 1


def test_handle_get_groups_with_filter_multiple(populated_group_store):
    group_list = groups.handle_get_groups(
        populated_group_store,
        RequestProvider(args={"filter": 'meta.resourceType eq "Group"'}),
    )
    assert len(group_list["Resources"]) == 3


def test_handle_put_group(populated_group_store, valid_group_resource):
    validator = mock.MagicMock(spec=ResourceValidator)
    server = mock.MagicMock(spec=SCIMServer)
    valid_group_resource.update({"displayName": "different name"})
    updated_group = groups.handle_put_group(
        populated_group_store,
        validator,
        server,
        RequestProvider(
            args={
                "resource_id": valid_group_resource["id"],
            },
            json_body=valid_group_resource,
        ),
    )
    assert updated_group.displayName == "different name"


def test_handle_put_group_missing(populated_group_store, valid_group_resource):
    validator = mock.MagicMock(spec=ResourceValidator)
    server = mock.MagicMock(spec=SCIMServer)
    with pytest.raises(exceptions.ResourceIdentifierMismatch):
        groups.handle_put_group(
            populated_group_store,
            validator,
            server,
            RequestProvider(
                args={
                    "resource_id": str(uuid1()),
                },
                json_body=valid_group_resource,
            ),
        )


def test_handle_get_groups_with_attribute_filter(populated_group_store):
    group_list = groups.handle_get_groups(
        populated_group_store,
        RequestProvider(
            args={"filter": 'displayName eq "test group"', "attributes": "displayName"}
        ),
    )
    first_result = group_list["Resources"][0]
    assert "displayName" in first_result
    assert not "meta" in first_result


def test_handle_get_groups_with_exclusion_filter(populated_group_store):
    group_list = groups.handle_get_groups(
        populated_group_store,
        RequestProvider(
            args={
                "filter": 'displayName eq "test group"',
                "excludedAttributes": "displayName",
            }
        ),
    )
    first_result = group_list["Resources"][0]
    assert not "displayName" in first_result
    assert "meta" in first_result


def test_handle_get_groups_with_no_results_filter(populated_group_store):
    group_list = groups.handle_get_groups(
        populated_group_store,
        RequestProvider(
            args={
                "filter": 'displayName eq "doesnt exist"',
                "excludedAttributes": "displayName",
            }
        ),
    )
    assert not "Resources" in group_list
