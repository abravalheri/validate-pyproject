# The code in this module is mostly borrowed/adapted from PyScaffold and was originally
# published under the MIT license
# The original PyScaffold license can be found in 'NOTICE.txt'
import functools
import importlib.metadata
import sys
from types import ModuleType
from typing import List

import pytest

from validate_pyproject import plugins
from validate_pyproject.plugins import ErrorLoadingPlugin, PluginWrapper, StoredPlugin

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

        pw = plugins.StoredPlugin("name", {}, "id1")
        assert pw.help_text == ""

        def _fn2(_):
            """Help for `${tool}`"""
            return {}

        pw = plugins.StoredPlugin("name", {"description": "Help for me"}, "id2")
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
    s1 = {"$id": "example1"}
    s2 = {"$id": "example2"}
    s3 = {"$id": "example3"}
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

    (fragmented,) = (e for e in lst if e.tool)
    assert fragmented.tool == "example"
    assert fragmented.fragment == "frag"
    assert fragmented.schema == s1


def fake_both_iterate_entry_points(
    name: str, epname: str
) -> List[importlib.metadata.EntryPoint]:
    if name == "validate_pyproject.multi_schema":
        return [
            importlib.metadata.EntryPoint(
                name=epname,
                value="test_module:f",
                group="validate_pyproject.multi_schema",
            )
        ]
    if name == "validate_pyproject.tool_schema":
        return [
            importlib.metadata.EntryPoint(
                name="example1",
                value="test_module:f1",
                group="validate_pyproject.tool_schema",
            ),
            importlib.metadata.EntryPoint(
                name="example3",
                value="test_module:f3",
                group="validate_pyproject.tool_schema",
            ),
            importlib.metadata.EntryPoint(
                name="example4",
                value="test_module:f4",
                group="validate_pyproject.tool_schema",
            ),
        ]
    return []


@pytest.mark.parametrize("epname", ["aaa", "zzz"])
def test_combined_plugins(monkeypatch, epname):
    s1 = {"$id": "example1"}
    s2 = {"$id": "example2"}
    s3 = {"$id": "example3"}
    sys.modules["test_module"] = ModuleType("test_module")
    sys.modules["test_module"].f = lambda: {
        "tools": {"example1": s1, "example2": s2, "example3": s3},
    }  # type: ignore[attr-defined]
    sys.modules["test_module"].f1 = lambda _: {"$id": "ztool1"}  # type: ignore[attr-defined]
    sys.modules["test_module"].f3 = lambda _: {"$id": "atool3"}  # type: ignore[attr-defined]
    sys.modules["test_module"].f4 = lambda _: {"$id": "tool4"}  # type: ignore[attr-defined]
    monkeypatch.setattr(
        plugins,
        "iterate_entry_points",
        functools.partial(fake_both_iterate_entry_points, epname=epname),
    )

    lst = plugins.list_from_entry_points()
    assert len(lst) == 4

    assert lst[0].tool == "example1"
    assert isinstance(lst[0], StoredPlugin)

    assert lst[1].tool == "example2"
    assert isinstance(lst[1], StoredPlugin)

    assert lst[2].tool == "example3"
    assert isinstance(lst[2], StoredPlugin)

    assert lst[3].tool == "example4"
    assert isinstance(lst[3], PluginWrapper)


def fake_several_entry_points(
    name: str, *, reverse: bool
) -> List[importlib.metadata.EntryPoint]:
    if name == "validate_pyproject.multi_schema":
        items = [
            importlib.metadata.EntryPoint(
                name="a",
                value="test_module:f1",
                group="validate_pyproject.multi_schema",
            ),
            importlib.metadata.EntryPoint(
                name="b",
                value="test_module:f2",
                group="validate_pyproject.multi_schema",
            ),
        ]
        return items[::-1] if reverse else items
    return []


@pytest.mark.parametrize("reverse", [True, False])
def test_several_multi_plugins(monkeypatch, reverse):
    s1 = {"$id": "example1"}
    s2 = {"$id": "example2"}
    s3 = {"$id": "example3"}
    sys.modules["test_module"] = ModuleType("test_module")
    sys.modules["test_module"].f1 = lambda: {
        "tools": {"example": s1},
    }  # type: ignore[attr-defined]
    sys.modules["test_module"].f2 = lambda: {
        "tools": {"example": s2, "other": s3},
    }  # type: ignore[attr-defined]
    monkeypatch.setattr(
        plugins,
        "iterate_entry_points",
        functools.partial(fake_several_entry_points, reverse=reverse),
    )

    (plugin1, plugin2) = plugins.list_from_entry_points()
    assert plugin1.schema["$id"] == "example1"
    assert plugin2.schema["$id"] == "example3"


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
