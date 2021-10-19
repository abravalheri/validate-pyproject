"""
Retrieve JSON schemas for validating dicts representing a ``pyproject.toml`` file.
"""
import json
import logging
import sys
from typing import List, Sequence, Tuple

from .types import Plugin, Schema

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


TOP_LEVEL_SCHEMA_FILE = "pep518"
PROJECT_TABLE_SCHEMA_FILE = "pep621_project"

NOT_SAFE_FOR_EMBEDDING = ["$schema"]
"""JSON Schemas should be fairly compositional, however some fields are
expected to be present only in the top-level definition.
"""

_logger = logging.getLogger(__name__)


def load(name: str, package: str = __package__, ext: str = ".json") -> Schema:
    """Load the schema from a JSON Schema file"""
    return Schema(json.loads(read_text(__package__, f"{name}.{ext}")))


def load_from_plugins(plugins: Sequence[Plugin]) -> List[Tuple[str, str, Schema]]:
    """Load the schemas for the `tool.xxx` table from plugins"""
    return [(f"{p.__module__}.{p.__qualname__}", *p()) for p in plugins]


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
    overall_schema["properties"]["project"] = clean(project_table_schema)

    tool_schemas = load_from_plugins(plugins)
    tool_properties = overall_schema["tool"].setdefault("properties", {})

    for plugin_id, tool_name, tool_schema in tool_schemas:
        if tool_name in tool_properties:
            _logger.warning(f"{plugin_id} overwrites `tool.{tool_name}` schema")
        else:
            _logger.info(f"{plugin_id} defines `tool.{tool_name}` schema")
        tool_properties[tool_name] = clean(tool_schema)

    return overall_schema
