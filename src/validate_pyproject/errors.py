from textwrap import dedent

from fastjsonschema import (
    JsonSchemaDefinitionException,
    JsonSchemaException,
    JsonSchemaValueException,
)

from .error_reporting import ValidationError


class URLMissingTool(RuntimeError):
    _DESC = """\
    The '--tool' option requires a tool name.

    Correct form is '--tool <tool-name>={url}', with an optional
    '#json/pointer' at the end.
    """
    __doc__ = _DESC

    def __init__(self, url: str):
        msg = dedent(self._DESC).strip()
        msg = msg.format(url=url)
        super().__init__(msg)


class InvalidSchemaVersion(JsonSchemaDefinitionException):
    _DESC = """\
    All schemas used in the validator should be specified using the same version \
    as the toplevel schema ({version!r}).

    Schema for {name!r} has version {given!r}.
    """
    __doc__ = _DESC

    def __init__(self, name: str, given_version: str, required_version: str):
        msg = dedent(self._DESC).strip()
        msg = msg.format(name=name, version=required_version, given=given_version)
        super().__init__(msg)


class SchemaMissingId(JsonSchemaDefinitionException):
    _DESC = """\
    All schemas used in the validator MUST define a unique toplevel `"$id"`.
    No `"$id"` was found for schema associated with {reference!r}.
    """
    __doc__ = _DESC

    def __init__(self, reference: str):
        msg = dedent(self._DESC).strip()
        super().__init__(msg.format(reference=reference))


class SchemaWithDuplicatedId(JsonSchemaDefinitionException):
    _DESC = """\
    All schemas used in the validator MUST define a unique toplevel `"$id"`.
    `$id = {schema_id!r}` was found at least twice.
    """
    __doc__ = _DESC

    def __init__(self, schema_id: str):
        msg = dedent(self._DESC).strip()
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
