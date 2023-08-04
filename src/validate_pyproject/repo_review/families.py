from __future__ import annotations

from .. import plugins

__all__ = ["repo_review_families"]


def __dir__() -> list[str]:
    return __all__


def repo_review_families() -> dict[str, dict[str, str]]:
    plugin_list = (f"`[tool.{ep.name}]`" for ep in plugins.iterate_entry_points())
    descr = f"Checks `[build-system]`, `[project]`, {', '.join(plugin_list)}"
    return {"validate-pyproject": {"name": "Validate-PyProject", "description": descr}}
