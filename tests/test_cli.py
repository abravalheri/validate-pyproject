import logging
from pathlib import Path

import pytest
from fastjsonschema import JsonSchemaValueException

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


def write_example(dir_path, text):
    path = Path(dir_path, "pyproject.toml")
    path.write_text(text, "UTF-8")
    return path


@pytest.fixture
def valid_example(tmp_path):
    return write_example(tmp_path, simple_example)


@pytest.fixture
def invalid_example(tmp_path):
    example = simple_example.replace(
        "zip-safe = false", "zip-safe = { hello = 'world' }"
    )
    return write_example(tmp_path, example)


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
        assert "data.zip-safe must be boolean" in captured
        assert "offending rule" in captured
        assert "given value" in captured
        assert '"type": "boolean"' in captured
