# The code in this module is mostly borrowed/adapted from PyScaffold and was originally
# published under the MIT license
# The original PyScaffold license can be found in 'NOTICE.txt'

import sys
from types import ModuleType
from typing import Any, List

import pytest

from validate_pyproject import plugins
from validate_pyproject.plugins import ErrorLoadingPlugin

EXISTING = (
    "setuptools",
    "distutils",
)


if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib import metadata  # pragma: no cover
else:
    import importlib_metadata as metadata  # pragma: no cover


def test_load_from_entry_point__error():
    # This module does not exist, so Python will have some trouble loading it
    # metadata.EntryPoint(name, value, group)
    entry = "mypkg.SOOOOO___fake___:activate"
    fake = metadata.EntryPoint("fake", entry, "validate_pyproject.tool_schema")
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
    pluging_list = plugins.list_plugins_from_entry_points()
    orig_len = len(pluging_list)
    plugin_names = " ".join(e.tool for e in pluging_list)
    for example in EXISTING:
        assert example in plugin_names

    # a filtering function can be passed to avoid loading plugins that are not needed
    pluging_list = plugins.list_plugins_from_entry_points(
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


def loader(name: str) -> Any:
    return {"example": "thing"}


def dynamic_ep():
    return {"some#fragment": loader}


class Select(list):
    def select(self, group: str) -> List[str]:
        return list(self) if group == "validate_pyproject.multi_schema" else []


def test_process_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    ep = metadata.EntryPoint(
        name="_",
        group="validate_pyproject.multi_schema",
        value="test_module:dynamic_ep",
    )
    sys.modules["test_module"] = ModuleType("test_module")
    sys.modules["test_module"].dynamic_ep = dynamic_ep  # type: ignore[attr-defined]
    sys.modules["test_module"].loader = loader  # type: ignore[attr-defined]
    monkeypatch.setattr(plugins, "entry_points", lambda: Select([ep]))
    eps = plugins.list_plugins_from_entry_points()
    (ep,) = eps
    assert ep.tool == "some"
    assert ep.fragment == "fragment"
