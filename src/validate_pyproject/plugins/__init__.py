# The code in this module is mostly borrowed/adapted from PyScaffold and was originally
# published under the MIT license
# The original PyScaffold license can be found in 'NOTICE.txt'
"""
.. _entry point: https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html
"""

import typing
from importlib.metadata import EntryPoint, entry_points
from string import Template
from textwrap import dedent
from typing import Any, Callable, Iterable, List, Optional, Protocol

from .. import __version__
from ..types import Plugin, Schema

ENTRYPOINT_GROUP = "validate_pyproject.tool_schema"


class PluginProtocol(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def tool(self) -> str: ...

    @property
    def schema(self) -> Schema: ...

    @property
    def help_text(self) -> str: ...

    @property
    def fragment(self) -> str: ...


class PluginWrapper:
    def __init__(self, tool: str, load_fn: Plugin):
        self._tool = tool
        self._load_fn = load_fn

    @property
    def id(self) -> str:
        return f"{self._load_fn.__module__}.{self._load_fn.__name__}"

    @property
    def tool(self) -> str:
        return self._tool

    @property
    def schema(self) -> Schema:
        return self._load_fn(self.tool)

    @property
    def fragment(self) -> str:
        return ""

    @property
    def help_text(self) -> str:
        tpl = self._load_fn.__doc__
        if not tpl:
            return ""
        return Template(tpl).safe_substitute(tool=self.tool, id=self.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.tool!r}, {self.id})"


if typing.TYPE_CHECKING:
    _: PluginProtocol = typing.cast(PluginWrapper, None)


def iterate_entry_points(group: str = ENTRYPOINT_GROUP) -> Iterable[EntryPoint]:
    """Produces a generator yielding an EntryPoint object for each plugin registered
    via ``setuptools`` `entry point`_ mechanism.

    This method can be used in conjunction with :obj:`load_from_entry_point` to filter
    the plugins before actually loading them.
    """
    entries = entry_points()
    if hasattr(entries, "select"):  # pragma: no cover
        # The select method was introduced in importlib_metadata 3.9 (and Python 3.10)
        # and the previous dict interface was declared deprecated
        select = typing.cast(
            Any,
            getattr(entries, "select"),  # noqa: B009
        )  # typecheck gymnastics
        entries_: Iterable[EntryPoint] = select(group=group)
    else:  # pragma: no cover
        # TODO: Once Python 3.10 becomes the oldest version supported, this fallback and
        #       conditional statement can be removed.
        entries_ = (plugin for plugin in entries.get(group, []))
    deduplicated = {
        e.name: e for e in sorted(entries_, key=lambda e: (e.name, e.value))
    }
    return list(deduplicated.values())


def load_from_entry_point(entry_point: EntryPoint) -> PluginWrapper:
    """Carefully load the plugin, raising a meaningful message in case of errors"""
    try:
        fn = entry_point.load()
        return PluginWrapper(entry_point.name, fn)
    except Exception as ex:
        raise ErrorLoadingPlugin(entry_point=entry_point) from ex


def list_from_entry_points(
    group: str = ENTRYPOINT_GROUP,
    filtering: Callable[[EntryPoint], bool] = lambda _: True,
) -> List[PluginWrapper]:
    """Produces a list of plugin objects for each plugin registered
    via ``setuptools`` `entry point`_ mechanism.

    Args:
        group: name of the setuptools' entry point group where plugins is being
            registered
        filtering: function returning a boolean deciding if the entry point should be
            loaded and included (or not) in the final list. A ``True`` return means the
            plugin should be included.
    """
    return [
        load_from_entry_point(e) for e in iterate_entry_points(group) if filtering(e)
    ]


class ErrorLoadingPlugin(RuntimeError):
    _DESC = """There was an error loading '{plugin}'.
    Please make sure you have installed a version of the plugin that is compatible
    with {package} {version}. You can also try uninstalling it.
    """
    __doc__ = _DESC

    def __init__(self, plugin: str = "", entry_point: Optional[EntryPoint] = None):
        if entry_point and not plugin:
            plugin = getattr(entry_point, "module", entry_point.name)

        sub = {"package": __package__, "version": __version__, "plugin": plugin}
        msg = dedent(self._DESC).format(**sub).splitlines()
        super().__init__(f"{msg[0]}\n{' '.join(msg[1:])}")
