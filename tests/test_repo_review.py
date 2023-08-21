from argparse import Namespace
from pathlib import Path

import pytest

from validate_pyproject import _tomllib as tomllib
from validate_pyproject.repo_review import repo_review_checks, repo_review_families

DIR = Path(__file__).parent.resolve()
EXAMPLES = DIR / "examples"
INVALID_EXAMPLES = DIR / "invalid-examples"


@pytest.fixture
def repo_review_processor():
    try:
        from repo_review import processor

        return processor
    except ImportError:

        class _Double:  # just for the sake of Python < 3.10 coverage
            @staticmethod
            def process(file: Path):
                pyproject = (file / "pyproject.toml").read_text(encoding="utf-8")
                opts = tomllib.loads(pyproject)
                checks = (
                    checker.check(opts) == ""  # No errors
                    for checker in repo_review_checks().values()
                )
                return Namespace(
                    families=repo_review_families(opts),
                    results=[Namespace(result=check) for check in checks],
                )

        return _Double


@pytest.mark.parametrize("name", ["atoml", "flit", "pdm", "pep_text", "trampolim"])
def test_valid_example(repo_review_processor, name: str) -> None:
    processed = repo_review_processor.process(EXAMPLES / name)
    assert all(r.result for r in processed.results), f"{processed.results}"


@pytest.mark.parametrize("name", ["pdm/invalid-version", "pdm/redefining-as-dynamic"])
def test_invalid_example(repo_review_processor, name: str) -> None:
    processed = repo_review_processor.process(INVALID_EXAMPLES / name)
    assert any(
        not r.result and r.result is not None for r in processed.results
    ), f"{processed.results}"


def test_no_distutils(repo_review_processor) -> None:
    processed = repo_review_processor.process(EXAMPLES / "pep_text")
    family = processed.families["validate-pyproject"]
    assert "[tool.setuptools]" in family["description"]
    assert "[tool.distutils]" not in family["description"]


def test_has_distutils(repo_review_processor, tmp_path: Path) -> None:
    d = tmp_path / "no-distutils"
    d.mkdir()
    d.joinpath("pyproject.toml").write_text("[tool.distutils]")
    processed = repo_review_processor.process(d)
    family = processed.families["validate-pyproject"]
    assert "[tool.setuptools]" in family["description"]
    assert "[tool.distutils]" in family["description"]
