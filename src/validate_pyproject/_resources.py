""":meta private:"""

from __future__ import annotations

from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


def read_text(package: str | ModuleType, resource: str) -> str:
    """:meta private:"""
    return files(package).joinpath(resource).read_text(encoding="utf-8")
