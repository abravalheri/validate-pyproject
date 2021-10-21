import logging
from pathlib import Path

import pytest
import toml
from fastjsonschema import JsonSchemaValueException

from validate_pyproject import api, cli

HERE = Path(__file__).parent
EXAMPLES = HERE / "examples"
INVALID = HERE / "invalid-examples"


def examples():
    return [str(f.relative_to(EXAMPLES)) for f in EXAMPLES.glob("**/*.toml")]


@pytest.mark.parametrize("example", examples())
def test_examples_api(example):
    toml_equivalent = toml.load(EXAMPLES / example)
    validator = api.Validator()
    return validator(toml_equivalent) is not None


@pytest.mark.parametrize("example", examples())
def test_examples_cli(example):
    assert cli.run(["--dump-json", "-i", str(EXAMPLES / example)]) == 0  # no errors


def invalid_examples():
    return [str(f.relative_to(INVALID)) for f in INVALID.glob("**/*.toml")]


@pytest.mark.parametrize("example", invalid_examples())
def test_invalid_examples_api(example):
    expected_error = (INVALID / example).with_name("errors.txt").read_text("utf-8")
    toml_equivalent = toml.load(INVALID / example)
    validator = api.Validator()
    with pytest.raises(JsonSchemaValueException) as exc_info:
        validator(toml_equivalent)
    exception_message = str(exc_info.value)
    for error in expected_error.splitlines():
        assert error in exception_message


@pytest.mark.parametrize("example", invalid_examples())
def test_invalid_examples_cli(example, caplog):
    caplog.set_level(logging.DEBUG)
    expected_error = (INVALID / example).with_name("errors.txt").read_text("utf-8")
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["-i", str(INVALID / example)])
    assert exc_info.value.args == (1,)
    for error in expected_error.splitlines():
        assert error in caplog.text
