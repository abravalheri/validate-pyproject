import logging

import pytest
import toml
from fastjsonschema import JsonSchemaValueException

from validate_pyproject import api, cli

from .helpers import EXAMPLES, INVALID, error_file, examples, invalid_examples


@pytest.mark.parametrize("example", examples())
def test_examples_api(example):
    toml_equivalent = toml.load(EXAMPLES / example)
    validator = api.Validator()
    return validator(toml_equivalent) is not None


@pytest.mark.parametrize("example", examples())
def test_examples_cli(example):
    assert cli.run(["--dump-json", str(EXAMPLES / example)]) == 0  # no errors


@pytest.mark.parametrize("example", invalid_examples())
def test_invalid_examples_api(example):
    example_file = INVALID / example
    expected_error = error_file(example_file).read_text("utf-8")
    toml_equivalent = toml.load(example_file)
    validator = api.Validator()
    with pytest.raises(JsonSchemaValueException) as exc_info:
        validator(toml_equivalent)
    exception_message = str(exc_info.value)
    for error in expected_error.splitlines():
        assert error in exception_message


@pytest.mark.parametrize("example", invalid_examples())
def test_invalid_examples_cli(example, caplog):
    caplog.set_level(logging.DEBUG)
    example_file = INVALID / example
    expected_error = error_file(example_file).read_text("utf-8")
    with pytest.raises(SystemExit) as exc_info:
        cli.main([str(example_file)])
    assert exc_info.value.args == (1,)
    for error in expected_error.splitlines():
        assert error in caplog.text
