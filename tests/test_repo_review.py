from pathlib import Path

import pytest

repo_review_processor = pytest.importorskip("repo_review.processor")

DIR = Path(__file__).parent.resolve()
EXAMPLES = DIR / "examples"
INVALID_EXAMPLES = DIR / "invalid-examples"


@pytest.mark.parametrize("name", ["atoml", "flit", "pdm", "pep_text", "trampolim"])
def test_valid_example(name: str) -> None:
    processed = repo_review_processor.process(EXAMPLES / name)
    assert all(r.result for r in processed.results), f"{processed.results}"


@pytest.mark.parametrize("name", ["pdm/invalid-version", "pdm/redefining-as-dynamic"])
def test_invalid_example(name: str) -> None:
    processed = repo_review_processor.process(INVALID_EXAMPLES / name)
    assert any(
        not r.result and r.result is not None for r in processed.results
    ), f"{processed.results}"


def test_no_distutils() -> None:
    processed = repo_review_processor.process(EXAMPLES / "pep_text")
    family = processed.families["validate-pyproject"]
    assert "[tool.setuptools]" in family["description"]
    assert "[tool.distutils]" not in family["description"]


def test_has_distutils(tmp_path: Path) -> None:
    d = tmp_path / "no-distutils"
    d.mkdir()
    d.joinpath("pyproject.toml").write_text("[tool.distutils]")
    processed = repo_review_processor.process(d)
    family = processed.families["validate-pyproject"]
    assert "[tool.setuptools]" in family["description"]
    assert "[tool.distutils]" in family["description"]
