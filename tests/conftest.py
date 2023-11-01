"""
    conftest.py for validate_pyproject.

    Read more about conftest.py under:
    - https://docs.pytest.org/en/stable/fixture.html
    - https://docs.pytest.org/en/stable/writing_plugins.html
"""

from pathlib import Path
from typing import List

import pytest

HERE = Path(__file__).parent.resolve()
EXAMPLES = HERE / "examples"
INVALID = HERE / "invalid-examples"


def examples() -> List[str]:
    return [str(f.relative_to(EXAMPLES)) for f in EXAMPLES.glob("**/*.toml")]


def invalid_examples() -> List[str]:
    return [str(f.relative_to(INVALID)) for f in INVALID.glob("**/*.toml")]


@pytest.fixture(params=examples())
def example(request) -> Path:
    return EXAMPLES / request.param


@pytest.fixture(params=invalid_examples())
def invalid_example(request) -> Path:
    return INVALID / request.param
