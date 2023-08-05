from __future__ import annotations

from typing import Any

from .. import plugins

__all__ = ["repo_review_families"]


def __dir__() -> list[str]:
    return __all__


def repo_review_families(pyproject: dict[str, Any]) -> dict[str, dict[str, str]]:
    has_distutils = "distutils" in pyproject.get("tool", {})
    plugin_names = (ep.name for ep in plugins.iterate_entry_points())
    plugin_list = (
        f"`[tool.{n}]`" for n in plugin_names if n != "distutils" or has_distutils
    )
    descr = f"Checks `[build-system]`, `[project]`, {', '.join(plugin_list)}"
    return {"validate-pyproject": {"name": "Validate-PyProject", "description": descr}}
