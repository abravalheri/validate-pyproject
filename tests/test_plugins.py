# The code in this module is mostly borrowed/adapted from PyScaffold and was originally
# published under the MIT license
# The original PyScaffold license can be found in 'NOTICE.txt'
from __future__ import annotations

import sys
from collections import defaultdict
from importlib.metadata import EntryPoint
from types import ModuleType
from typing import Callable, TypeVar

import pytest

from validate_pyproject import plugins
from validate_pyproject.plugins import ErrorLoadingPlugin, PluginWrapper, StoredPlugin

EXISTING = (
    "setuptools",
    "distutils",
)

T = TypeVar("T", bound=Callable)


def test_load_from_entry_point__error():
    # This module does not exist, so Python will have some trouble loading it
    # EntryPoint(name, value, group)
    entry = "mypkg.SOOOOO___fake___:activate"
    fake = EntryPoint("fake", entry, "validate_pyproject.tool_schema")
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

        pw = plugins.StoredPlugin("name", {}, "id1", 0)
        assert pw.help_text == ""

        def _fn2(_):
            """Help for `${tool}`"""
            return {}

        pw = plugins.StoredPlugin("name", {"description": "Help for me"}, "id2", 0)
        assert pw.help_text == "Help for me"


class _FakeEntryPoints:
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        group: str = "__NOT_SPECIFIED__",
        data: defaultdict[str, list[EntryPoint]] | None = None,
    ):
        self._monkeypatch = monkeypatch
        self._group = group
        self._data = defaultdict(list) if data is None else data
        self.get = self._data.__getitem__

    def group(self, group: str) -> _FakeEntryPoints:
        return _FakeEntryPoints(self._monkeypatch, group, self._data)

    def reverse(self) -> _FakeEntryPoints:
        data = defaultdict(list, {k: list(reversed(v)) for k, v in self._data.items()})
        return _FakeEntryPoints(self._monkeypatch, self._group, data)

    def __call__(self, *, name: str, value: str) -> Callable[[T], T]:
        def fake_entry_point(impl: T) -> T:
            ep = EntryPoint(name=name, value=value, group=self._group)
            self._data[ep.group].append(ep)
            module, _, func = ep.value.partition(":")
            if module not in sys.modules:
                self._monkeypatch.setitem(sys.modules, module, ModuleType(module))
            self._monkeypatch.setattr(sys.modules[module], func, impl, raising=False)
            return impl

        return fake_entry_point


def test_multi_plugins(monkeypatch):
    fake_eps = _FakeEntryPoints(monkeypatch, group="validate_pyproject.multi_schema")
    fake_eps(name="f", value="test_module:f")(
        lambda: {
            "tools": {"example#frag": {"$id": "example1"}},
            "schemas": [
                {"$id": "example2"},
                {"$id": "example3"},
            ],
        }
    )
    monkeypatch.setattr(plugins, "iterate_entry_points", fake_eps.get)

    lst = plugins.list_from_entry_points()
    assert len(lst) == 3

    (fragmented,) = (e for e in lst if e.tool)
    assert fragmented.tool == "example"
    assert fragmented.fragment == "frag"
    assert fragmented.schema == {"$id": "example1"}


@pytest.mark.parametrize("epname", ["aaa", "zzz"])
def test_combined_plugins(monkeypatch, epname):
    fake_eps = _FakeEntryPoints(monkeypatch)
    multi_eps = fake_eps.group("validate_pyproject.multi_schema")
    tool_eps = fake_eps.group("validate_pyproject.tool_schema")
    multi_eps(name=epname, value="test_module:f")(
        lambda: {
            "tools": {
                "example1": {"$id": "example1"},
                "example2": {"$id": "example2"},
                "example3": {"$id": "example3"},
            }
        }
    )
    tool_eps(name="example1", value="test_module:f1")(lambda _: {"$id": "ztool1"})
    tool_eps(name="example2", value="test_module:f2")(lambda _: {"$id": "atool2"})
    tool_eps(name="example4", value="test_module:f2")(lambda _: {"$id": "tool4"})

    monkeypatch.setattr(plugins, "iterate_entry_points", fake_eps.get)

    lst = plugins.list_from_entry_points()
    print(lst)
    assert len(lst) == 4

    assert lst[0].tool == "example1"
    assert isinstance(lst[0], PluginWrapper)

    assert lst[1].tool == "example2"
    assert isinstance(lst[1], PluginWrapper)

    assert lst[2].tool == "example3"
    assert isinstance(lst[2], StoredPlugin)

    assert lst[3].tool == "example4"
    assert isinstance(lst[3], PluginWrapper)


def test_several_multi_plugins(monkeypatch):
    fake_eps = _FakeEntryPoints(monkeypatch, "validate_pyproject.multi_schema")
    fake_eps(name="zzz", value="test_module:f1")(
        lambda: {
            "tools": {"example": {"$id": "example1"}},
        }
    )
    fake_eps(name="aaa", value="test_module:f2")(
        lambda: {
            "tools": {"example": {"$id": "example2"}, "other": {"$id": "example3"}}
        }
    )
    for eps in (fake_eps, fake_eps.reverse()):
        monkeypatch.setattr(plugins, "iterate_entry_points", eps.get)
        # entry-point names closer to "zzzzzzzz..." have priority
        (plugin1, plugin2) = plugins.list_from_entry_points()
        print(plugin1, plugin2)
        assert plugin1.schema["$id"] == "example1"
        assert plugin2.schema["$id"] == "example3"


def test_custom_priority(monkeypatch):
    fake_eps = _FakeEntryPoints(monkeypatch)
    tool_eps = fake_eps.group("validate_pyproject.tool_schema")
    multi_eps = fake_eps.group("validate_pyproject.multi_schema")

    multi_schema = {"tools": {"example": {"$id": "multi-eps"}}}
    multi_eps(name="example", value="test_module:f")(lambda: multi_schema)

    @tool_eps(name="example", value="test_module1:f1")
    def tool_schema1(_name):
        return {"$id": "tool-eps-1"}

    @tool_eps(name="example", value="test_module2:f1")
    def tool_schema2(_name):
        return {"$id": "tool-eps-2"}

    monkeypatch.setattr(plugins, "iterate_entry_points", fake_eps.get)
    (winner,) = plugins.list_from_entry_points()  # default: tool with "higher" ep name
    assert winner.schema["$id"] == "tool-eps-2"

    tool_schema1.priority = 1.1
    (winner,) = plugins.list_from_entry_points()  # default: tool has priority
    assert winner.schema["$id"] == "tool-eps-1"

    tool_schema1.priority = 0.1
    tool_schema2.priority = 0.2
    multi_schema["priority"] = 0.9
    (winner,) = plugins.list_from_entry_points()  # custom higher priority wins
    assert winner.schema["$id"] == "multi-eps"


def test_broken_multi_plugin(monkeypatch):
    fake_eps = _FakeEntryPoints(monkeypatch, "validate_pyproject.multi_schema")
    fake_eps(name="broken", value="test_module.f")(lambda: {}["no-such-key"])
    monkeypatch.setattr(plugins, "iterate_entry_points", fake_eps.get)
    with pytest.raises(ErrorLoadingPlugin):
        plugins.list_from_entry_points()
