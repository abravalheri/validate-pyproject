# The code in this module is mostly borrowed/adapted from PyScaffold and was originally
# published under the MIT license
# The original PyScaffold license can be found in 'NOTICE.txt'
import importlib.metadata
import sys
from types import ModuleType
from typing import List

import pytest

from validate_pyproject import plugins
from validate_pyproject.plugins import ErrorLoadingPlugin

EXISTING = (
    "setuptools",
    "distutils",
)


def test_load_from_entry_point__error():
    # This module does not exist, so Python will have some trouble loading it
    # EntryPoint(name, value, group)
    entry = "mypkg.SOOOOO___fake___:activate"
    fake = importlib.metadata.EntryPoint(
        "fake", entry, "validate_pyproject.tool_schema"
    )
    with pytest.raises(ErrorLoadingPlugin):
        plugins.load_from_entry_point(fake)


def is_entry_point(ep):
    return all(hasattr(ep, attr) for attr in ("name", "load"))


def test_iterate_entry_points():
    plugin_iter = plugins.iterate_entry_points("validate_pyproject.tool_schema")
    assert hasattr(plugin_iter, "__iter__")
    pluging_list = list(plugin_iter)
    assert all(is_entry_point(e) for e in pluging_list)
    name_list = [e.name for e in pluging_list]
    for ext in EXISTING:
        assert ext in name_list


def test_list_from_entry_points():
    # Should return a list with all the plugins registered in the entrypoints
    pluging_list = plugins.list_from_entry_points()
    orig_len = len(pluging_list)
    plugin_names = " ".join(e.tool for e in pluging_list)
    for example in EXISTING:
        assert example in plugin_names

    # a filtering function can be passed to avoid loading plugins that are not needed
    pluging_list = plugins.list_from_entry_points(
        filtering=lambda e: e.name != "setuptools"
    )
    plugin_names = " ".join(e.tool for e in pluging_list)
    assert len(pluging_list) == orig_len - 1
    assert "setuptools" not in plugin_names


class TestPluginWrapper:
    def test_empty_help_text(self):
        def _fn1(_):
            return {}

        pw = plugins.PluginWrapper("name", _fn1)
        assert pw.help_text == ""

        def _fn2(_):
            """Help for `${tool}`"""
            return {}

        pw = plugins.PluginWrapper("name", _fn2)
        assert pw.help_text == "Help for `name`"


class TestStoredPlugin:
    def test_empty_help_text(self):
        def _fn1(_):
            return {}

        pw = plugins.StoredPlugin("name", {})
        assert pw.help_text == ""

        def _fn2(_):
            """Help for `${tool}`"""
            return {}

        pw = plugins.StoredPlugin("name", {"description": "Help for me"})
        assert pw.help_text == "Help for me"


def fake_multi_iterate_entry_points(name: str) -> List[importlib.metadata.EntryPoint]:
    if name == "validate_pyproject.multi_schema":
        return [
            importlib.metadata.EntryPoint(
                name="_", value="test_module:f", group="validate_pyproject.multi_schema"
            )
        ]
    return []


def test_multi_plugins(monkeypatch):
    s1 = {"id": "example1"}
    s2 = {"id": "example2"}
    s3 = {"id": "example3"}
    sys.modules["test_module"] = ModuleType("test_module")
    sys.modules["test_module"].f = lambda: {
        "tools": {"example#frag": s1},
        "schemas": [s2, s3],
    }  # type: ignore[attr-defined]
    monkeypatch.setattr(
        plugins, "iterate_entry_points", fake_multi_iterate_entry_points
    )

    lst = plugins.list_from_entry_points()
    assert len(lst) == 3
    assert all(e.id.startswith("example") for e in lst)

    (fragmented,) = (e for e in lst if e.tool)
    assert fragmented.tool == "example"
    assert fragmented.fragment == "frag"
    assert fragmented.schema == s1


def test_broken_multi_plugin(monkeypatch):
    def broken_ep():
        raise RuntimeError("Broken")

    sys.modules["test_module"] = ModuleType("test_module")
    sys.modules["test_module"].f = broken_ep
    monkeypatch.setattr(
        plugins, "iterate_entry_points", fake_multi_iterate_entry_points
    )
    with pytest.raises(ErrorLoadingPlugin):
        plugins.list_from_entry_points()
