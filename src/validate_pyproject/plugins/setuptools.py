from .. import api
from ..types import Schema

SCHEMA_NAME = "setuptools"


class Setuptools:
    tool_name = "setuptools"
    help_text = (
        "`setuptools` configuration imagined as if it was done via `pyproject.toml` "
        "(excludes PEP 621-related metadata)."
    )

    @property
    def tool_schema(self) -> Schema:
        return api.load(SCHEMA_NAME, __package__)
