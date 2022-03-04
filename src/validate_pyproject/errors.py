from textwrap import dedent

from ._vendor.fastjsonschema import (
    JsonSchemaDefinitionException,
    JsonSchemaException,
    JsonSchemaValueException,
)
from .error_reporting import ValidationError


class InvalidSchemaVersion(JsonSchemaDefinitionException):
    """\
    All schemas used in the validator should be specified using the same version \
    as the toplevel schema ({version!r}).

    Schema for {name!r} has version {given!r}.
    """

    def __init__(self, name: str, given_version: str, required_version: str):
        msg = dedent(self.__doc__ or "").strip()
        msg = msg.format(name=name, version=required_version, given=given_version)
        super().__init__(msg)


class SchemaMissingId(JsonSchemaDefinitionException):
    """\
    All schemas used in the validator MUST define a unique toplevel `"$id"`.
    No `"$id"` was found for schema associated with {reference!r}.
    """

    def __init__(self, reference: str):
        msg = dedent(self.__doc__ or "").strip()
        super().__init__(msg.format(reference=reference))


class SchemaWithDuplicatedId(JsonSchemaDefinitionException):
    """\
    All schemas used in the validator MUST define a unique toplevel `"$id"`.
    `$id = {schema_id!r}` was found at least twice.
    """

    def __init__(self, schema_id: str):
        msg = dedent(self.__doc__ or "").strip()
        super().__init__(msg.format(schema_id=schema_id))


__all__ = [
    "InvalidSchemaVersion",
    "JsonSchemaDefinitionException",
    "JsonSchemaException",
    "JsonSchemaValueException",
    "SchemaMissingId",
    "SchemaWithDuplicatedId",
    "ValidationError",
]
