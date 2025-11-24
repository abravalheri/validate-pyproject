from __future__ import annotations

from typing import Any

import fastjsonschema

from . import api, plugins

__all__ = ["VPP001", "repo_review_checks", "repo_review_families"]


class VPP001:
    """Validate pyproject.toml"""

    family = "validate-pyproject"

    @staticmethod
    def check(pyproject: dict[str, Any]) -> str:
        validator = api.Validator()
        try:
            validator(pyproject)
        except fastjsonschema.JsonSchemaValueException as e:
            return f"Invalid pyproject.toml! Error: {e}"
        return ""


def repo_review_checks() -> dict[str, VPP001]:
    return {"VPP001": VPP001()}


def repo_review_families(pyproject: dict[str, Any]) -> dict[str, dict[str, str]]:
    has_distutils = "distutils" in pyproject.get("tool", {})
    plugin_list = plugins.list_from_entry_points(
        lambda e: e.name != "distutils" or has_distutils
    )
    plugin_names = (f"`[tool.{n.tool}]`" for n in plugin_list if n.tool)
    descr = f"Checks `[build-system]`, `[project]`, {', '.join(plugin_names)}"
    return {"validate-pyproject": {"name": "Validate-PyProject", "description": descr}}
