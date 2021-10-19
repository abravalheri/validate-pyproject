"""The purpose of this module is implement PEP 621 validations that are
difficult to express as a JSON Schema (or that are not supported by the current
JSON Schema library).
"""

from typing import Mapping, TypeVar

from fastjsonschema import JsonSchemaValueException

T = TypeVar("T", bound=Mapping)


class MissingStaticOrDynamic(JsonSchemaValueException):
    """According to PEP 621:

        If the core metadata specification lists a field as "Required", then
        the metadata MUST specify the field statically or list it in dynamic

    In turn, `core metadata`_ defines:

        The required fields are: Metadata-Version, Name, Version.
        All the other fields are optional.

    Since ``Metadata-Version`` is defined by the build back-end, ``name`` and
    ``version`` are the only mandatory information in ``pyproject.toml``.

    .. _core metadata: https://packaging.python.org/specifications/core-metadata/
    """


class RedefiningStaticFieldAsDynamic(JsonSchemaValueException):
    """According to PEP 621:

    Build back-ends MUST raise an error if the metadata specifies a field
    statically as well as being listed in dynamic.
    """


def validate_project_dynamic(pyproject: T) -> T:
    project_table = pyproject.get("project", {})
    dynamic = project_table.get("dynamic", [])
    # we need to ensure `version` (`name` is already mandatory in the JSON Schema)
    if "version" not in pyproject and "version" not in dynamic:
        msg = "You need to provide a value for `version` or list it under `dynamic`"
        raise MissingStaticOrDynamic(msg, "data.project.version")

    for field in dynamic:
        if field in project_table:
            msg = f"You cannot provided a value for `{field}` and "
            msg += "list it under `dynamic` at the same time"
            raise RedefiningStaticFieldAsDynamic(msg, f"data.project.{field}")

    return pyproject


EXTRA_VALIDATIONS = (validate_project_dynamic,)
