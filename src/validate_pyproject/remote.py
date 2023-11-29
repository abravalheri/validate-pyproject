import io
import json
import sys
import typing
import urllib.parse
import urllib.request
from typing import Tuple

from . import errors
from .types import Schema

if typing.TYPE_CHECKING:
    if sys.version_info < (3, 11):
        from typing_extensions import Self
    else:
        from typing import Self

if sys.platform == "emscripten" and "pyodide" in sys.modules:
    from pyodide.http import open_url
else:

    def open_url(url: str) -> io.StringIO:
        if not url.startswith(("http:", "https:")):
            raise ValueError("URL must start with 'http:' or 'https:'")
        with urllib.request.urlopen(url) as response:  # noqa: S310
            return io.StringIO(response.read().decode("utf-8"))


__all__ = ["RemotePlugin"]


def load_from_uri(tool_uri: str) -> Tuple[str, Schema]:
    tool_info = urllib.parse.urlparse(tool_uri)
    if tool_info.netloc:
        url = f"{tool_info.scheme}://{tool_info.netloc}{tool_info.path}"
        with open_url(url) as f:
            contents = json.load(f)
    else:
        with open(tool_info.path, "rb") as f:
            contents = json.load(f)
    return tool_info.fragment, contents


class RemotePlugin:
    def __init__(self, tool: str, url: str):
        self.tool = tool
        self.fragment, self.schema = load_from_uri(url)
        self.id = self.schema["$id"]
        self.help_text = f"{tool} <external>"

    @classmethod
    def from_str(cls, tool_url: str) -> "Self":
        tool, _, url = tool_url.partition("=")
        if not url:
            raise errors.URLMissingTool(tool)
        return cls(tool, url)


if typing.TYPE_CHECKING:
    from .plugins import PluginProtocol

    _: PluginProtocol = typing.cast(RemotePlugin, None)
