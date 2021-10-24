from collections.abc import Mapping
from functools import partial, wraps

import pytest

from validate_pyproject import api, errors, plugins, types


def test_load():
    spec = api.load("pyproject_toml")
    assert isinstance(spec, Mapping)
    assert spec["$id"] == "https://www.python.org/dev/peps/pep-0517/"

    spec = api.load("pep621_project")
    assert spec["$id"] == "https://www.python.org/dev/peps/pep-0621/"


class TestRegistry:
    def test_with_plugins(self):
        plg = plugins.list_from_entry_points()
        registry = api.SchemaRegistry(plg)
        main_schema = registry[registry.main]
        project = main_schema["properties"]["project"]
        assert project["$ref"] == "https://www.python.org/dev/peps/pep-0621/"
        tool = main_schema["properties"]["tool"]
        assert "setuptools" in tool["properties"]
        assert "$ref" in tool["properties"]["setuptools"]

    def fake_plugin(self, name, schema_version=7):
        schema = {
            "$id": f"https://example.com/{name}.schema.json",
            "$schema": f"http://json-schema.org/draft-{schema_version:02d}/schema",
            "type": "object",
        }
        return types.Schema(schema)

    def test_incompatible_versions(self):
        fn = wraps(self.fake_plugin)(partial(self.fake_plugin, schema_version=8))
        plg = plugins.PluginWrapper("plugin", fn)
        with pytest.raises(errors.InvalidSchemaVersion):
            api.SchemaRegistry([plg])

    def test_duplicated_id(self):
        plg = [plugins.PluginWrapper("plg", self.fake_plugin) for _ in range(2)]
        with pytest.raises(errors.SchemaWithDuplicatedId):
            api.SchemaRegistry(plg)

    def test_missing_id(self):
        def _fake_plugin(name):
            plg = dict(self.fake_plugin(name))
            del plg["$id"]
            return types.Schema(plg)

        plg = plugins.PluginWrapper("plugin", _fake_plugin)
        with pytest.raises(errors.SchemaMissingId):
            api.SchemaRegistry([plg])
