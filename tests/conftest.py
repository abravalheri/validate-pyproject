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


def pytest_configure(config):
    config.addinivalue_line("markers", "uses_network: tests may try to download files")


def collect(base: Path) -> List[str]:
    return [str(f.relative_to(base)) for f in base.glob("**/*.toml")]


@pytest.fixture(params=collect(HERE / "examples"))
def example(request) -> Path:
    return HERE / "examples" / request.param


@pytest.fixture(params=collect(HERE / "invalid-examples"))
def invalid_example(request) -> Path:
    return HERE / "invalid-examples" / request.param


@pytest.fixture(params=collect(HERE / "remote/examples"))
def remote_example(request) -> Path:
    return HERE / "remote/examples" / request.param


@pytest.fixture(params=collect(HERE / "remote/invalid-examples"))
def remote_invalid_example(request) -> Path:
    return HERE / "remote/invalid-examples" / request.param
