"""
Retrieve JSON schemas for validating dicts representing a ``pyproject.toml`` file.
"""
import json
import logging
import sys
from enum import Enum
from functools import reduce
from itertools import chain
from types import MappingProxyType
from typing import Dict, List, Mapping, Optional, Sequence, TypeVar, Union, cast

import fastjsonschema

from . import format
from .extra_validations import EXTRA_VALIDATIONS
from .types import FormatValidationFn, Plugin, Schema, ValidationFn

if sys.version_info[:2] >= (3, 7):  # pragma: no cover
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.7`
    from importlib.resources import read_text
else:  # pragma: no cover
    try:
        from pkgutil import get_data  # pragma: no cover
    except ImportError as ex:
        msg = "Please install `setuptools` or `importlib_metadata`"
        raise ImportError(msg) from ex

    # The following "polyfill" is taken from PyScaffold (licensed under MIT)
    # https://github.com/pyscaffold/pyscaffold/blob/master/LICENSE.txt
    # https://github.com/pyscaffold/pyscaffold/blob/609f548574618834e6056997aff411b43a24e3fb/src/pyscaffold/templates/__init__.py#L27

    def read_text(package, resource, encoding="utf-8") -> str:  # pragma: no cover
        data = get_data(package, resource)
        if data is None:
            raise FileNotFoundError(f"{resource!r} resource not found in {package!r}")
        return data.decode(encoding)


T = TypeVar("T", bound=Mapping)
AllPlugins = Enum("AllPlugins", "ALL_PLUGINS")
ALL_PLUGINS = AllPlugins.ALL_PLUGINS

TOP_LEVEL_SCHEMA_FILE = "pep517_518"
PROJECT_TABLE_SCHEMA_FILE = "pep621_project"

NOT_SAFE_FOR_EMBEDDING = ["$schema"]
"""JSON Schemas should be fairly compositional, however some fields are
expected to be present only in the top-level definition.
"""

FORMAT_FUNCTIONS: Mapping[str, FormatValidationFn] = MappingProxyType(
    {
        fn.__name__.replace("_", "-"): fn
        for fn in format.__dict__.values()
        if callable(fn)
    }
)

_logger = logging.getLogger(__name__)
_chain_iter = chain.from_iterable


def load(name: str, package: str = __package__, ext: str = ".schema.json") -> Schema:
    """Load the schema from a JSON Schema file"""
    return Schema(json.loads(read_text(__package__, f"{name}{ext}")))


def plugin_id(plugin: Plugin):
    return f"{plugin.__module__}.{plugin.__class__.__qualname__}"


def clean(schema: Schema) -> Schema:
    """Given a dict represeting a JSON Schema, make it suitable for being
    embeded inside the ``properties`` of another schema.
    """
    return Schema({k: v for k, v in schema.items() if k not in NOT_SAFE_FOR_EMBEDDING})


def combine(self, plugins: Sequence[Plugin] = ()) -> Schema:
    """Retrieve a schema that validates ``pyproject.toml`` by aggregating the
    standard schemas and the ones provided by plugins.
    """
    overall_schema = load(TOP_LEVEL_SCHEMA_FILE)
    project_table_schema = load(PROJECT_TABLE_SCHEMA_FILE)
    overall_properties = overall_schema["properties"]
    overall_properties["project"] = clean(project_table_schema)

    tool_properties = overall_properties["tool"].setdefault("properties", {})

    for plugin in plugins:
        pid, tool, schema = plugin_id(plugin), plugin.tool_name, plugin.tool_schema
        if tool in tool_properties:
            _logger.warning(f"{pid} overwrites `tool.{tool}` schema")
        else:
            _logger.info(f"{pid} defines `tool.{tool}` schema")
        tool_properties[tool] = clean(schema)

    return overall_schema


class Validator:
    def __init__(
        self,
        plugins: Union[Sequence[Plugin], AllPlugins] = ALL_PLUGINS,
        format_validators: Mapping[str, FormatValidationFn] = FORMAT_FUNCTIONS,
        extra_validations: Sequence[ValidationFn] = EXTRA_VALIDATIONS,
    ):
        self._cache: Optional[ValidationFn] = None
        self._schema: Optional[Schema] = None
        self._format_validators: Optional[Dict[str, FormatValidationFn]] = None
        self._in_format_validators = dict(format_validators)
        # REMOVED: Plugins can no longer specify extra validations
        # >>> self._extra_validations: Optional[List[ValidationFn]] = None
        self._in_extra_validations = list(extra_validations)

        if plugins is ALL_PLUGINS:
            from .plugins import list_from_entry_points

            plugins = list_from_entry_points()

        self.plugins = tuple(plugins)  # force immutability / read only

    @property
    def schema(self) -> Schema:
        if self._schema is None:
            self._schema = combine(self.plugins)
        return self._schema

    @property
    def extra_validations(self) -> List[ValidationFn]:
        # REMOVED: Plugins can no longer specify extra validations
        # (it is too complicated to embed them)
        # >>> if self._extra_validations is None:
        # >>>     from_plugins = _chain_iter(p.extra_validations for p in self.plugins)
        # >>>     self._extra_validations = [*self._in_extra_validations, *from_plugins]
        return self._in_extra_validations

    @property
    def format_validators(self) -> Dict[str, FormatValidationFn]:
        if self._format_validators is None:
            formats = _chain_iter(
                p.format_validators.items()
                for p in self.plugins
                if hasattr(p, "format_validators")
            )
            formats = chain(self._in_format_validators.items(), formats)
            self._format_validators = dict(formats)
        return self._format_validators

    def __call__(self, pyproject: T) -> T:
        if self._cache is None:
            kw = {"formats": self.format_validators}
            self._cache = cast(ValidationFn, fastjsonschema.compile(self.schema, **kw))

        self._cache(pyproject)
        return reduce(lambda acc, fn: fn(acc), self.extra_validations, pyproject)
