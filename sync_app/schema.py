#!/usr/bin/env python
import json
import jsonschema
from typing import Iterable, OrderedDict, Optional, TypeAlias, Mapping, List, TypeVar
from dataclasses import dataclass
from sync_app.scim.resource import Resource

COMMON_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Common"


class JSONSchema:
    schema: Mapping
    id: str

    @staticmethod
    def load(path: str, schemaValidator: Optional["JSONSchema"] = None) -> "JSONSchema":
        with open(path, "r") as fh:
            return JSONSchema(json.load(fh), schemaValidator)

    def __init__(self, schema: Mapping, schemaValidator: Optional["JSONSchema"] = None):
        assert "$id" in schema, "All schemas must have a $id entry for identification"
        assert (
            "$schema" in schema
        ), "All schemas must have a validating schema in $schema"

        if schemaValidator:
            schemaValidator.validate(schema)

        self.schema = schema
        self.id = schema["$id"]
        self.validatingSchema = schema["$schema"]

    def validate(self, instance: Mapping) -> bool:
        jsonschema.validate(instance, self.schema)
        # No exception means the schema is valid
        return True


IdToSchema: TypeAlias = Mapping[str, JSONSchema]


class SchemaNotFoundInValidator(Exception):
    pass


class ResourceMissingSchemas(Exception):
    pass


@dataclass
class ValidatorResult:
    valid: bool
    errors: Iterable[jsonschema.ValidationError]


class ResourceValidator:
    schemas: IdToSchema

    @staticmethod
    def load(paths: Iterable[str]) -> "ResourceValidator":
        schemas = []
        for path in paths:
            with open(path, "r") as fh:
                schemas.append(JSONSchema(json.load(fh)))

        return ResourceValidator(schemas)

    def __init__(self, schemas: Iterable[JSONSchema]):
        self.schemas = {schema.id: schema for schema in schemas}
        self.validate_schemas()

    def validate_schemas(self) -> ValidatorResult:
        errors: List[jsonschema.ValidationError] = []
        for schema in self.schemas.values():
            validating_schema = schema.validatingSchema
            if validating_schema not in self.schemas:
                raise SchemaNotFoundInValidator(
                    "While processing schema could not find this validating schema: {schema}".format(
                        schema=schema.validatingSchema
                    )
                )
            else:
                try:
                    self.schemas[validating_schema].validate(schema.schema)
                except jsonschema.ValidationError as e:
                    errors.append(e)

        return ValidatorResult(len(errors) == 0, errors)

    def validate(self, resource: Mapping) -> ValidatorResult:
        errors: List[jsonschema.ValidationError] = []

        if "schemas" not in resource:
            raise ResourceMissingSchemas()

        schemas_to_check = resource["schemas"]

        if COMMON_SCHEMA in self.schemas:
            # The common schema is always added if it's present in the validator
            schemas_to_check = schemas_to_check + [COMMON_SCHEMA]

        for schemaId in schemas_to_check:
            schema_to_check = self.schemas.get(schemaId, None)
            if schema_to_check is None:
                raise SchemaNotFoundInValidator(
                    "While processing {meta!r}".format(meta=resource["meta"])
                )
            try:
                schema_to_check.validate(resource)
            except jsonschema.ValidationError as e:
                errors.append(e)

        return ValidatorResult(len(errors) == 0, errors)
