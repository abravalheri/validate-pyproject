import logging
from pathlib import Path

import pytest

from validate_pyproject import _tomllib as tomllib
from validate_pyproject import api, cli
from validate_pyproject.error_reporting import ValidationError

from .helpers import error_file, get_test_config


def test_examples_api(example: Path) -> None:
    tools = get_test_config(example).get("tools", {})
    load_tools = [f"{k}={v}" for k, v in tools.items()]

    toml_equivalent = tomllib.loads(example.read_text())
    validator = api.Validator(load_tools=load_tools)
    assert validator(toml_equivalent) is not None


def test_examples_cli(example: Path) -> None:
    tools = get_test_config(example).get("tools", {})
    args = [f"--tool={k}={v}" for k, v in tools.items()]

    assert cli.run(["--dump-json", str(example), *args]) == 0  # no errors


def test_invalid_examples_api(invalid_example: Path) -> None:
    tools = get_test_config(invalid_example).get("tools", {})
    load_tools = [f"{k}={v}" for k, v in tools.items()]

    expected_error = error_file(invalid_example).read_text("utf-8")
    toml_equivalent = tomllib.loads(invalid_example.read_text())
    validator = api.Validator(load_tools=load_tools)
    with pytest.raises(ValidationError) as exc_info:
        validator(toml_equivalent)
    exception_message = str(exc_info.value)
    summary = exc_info.value.summary
    for error in expected_error.splitlines():
        assert error in exception_message
        assert error in summary


def test_invalid_examples_cli(invalid_example: Path, caplog) -> None:
    tools = get_test_config(invalid_example).get("tools", {})
    args = [f"--tool={k}={v}" for k, v in tools.items()]

    caplog.set_level(logging.DEBUG)
    expected_error = error_file(invalid_example).read_text("utf-8")
    with pytest.raises(SystemExit) as exc_info:
        cli.main([str(invalid_example), *args])
    assert exc_info.value.args == (1,)
    for error in expected_error.splitlines():
        assert error in caplog.text
