from typing import Any, Dict

import fastjsonschema

from . import api, plugins

__all__ = ["VPP001", "repo_review_checks", "repo_review_families"]


class VPP001:
    """Validate pyproject.toml"""

    family = "validate-pyproject"

    @staticmethod
    def check(pyproject: Dict[str, Any]) -> str:
        validator = api.Validator()
        try:
            validator(pyproject)
            return ""
        except fastjsonschema.JsonSchemaValueException as e:
            return f"Invalid pyproject.toml! Error: {e}"


def repo_review_checks() -> Dict[str, VPP001]:
    return {"VPP001": VPP001()}


def repo_review_families(pyproject: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    has_distutils = "distutils" in pyproject.get("tool", {})
    plugin_names = (ep.tool for ep in plugins.list_plugins_from_entry_points())
    plugin_list = (
        f"`[tool.{n}]`" for n in plugin_names if n != "distutils" or has_distutils
    )
    descr = f"Checks `[build-system]`, `[project]`, {', '.join(plugin_list)}"
    return {"validate-pyproject": {"name": "Validate-PyProject", "description": descr}}
