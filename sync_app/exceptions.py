class ResourceValidationError(Exception):
    pass


class ResourceIdentifierMismatch(Exception):
    pass


class NoTarget(Exception):
    pass


class SCIMException(Exception):
    schema = "urn:ietf:params:scim:api:messages:2.0:Error"
    exception_type = "unknown"
    code = 500

    def to_dict(self):
        return {
            "scimType": self.exception_type,
            "schemas": [self.schema],
            "detail": repr(self),
        }


class TooManyResources(SCIMException):
    exception_type = "tooMany"
    code = 400


class InvalidValue(SCIMException):
    exception_type = "invalidValue"
    code = 400


class MutabilityError(Exception):
    pass


class InvalidOptions(Exception):
    pass


class InvalidQueryParameter(Exception):
    pass


class InvalidResourceID(SCIMException):
    exception_type = "invalidValue"
    code = 404


class InvalidSCIMFilter(SCIMException):
    exception_type = "invalidFilter"
    code = 400


class ResourceConflict(SCIMException):
    exception_type = "uniqueness"
    code = 409


class ResourceMissing(SCIMException):
    exception_type = "notFound"
    code = 404


class UnknownSCIMException(SCIMException):
    exception_type = "unknown"
    code = 500
