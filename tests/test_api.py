from collections.abc import Mapping

from validate_pyproject import api, plugins


def test_load():
    spec = api.load("pyproject_toml")
    assert isinstance(spec, Mapping)
    assert spec["$id"] == "https://www.python.org/dev/peps/pep-0517/"

    spec = api.load("pep621_project")
    assert spec["$id"] == "https://www.python.org/dev/peps/pep-0621/"


def test_schema_registry():
    plg = plugins.list_from_entry_points()
    registry = api.SchemaRegistry(plg)
    main_schema = registry.main
    project = main_schema["properties"]["project"]
    assert project["$ref"] == "https://www.python.org/dev/peps/pep-0621/"
    tool = main_schema["properties"]["tool"]
    assert "setuptools" in tool["properties"]
    assert "$ref" in tool["properties"]["setuptools"]
