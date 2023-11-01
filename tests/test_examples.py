import logging
from pathlib import Path

import pytest

from validate_pyproject import _tomllib as tomllib
from validate_pyproject import api, cli
from validate_pyproject.error_reporting import ValidationError

from .helpers import error_file


def test_examples_api(example: Path) -> None:
    toml_equivalent = tomllib.loads(example.read_text())
    validator = api.Validator()
    assert validator(toml_equivalent) is not None


def test_examples_cli(example: Path) -> None:
    assert cli.run(["--dump-json", str(example)]) == 0  # no errors


def test_invalid_examples_api(invalid_example: Path) -> None:
    expected_error = error_file(invalid_example).read_text("utf-8")
    toml_equivalent = tomllib.loads(invalid_example.read_text())
    validator = api.Validator()
    with pytest.raises(ValidationError) as exc_info:
        validator(toml_equivalent)
    exception_message = str(exc_info.value)
    summary = exc_info.value.summary
    for error in expected_error.splitlines():
        assert error in exception_message
        assert error in summary


def test_invalid_examples_cli(invalid_example: Path, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    expected_error = error_file(invalid_example).read_text("utf-8")
    with pytest.raises(SystemExit) as exc_info:
        cli.main([str(invalid_example)])
    assert exc_info.value.args == (1,)
    for error in expected_error.splitlines():
        assert error in caplog.text
