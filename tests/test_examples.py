import copy
import logging
from pathlib import Path

import pytest

from validate_pyproject import _tomllib as tomllib
from validate_pyproject import api, cli
from validate_pyproject.error_reporting import ValidationError

from .helpers import error_file, get_tools, get_tools_as_args


def test_examples_api(example: Path) -> None:
    load_tools = get_tools(example)

    toml_equivalent = tomllib.loads(example.read_text())
    copy_toml = copy.deepcopy(toml_equivalent)
    validator = api.Validator(extra_plugins=load_tools)
    assert validator(toml_equivalent) is not None
    assert toml_equivalent == copy_toml


def test_examples_cli(example: Path) -> None:
    args = get_tools_as_args(example)

    assert cli.run(["--dump-json", str(example), *args]) == 0  # no errors


def test_invalid_examples_api(invalid_example: Path) -> None:
    load_tools = get_tools(invalid_example)

    expected_error = error_file(invalid_example).read_text("utf-8")
    toml_equivalent = tomllib.loads(invalid_example.read_text())
    validator = api.Validator(extra_plugins=load_tools)
    with pytest.raises(ValidationError) as exc_info:
        validator(toml_equivalent)
    exception_message = str(exc_info.value)
    summary = exc_info.value.summary
    for error in expected_error.splitlines():
        assert error in exception_message
        assert error in summary


def test_invalid_examples_cli(invalid_example: Path, caplog) -> None:
    args = get_tools_as_args(invalid_example)

    caplog.set_level(logging.DEBUG)
    expected_error = error_file(invalid_example).read_text("utf-8")
    with pytest.raises(SystemExit) as exc_info:
        cli.main([str(invalid_example), *args])
    assert exc_info.value.args == (1,)
    for error in expected_error.splitlines():
        assert error in caplog.text
