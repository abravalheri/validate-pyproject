from collections.abc import Mapping
from functools import partial, wraps

import fastjsonschema as FJS
import pytest

from validate_pyproject import _tomllib as tomllib
from validate_pyproject import api, errors, plugins, types

PYPA_SPECS = "https://packaging.python.org/en/latest/specifications"


def test_load():
    spec = api.load("pyproject_toml")
    assert isinstance(spec, Mapping)

    assert spec["$id"] == f"{PYPA_SPECS}/declaring-build-dependencies/"

    spec = api.load("project_metadata")
    assert spec["$id"] == f"{PYPA_SPECS}/pyproject-toml/"


def test_load_plugin():
    spec = api.load_builtin_plugin("distutils")
    assert spec["$id"].startswith("https://setuptools.pypa.io")
    assert "deprecated/distutils" in spec["$id"]

    spec = api.load_builtin_plugin("setuptools")
    assert spec["$id"].startswith("https://setuptools.pypa.io")
    assert "pyproject" in spec["$id"]


class TestRegistry:
    def test_with_plugins(self):
        plg = plugins.list_from_entry_points()
        registry = api.SchemaRegistry(plg)
        main_schema = registry[registry.main]
        project = main_schema["properties"]["project"]
        assert project["$ref"] == f"{PYPA_SPECS}/pyproject-toml/"
        tool = main_schema["properties"]["tool"]
        assert "setuptools" in tool["properties"]
        assert "$ref" in tool["properties"]["setuptools"]

    def fake_plugin(self, name, schema_version=7, end="#"):
        schema = {
            "$id": f"https://example.com/{name}.schema.json",
            "$schema": f"http://json-schema.org/draft-{schema_version:02d}/schema{end}",
            "type": "object",
        }
        return types.Schema(schema)

    @pytest.mark.parametrize("end", ["", "#"], ids=["no#", "with#"])
    def test_schema_ending(self, end):
        fn = wraps(self.fake_plugin)(partial(self.fake_plugin, end=end))
        plg = plugins.PluginWrapper("plugin", fn)
        registry = api.SchemaRegistry([plg])
        main_schema = registry[registry.main]
        assert main_schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_incompatible_versions(self):
        fn = wraps(self.fake_plugin)(partial(self.fake_plugin, schema_version=8))
        plg = plugins.PluginWrapper("plugin", fn)
        with pytest.raises(errors.InvalidSchemaVersion):
            api.SchemaRegistry([plg])

    def test_duplicated_id_different_tools(self):
        schema = self.fake_plugin("plg")
        fn = wraps(self.fake_plugin)(lambda _: schema)  # Same ID
        plg = [plugins.PluginWrapper(f"plg{i}", fn) for i in range(2)]
        with pytest.raises(errors.SchemaWithDuplicatedId):
            api.SchemaRegistry(plg)

    def test_allow_overwrite_same_tool(self):
        plg = [plugins.PluginWrapper("plg", self.fake_plugin) for _ in range(2)]
        registry = api.SchemaRegistry(plg)
        sid = self.fake_plugin("plg")["$id"]
        assert sid in registry

    def test_missing_id(self):
        def _fake_plugin(name):
            plg = dict(self.fake_plugin(name))
            del plg["$id"]
            return types.Schema(plg)

        plg = plugins.PluginWrapper("plugin", _fake_plugin)
        with pytest.raises(errors.SchemaMissingId):
            api.SchemaRegistry([plg])


class TestValidator:
    example_toml = """\
    [project]
    name = "myproj"
    version = "0"

    [tool.setuptools]
    zip-safe = false
    packages = {find = {}}
    """

    @property
    def valid_example(self):
        return tomllib.loads(self.example_toml)

    @property
    def invalid_example(self):
        example = self.valid_example
        example["tool"]["setuptools"]["zip-safe"] = {"hello": "world"}
        return example

    def test_valid(self):
        validator = api.Validator()
        assert validator(self.valid_example) is not None

    def test_invalid(self):
        validator = api.Validator()
        with pytest.raises(FJS.JsonSchemaValueException):
            validator(self.invalid_example)

    # ---

    def plugin(self, tool):
        plg = plugins.list_from_entry_points(filtering=lambda e: e.name == tool)
        return plg[0]

    TOOLS = ("distutils", "setuptools")

    @pytest.mark.parametrize("tool, other_tool", zip(TOOLS, reversed(TOOLS)))
    def test_plugin_not_enabled(self, tool, other_tool):
        plg = self.plugin(tool)
        validator = api.Validator([plg])
        registry = validator.registry
        main_schema = registry[registry.main]
        assert tool in main_schema["properties"]["tool"]["properties"]
        assert other_tool not in main_schema["properties"]["tool"]["properties"]
        tool_properties = main_schema["properties"]["tool"]["properties"]
        assert tool_properties[tool]["$ref"] == plg.schema["$id"]

    def test_invalid_but_plugin_not_enabled(self):
        # When the plugin is not enabled, the validator should ignore the tool
        validator = api.Validator([self.plugin("distutils")])
        try:
            assert validator(self.invalid_example) is not None
        except Exception:
            registry = validator.registry
            main_schema = registry[registry.main]
            assert "setuptools" not in main_schema["properties"]["tool"]["properties"]
            import json

            assert "setuptools" not in json.dumps(main_schema)
            raise
