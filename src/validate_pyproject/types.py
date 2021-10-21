import sys
from types import MappingProxyType
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
    try:
        from typing_extensions import Protocol
    except ImportError:
        # Since we don't really need Protocol as an implementation, just for type check,
        # we can use something else in its place in the case we are in an old version of
        # Python.
        from collections.abc import ABC as Protocol


class Plugin(Protocol):
    tool_name: str
    help_text: str
    format_validators: Mapping[str, FormatValidationFn] = MappingProxyType({})
    extra_validations: Sequence[ValidationFn] = ()

    @property
    def tool_schema(self) -> Schema:
        raise NotImplementedError
