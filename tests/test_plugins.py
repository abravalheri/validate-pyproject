# The code in this module is mostly borrowed/adapted from PyScaffold and was originally
# published under the MIT license
# The original PyScaffold license can be found in 'NOTICE.txt'

import sys

import pytest

from validate_pyproject import plugins
from validate_pyproject.plugins import ENTRYPOINT_GROUP, ErrorLoadingPlugin

EXISTING = (
    "setuptools",
    "distutils",
)


if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import EntryPoint  # pragma: no cover
else:
    from importlib_metadata import EntryPoint  # pragma: no cover


def test_load_from_entry_point__error():
    # This module does not exist, so Python will have some trouble loading it
    # EntryPoint(name, value, group)
    entry = "mypkg.SOOOOO___fake___:activate"
    fake = EntryPoint("fake", entry, ENTRYPOINT_GROUP)
    with pytest.raises(ErrorLoadingPlugin):
        plugins.load_from_entry_point(fake)


def test_iterate_entry_points():
    plugin_iter = plugins.iterate_entry_points()
    assert hasattr(plugin_iter, "__iter__")
    pluging_list = list(plugin_iter)
    assert all([isinstance(e, EntryPoint) for e in pluging_list])
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
