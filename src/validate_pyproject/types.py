import sys
from typing import Callable, Mapping, NewType, Sequence, TypeVar

T = TypeVar("T", bound=Mapping)
Schema = NewType("Schema", dict)
ValidationFn = Callable[[T], T]
"""Custom validation function.
It should receive as input a mapping corresponding to the whole
``pyproject.toml`` file and raise a :exc:`fastjsonschema.JsonSchemaValueException`
if it is not valid.
"""
FormatValidationFn = Callable[[str], bool]
"""Should return ``True`` when the input string satisfies the format"""


if sys.version_info[:2] >= (3, 7):  # pragma: no cover
    from typing import Protocol
else:  # pragma: no cover
    from collections.abc import ABC as Protocol


class Plugin(Protocol):
    tool_name: str
    help_text: str
    format_validators: Sequence[FormatValidationFn] = ()
    extra_validations: Sequence[ValidationFn] = ()

    @property
    def tool_schema(self) -> Schema:
        raise NotImplementedError
