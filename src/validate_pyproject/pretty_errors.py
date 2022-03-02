import io
import re
from itertools import chain
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
    def __call__(self, definition: dict, *, _neg=False) -> str:
        if "enum" in definition:
            return f"one of {definition['enum']!r}\n"
        if "const" in definition:
            return f"specifically {definition['const']!r}\n"

        if "not" in definition and definition["not"]:
            return self._format_not(definition["not"])

        for rule in ("anyOf", "oneOf", "allOf"):
            if rule in definition and definition[rule]:
                return self._format_composition(rule, definition[rule], _neg)

        if "properties" in definition and "type" not in definition:
            definition["type"] = "object"
        if "pattern" in definition and "type" not in definition:
            definition["type"] = "string"

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

    def _format_not(self, definition: dict) -> str:
        prefix = "  - "
        if any(rule in definition for rule in ("anyOf", "oneOf", "allOf")):
            return self(definition, _neg=True)

        child = self.details(definition, prefix)
        return f"a value that does **NOT** match the following:\n{child}"

    def _format_composition(self, rule: str, definitions: List[dict], neg=False) -> str:
        expr = {
            "anyOf": "any (one or more)",
            "oneOf": "exactly one",
            "allOf": "all",
        }

        prefix = "  - "
        pred = "does NOT match" if neg else "matches"
        children = "".join(self.details(k, prefix) for k in definitions)
        return f"a value that {pred} {expr[rule]} of the following:\n{children}"

    def _format_object(self, definition):
        with io.StringIO() as buffer:
            spec = definition.copy()
            property_names = spec.pop("propertyNames", {})
            pattern_properties = spec.pop("patternProperties", {})
            properties: dict = {
                **{f"`{k}`": v for k, v in spec.pop("properties", {}).items()},
                **{f"/{k}/ (pattern)": v for k, v in pattern_properties.items()},
            }
            required: List[str] = spec.pop("required", [])

            prefix = "    * "
            buffer.write("a table (dict)\n")
            if properties:
                buffer.write("  - with the following fields:\n")
                children = (self.details(v, prefix, k) for k, v in properties.items())
                buffer.write("".join(children))
            if property_names:
                buffer.write("  - with any fields in the form of:\n")
                buffer.write(self.details(property_names, prefix))
            if spec.pop("additionalProperties", True) is False:
                buffer.write("  - no extra fields\n")
            elif properties or property_names:
                buffer.write("  - extra fields are allowed\n")
            if required:
                buffer.write(f"  - required fields: {required!r}\n")

            attrs = "\n".join(_format_attrs(spec)).replace("properties", "fields")
            if attrs:
                buffer.write(indent(attrs + "\n", "  - "))

            return _add_colon(buffer.getvalue())

    def _format_array(self, definition: dict) -> str:
        with io.StringIO() as buffer:
            spec = definition.copy()
            items: List[dict] = spec.pop("prefixItems", [])
            general_item: Union[bool, dict] = spec.pop("items", {})
            contains: Optional[dict] = spec.pop("contains", None)

            prefix = "    * "
            buffer.write(f"an array (list)\n")
            if items:
                buffer.write("  - with the following items:\n")
                buffer.write("".join(self.details(i, prefix) for i in items))
                if general_item is False:
                    buffer.write("  - no extra item\n")
            if general_item:
                buffer.write("  - with any items in the form of:\n")
                buffer.write(self.details(general_item, prefix))
            if contains:
                buffer.write("  - with at least one item in the form of:\n")
                buffer.write(self.details(contains, prefix))

            attrs = "\n".join(_format_attrs(spec))
            if attrs:
                buffer.write(indent(attrs + "\n", "  - "))

            return _add_colon(buffer.getvalue())

    def details(self, definition: dict, prefix="  - ", name: str = "") -> str:
        L = len(prefix)
        rest = indent(self(definition), L * " ")
        return prefix + (f"{name}: " if name else "") + rest[L:]


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


def _add_colon(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if len(lines) <= 1:
        return text
    header = lines[0].strip()
    changed = lines[0].replace(header, f"{header.rstrip(':')}:")
    return "".join(chain((changed,), lines[1:]))
