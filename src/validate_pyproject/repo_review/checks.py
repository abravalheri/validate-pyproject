from __future__ import annotations

from typing import Any

import fastjsonschema

from .. import api

__all__ = ["VPP001", "repo_review_checks"]


class VPP001:
    """Validate pyproject.toml"""

    family = "validate-pyproject"

    @staticmethod
    def check(pyproject: dict[str, Any]) -> str:
        validator = api.Validator()
        try:
            validator(pyproject)
            return ""
        except fastjsonschema.JsonSchemaValueException as e:
            return f"Invalid pyproject.toml! Error: {e}"


def repo_review_checks() -> dict[str, VPP001]:
    return {"VPP001": VPP001()}
