"""
Retrieve JSON schemas for validating dicts representing a ``pyproject.toml`` file.
"""
import json
import logging
import sys
from collections import defaultdict
from enum import Enum
from functools import reduce
from itertools import chain
from types import MappingProxyType
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, TypeVar, Union, cast

import fastjsonschema

from . import errors, format
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

TOP_LEVEL_SCHEMA = "pyproject_toml"
PROJECT_TABLE_SCHEMA = "pep621_project"

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
    """Load the schema from a JSON Schema file.
    The returned dict-like object is immutable.
    """
    return Schema(MappingProxyType(json.loads(read_text(__package__, f"{name}{ext}"))))


def plugin_id(plugin: Plugin):
    return f"{plugin.__module__}.{plugin.__class__.__qualname__}"


def ensure_compatible_schema(
    reference: str, schema: Schema, required_version: str
) -> Schema:
    if "$id" not in schema:
        raise errors.SchemaMissingId(reference)
    version = schema.get("$schema")
    if version and version != required_version:
        raise errors.InvalidSchemaVersion(reference, version, required_version)
    return schema


def combine(plugins: Sequence[Plugin] = ()) -> Tuple[Schema, Dict[str, Schema]]:
    """Retrieve a schema that validates ``pyproject.toml`` by aggregating the
    standard schemas and the ones provided by plugins.

    It returns a tuple with two elements, being the first the main schema against which
    ``pyproject.toml`` should be validated and the second a "registry" of secondary
    schemas referenced by the main one in the form of a ``$id`` => ``Schema`` dict.

    Please notice that all schemas provided by plugins should have a top level ``$id``.
    """
    overall_schema = dict(load(TOP_LEVEL_SCHEMA))  # Make it mutable
    schema_version = overall_schema["$schema"]
    overall_properties = overall_schema["properties"]
    tool_properties = overall_properties["tool"].setdefault("properties", {})

    # Add PEP 621
    project_table_schema = load(PROJECT_TABLE_SCHEMA)
    ensure_compatible_schema(PROJECT_TABLE_SCHEMA, project_table_schema, schema_version)
    overall_properties["project"] = {"$ref": project_table_schema["$id"]}
    registry = {project_table_schema["$id"]: project_table_schema}

    # Add tools using Plugins

    for plugin in plugins:
        pid, tool, schema = plugin_id(plugin), plugin.tool_name, plugin.tool_schema
        if tool in tool_properties:
            _logger.warning(f"{pid} overwrites `tool.{tool}` schema")
        else:
            _logger.info(f"{pid} defines `tool.{tool}` schema")
        sid = ensure_compatible_schema(tool, schema, schema_version)["$id"]
        if sid in registry:
            raise errors.SchemaWithDuplicatedId(sid)
        tool_properties[tool] = {"$ref": sid}
        registry[sid] = schema

    main_schema = Schema(MappingProxyType(overall_schema))  # make it immutable
    registry[main_schema["$id"]] = main_schema
    return main_schema, registry  # make it immutable


class ForcedUriHandler(defaultdict):
    """This object is used to force ``fastjsonschema`` to always look in the local
    registry instead of using :mod:`urllib` to download schemas.
    """

    def __contains__(self, key) -> bool:
        return True


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

            self.plugins = tuple(list_from_entry_points())
        else:
            self.plugins = tuple(plugins)  # force immutability / read only

        self.main_schema, self._schema_registry = combine(self.plugins)
        self._handlers = ForcedUriHandler(lambda _: self.__getitem__)

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

    def __getitem__(self, schema_id: str) -> Schema:
        """Retrieve a schema from registry"""
        return self._schema_registry[schema_id]

    def __call__(self, pyproject: T) -> T:
        if self._cache is None:
            kw = {"formats": self.format_validators, "handlers": self._handlers}
            schema = self.main_schema
            self._cache = cast(ValidationFn, fastjsonschema.compile(schema, **kw))

        self._cache(pyproject)
        return reduce(lambda acc, fn: fn(acc), self.extra_validations, pyproject)
