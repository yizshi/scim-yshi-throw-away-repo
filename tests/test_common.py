from sync_app.schema import ResourceValidator
from sync_app.parsers.python_filter import (
    PythonFilter,
)
from sync_app.handlers.common import filter_resource
from sync_app.scim.list_response import ListResponse
from sync_app.store import Store
from typing import Mapping, Optional
from dataclasses import dataclass
from sync_app import exceptions
import pytest
import uuid


@pytest.fixture
def basic_resource():
    return {
        "id": "someid",
        "schemas": ["fakeschema"],
        "userName": "foo",
        "height": 5,
        "name": {
            "first": "foo",
            "last": "bar",
        },
    }


def test_filter_include_resource_basic(basic_resource):
    result = filter_resource(basic_resource, include=[["name"]])
    assert result == {
        "id": basic_resource["id"],
        "schemas": basic_resource["schemas"],
        "name": basic_resource["name"],
    }


def test_filter_include_resource_subattribute_path(basic_resource):
    result = filter_resource(basic_resource, include=[["name", "last"]])
    assert result == {
        "id": basic_resource["id"],
        "schemas": basic_resource["schemas"],
        "name": {"last": basic_resource["name"]["last"]},
    }


def test_filter_include_resource_subattribute_path_multiple(basic_resource):
    result = filter_resource(
        basic_resource, include=[["name", "last"], ["name", "first"], ["userName"]]
    )
    assert result == {
        "id": basic_resource["id"],
        "schemas": basic_resource["schemas"],
        "userName": basic_resource["userName"],
        "name": basic_resource["name"],
    }


def test_filter_exclude_resource_basic(basic_resource):
    result = filter_resource(basic_resource, exclude=[["name"]])
    assert result == {
        "id": basic_resource["id"],
        "schemas": basic_resource["schemas"],
        "userName": basic_resource["userName"],
        "height": basic_resource["height"],
    }


def test_filter_exclude_resource_subattribute_path(basic_resource):
    result = filter_resource(basic_resource, exclude=[["name", "last"]])
    assert result == {
        "id": basic_resource["id"],
        "schemas": basic_resource["schemas"],
        "userName": basic_resource["userName"],
        "height": basic_resource["height"],
        "name": {"first": basic_resource["name"]["first"]},
    }


def test_filter_exclude_resource_subattribute_path_multiple(basic_resource):
    result = filter_resource(
        basic_resource, exclude=[["name", "last"], ["name", "first"], ["userName"]]
    )
    assert result == {
        "id": basic_resource["id"],
        "schemas": basic_resource["schemas"],
        "height": basic_resource["height"],
    }


def test_filter_exclude_required(basic_resource):
    result = filter_resource(basic_resource, exclude=[["id"], ["schemas"]])
    assert result == basic_resource
