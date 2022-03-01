import io
import re
from numbers import Number
from textwrap import indent
from typing import Union, List, Optional, Callable

from ._vendor.fastjsonschema import JsonSchemaValueException


def format_error(ex: JsonSchemaValueException) -> str:
    name = f"`{ex.name.replace('data.','')}`"
    header = ex.message.replace(ex.name, name)


class _ErrorProcessor:
    HANDLING = {
        "propertyName": dict(
            replacements={"by propertyName definition": "according to the following"},
        ),
        "contains definition": dict(
            replacements={
                "one of contains definition": "at least one item that matches the following"
            },
        ),
        "const definition": dict(
            replacements={"same as const definition:": ""}, skip_details=True
        ),
        "only specified items": dict(
            replacements={
                "only specified items": "only items matching the following definition"
            },
        ),
    }

    SKIP_DETAILS = {
        "type",
        "minimum",
        "maximum",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "maxItems",
        "minItems",
    }
    # Easy rules, with comprehensive error messages, that don't need schema summaries

    def __init__(self, formatter: "Formatter"):
        self.formatter = formatter

    def __call__(self, ex):
        msg = ex.message

        if ex.rule in self.SKIP_DETAILS:
            return msg

        for guard, handling in self.ERROR_HANDLERS.items():
            if guard in msg:
                return self._process_error_message(handling, msg, ex.definition)

        return msg

    def _process_error_message(self, handling: dict, msg: str, definition: dict) -> str:
        for bad, repl in handling.get("replacements", {}).items():
            msg = msg.replace(bad, repl)

        if handling.get("skip_details"):
            return f"{msg}\n"

        return f"{msg}:\n\n{self.formatter.details(definition)}"


class _Formatter:
    def __call__(self, definition: dict) -> str:
        if "properties" in definition and "type" not in definition:
            definition["type"] = "object"
        if "enum" in definition:
            return f"one of: {definition['enum']!r}\n"
        if "const" in definition:
            return f"specifically: {definition['const']!r}\n"
        if "type" in definition:
            return self._format_type(definition)

    def _format_type(self, definition: dict) -> str:
        type_ = definition["type"]
        custom_format: Optional[Callable[[dict], str]] = getattr(
            self, f"_format_{type_}", None
        )
        if custom_format:
            return custom_format(definition)
        attrs = _format_attrs(definition)
        suffix = f" ({', '.join(attrs)})" if attrs else ""
        return f"a {type_} value{suffix}\n"

    def _format_object(self, definition):
        pass

    def _format_array(self, definition: dict) -> str:
        with io.StringIO() as buffer:
            spec = definition.copy()
            items: List[dict] = spec.pop("prefixItems", [])
            general_item: Union[bool, dict] = spec.pop("items", {})
            contains: Optional[dict] = spec.pop("contains", None)

            prefix = "  * "
            buffer.write(f"an array (list)\n")
            if items:
                buffer.write("- with the following items:\n")
                buffer.write("".join(self.details(i, prefix) for i in items))
                if general_item is False:
                    buffer.write("- no extra item\n")
            if general_item:
                buffer.write("- with any items in the form of:\n")
                buffer.write(self.details(general_item, prefix))
            if contains:
                buffer.write("- with at least one item in the form of:\n")
                buffer.write(self.details(contains, prefix))

            attrs = "\n".join(_format_attrs(spec))
            if attrs:
                buffer.write(indent(attrs + "\n", "- "))

            return buffer.getvalue()


    def details(self, definition: dict, prefix="  - ") -> str:
        L = len(prefix)
        rest = indent(self(definition), L * " ")
        return prefix + rest[L:]


CAMEL_CASE_SPLITTER = re.compile(r"\W+|([A-Z][^A-Z\W]*)")


def _format_attr(word: str) -> str:
    """
    >>> _format_attr("FooBar-foo")
    "foo bar foo"
    """
    return " ".join(w for w in CAMEL_CASE_SPLITTER.split(word) if w).lower()


def _format_attrs(definition: dict) -> List[str]:
    """
    >>> list(_format_attrs({"minItems": 2, "maxItems": 3, "unique Items": true}))
    ["min items: 2", "max items: 3", "unique items": true"]
    >>> list(_format_attrs({"pattern": "a*"}))
    ["pattern": "'a*'"]
    """
    return [f"{_format_attr(k)}: {v!r}" for k, v in definition.items() if k != "type"]
