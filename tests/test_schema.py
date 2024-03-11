#!/usr/bin/env python
from sync_app import schema
import pytest
import jsonschema
import os
from types import MappingProxyType

COMMON_SCHEMA_FILENAME = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "common.schema.json"
)

USER_SCHEMA_FILENAME = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "user.schema.json"
)


SCHEMAS_SCHEMA_FILENAME = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "schemas.schema.json"
)

TEST_USER = dict(
    {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": "2819c223-7f76-453a-919d-413861904646",
        "userName": "bjensen@example.com",
        "meta": {
            "resourceType": "User",
            "created": "2010-01-23T04:56:22Z",
            "lastModified": "2011-05-13T04:42:34Z",
            "version": "",
            "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
        },
    }
)


def test_load():
    meta_schema = schema.JSONSchema.load(COMMON_SCHEMA_FILENAME)
    assert meta_schema.id == "urn:ietf:params:scim:schemas:core:2.0:Common"


def test_load_validated():
    schemas_schema = schema.JSONSchema.load(SCHEMAS_SCHEMA_FILENAME)
    meta_schema = schema.JSONSchema.load(COMMON_SCHEMA_FILENAME, schemas_schema)


def test_failed_validation():
    meta_schema = schema.JSONSchema.load(COMMON_SCHEMA_FILENAME)
    with pytest.raises(jsonschema.ValidationError):
        meta_schema.validate({})


def test_passed_validation():
    meta_schema = schema.JSONSchema.load(COMMON_SCHEMA_FILENAME)
    meta_schema.validate(TEST_USER)


def test_validator_load():
    schema.ResourceValidator.load([COMMON_SCHEMA_FILENAME, SCHEMAS_SCHEMA_FILENAME])


def test_validator_load_missing_validation_chain():
    with pytest.raises(schema.SchemaNotFoundInValidator):
        meta_schema = schema.ResourceValidator.load([COMMON_SCHEMA_FILENAME])


def test_validator_validate_user():
    validator = schema.ResourceValidator.load(
        [COMMON_SCHEMA_FILENAME, USER_SCHEMA_FILENAME, SCHEMAS_SCHEMA_FILENAME]
    )
    result = validator.validate(TEST_USER)
    assert result.valid


def test_validator_missing_required():
    validator = schema.ResourceValidator.load(
        [COMMON_SCHEMA_FILENAME, USER_SCHEMA_FILENAME, SCHEMAS_SCHEMA_FILENAME]
    )
    bad_user = dict(TEST_USER)
    del bad_user["id"]
    result = validator.validate(bad_user)
    assert result.valid == False


def test_validator_missing_schema():
    validator = schema.ResourceValidator.load(
        [COMMON_SCHEMA_FILENAME, USER_SCHEMA_FILENAME, SCHEMAS_SCHEMA_FILENAME]
    )
    user = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User", "extraschema"],
        "id": "2819c223-7f76-453a-919d-413861904646",
        "userName": "bjensen@example.com",
        "meta": TEST_USER["meta"],
    }
    with pytest.raises(schema.SchemaNotFoundInValidator):
        validator.validate(user)


def test_validator_common_schema_default():
    validator = schema.ResourceValidator.load(
        [COMMON_SCHEMA_FILENAME, USER_SCHEMA_FILENAME, SCHEMAS_SCHEMA_FILENAME]
    )
    user = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": "2819c223-7f76-453a-919d-413861904646",
        "userName": "bjensen@example.com",
        "meta": {},
    }
    result = validator.validate(user)
    assert any([isinstance(e, jsonschema.ValidationError) for e in result.errors])
