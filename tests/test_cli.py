import inspect
import logging
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from validate_pyproject._vendor.fastjsonschema import JsonSchemaValueException

from validate_pyproject import cli, plugins


class TestHelp:
    def test_list_default_plugins(self, capsys):
        with pytest.raises(SystemExit):
            cli.main(["--help"])
        captured = capsys.readouterr()
        assert "setuptools" in captured.out
        assert "distutils" in captured.out

    def test_no_plugins(self, capsys):
        with pytest.raises(SystemExit):
            cli.parse_args(["--help"], plugins=[])
        captured = capsys.readouterr()
        assert "setuptools" not in captured.out
        assert "distutils" not in captured.out

    def test_custom_plugins(self, capsys):
        fake_plugin = plugins.PluginWrapper("my42", lambda _: {})
        with pytest.raises(SystemExit):
            cli.parse_args(["--help"], plugins=[fake_plugin])
        captured = capsys.readouterr()
        assert "my42" in captured.out


def parse_args(args):
    plg = plugins.list_from_entry_points()
    return cli.parse_args(args, plg)


simple_example = """\
[project]
name = "myproj"
version = "0"

[tool.setuptools]
zip-safe = false
packages = {find = {}}
"""


def write_example(dir_path, *, name="pyproject.toml", _text=simple_example):
    path = Path(dir_path, name)
    path.write_text(_text, "UTF-8")
    return path


def write_invalid_example(dir_path, *, name="pyproject.toml"):
    text = simple_example.replace("zip-safe = false", "zip-safe = { hello = 'world' }")
    return write_example(dir_path, name=name, _text=text)


@pytest.fixture
def valid_example(tmp_path):
    return write_example(tmp_path)


@pytest.fixture
def invalid_example(tmp_path):
    return write_invalid_example(tmp_path)


class TestEnable:
    TOOLS = ("setuptools", "distutils")

    @pytest.mark.parametrize("tool, other_tool", zip(TOOLS, reversed(TOOLS)))
    def test_parse(self, valid_example, tool, other_tool):
        params = parse_args([str(valid_example), "-E", tool])
        assert len(params.plugins) == 1
        assert params.plugins[0].tool == tool

        # Meta test:
        schema = params.plugins[0].schema
        if tool == "setuptools":
            assert "zip-safe" in schema["properties"]
            assert schema["properties"]["zip-safe"]["type"] == "boolean"

    def test_valid(self, valid_example):
        assert cli.main([str(valid_example), "-E", "setuptools"]) == 0

    def test_invalid(self, invalid_example):
        print(invalid_example.read_text())
        with pytest.raises(JsonSchemaValueException):
            cli.run([str(invalid_example), "-E", "setuptools"])

    def test_invalid_not_enabled(self, invalid_example):
        # When the plugin is not enabled, the validator should ignore the tool
        assert cli.main([str(invalid_example), "-E", "distutils"]) == 0


class TestDisable:
    TOOLS = ("setuptools", "distutils")

    @pytest.mark.parametrize("tool, other_tool", zip(TOOLS, reversed(TOOLS)))
    def test_parse(self, valid_example, tool, other_tool):
        params = parse_args([str(valid_example), "-D", tool])
        assert len(params.plugins) == 1
        assert params.plugins[0].tool == other_tool

    def test_valid(self, valid_example):
        assert cli.run([str(valid_example), "-D", "distutils"]) == 0

    def test_invalid(self, invalid_example):
        print(invalid_example.read_text())
        with pytest.raises(JsonSchemaValueException):
            cli.run([str(invalid_example), "-D", "distutils"])

    def test_invalid_disabled(self, invalid_example):
        # When the plugin is disabled, the validator should ignore the tool
        assert cli.main([str(invalid_example), "-D", "setuptools"]) == 0


class TestOutput:
    def test_valid(self, capsys, valid_example):
        cli.main([str(valid_example)])
        captured = capsys.readouterr()
        assert "valid" in captured.out.lower()

    def test_invalid(self, caplog, invalid_example):
        caplog.set_level(logging.DEBUG)
        with pytest.raises(SystemExit):
            cli.main([str(invalid_example)])
        captured = caplog.text.lower()
        assert "`tool.setuptools.zip-safe` must be boolean" in captured
        assert "offending rule" in captured
        assert "given value" in captured
        assert '"type": "boolean"' in captured


def test_multiple_files(tmp_path, capsys):
    N = 3

    valid_files = [
        write_example(tmp_path, name=f"valid-pyproject{i}.toml") for i in range(N)
    ]
    cli.run(map(str, valid_files))
    captured = capsys.readouterr().out.lower()
    number_valid = captured.count("valid file:")
    assert number_valid == N

    invalid_files = [
        write_invalid_example(tmp_path, name=f"invalid-pyproject{i}.toml")
        for i in range(N + 3)
    ]
    with pytest.raises(SystemExit):
        cli.main(map(str, valid_files + invalid_files))

    repl = str(uuid4())
    captured = capsys.readouterr().out.lower()
    captured = captured.replace("invalid file:", repl)
    number_invalid = captured.count(repl)
    number_valid = captured.count("valid file:")
    captured = captured.replace(repl, "invalid file:")
    assert number_valid == N
    assert number_invalid == N + 3


@pytest.mark.skipif(sys.version_info[:2] < (3, 11), reason="requires 3.11+")
def test_parser_is_tomllib():
    """Make sure Python >= 3.11 uses tomllib instead of tomli"""
    module_name = inspect.getmodule(cli.loads).__name__
    assert module_name.startswith("tomllib")
