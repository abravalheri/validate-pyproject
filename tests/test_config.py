import os
from textwrap import dedent

import pytest

from validate_pyproject import _tomllib as tomllib
from validate_pyproject import config
from validate_pyproject.plugins import PluginWrapper


def _toml(text: str) -> dict:
    return tomllib.loads(dedent(text))


class TestReadTOMLConfig:
    def test_empty(self):
        assert config.read_toml_config(_toml("[project]\nname = \"x\"")).enable == ()
        assert config.read_toml_config(_toml("[project]\nname = \"x\"")).disable == ()

    def test_enable(self):
        pyproject = _toml("""\
        [tool.validate-pyproject]
        enable = ["setuptools"]
        """)
        cfg = config.read_toml_config(pyproject)
        assert cfg.enable == ("setuptools",)
        assert cfg.disable == ()

    def test_disable(self):
        pyproject = _toml("""\
        [tool.validate-pyproject]
        disable = ["distutils"]
        """)
        cfg = config.read_toml_config(pyproject)
        assert cfg.enable == ()
        assert cfg.disable == ("distutils",)

    def test_both(self):
        pyproject = _toml("""\
        [tool.validate-pyproject]
        enable = ["setuptools"]
        disable = ["distutils"]
        """)
        cfg = config.read_toml_config(pyproject)
        assert cfg.enable == ("setuptools",)
        assert cfg.disable == ("distutils",)

    def test_enable_string(self):
        """A single string should be split like a comma-separated list."""
        pyproject = _toml("""\
        [tool.validate-pyproject]
        enable = "setuptools"
        """)
        cfg = config.read_toml_config(pyproject)
        assert cfg.enable == ("setuptools",)
        assert cfg.disable == ()


class TestReadEnvConfig:
    def teardown_method(self):
        for key in ("VALIDATE_PYPROJECT_ENABLE", "VALIDATE_PYPROJECT_DISABLE"):
            os.environ.pop(key, None)

    def test_no_env(self):
        cfg = config.read_env_config()
        assert cfg.enable == ()
        assert cfg.disable == ()

    def test_enable(self):
        os.environ["VALIDATE_PYPROJECT_ENABLE"] = "setuptools,distutils"
        cfg = config.read_env_config()
        assert cfg.enable == ("setuptools", "distutils")
        assert cfg.disable == ()

    def test_disable(self):
        os.environ["VALIDATE_PYPROJECT_DISABLE"] = "setuptools"
        cfg = config.read_env_config()
        assert cfg.enable == ()
        assert cfg.disable == ("setuptools",)

    def test_both(self):
        os.environ["VALIDATE_PYPROJECT_ENABLE"] = "setuptools"
        os.environ["VALIDATE_PYPROJECT_DISABLE"] = "distutils"
        cfg = config.read_env_config()
        assert cfg.enable == ("setuptools",)
        assert cfg.disable == ("distutils",)


class TestSelectPlugins:
    @pytest.fixture
    def plugins(self):
        return [
            PluginWrapper("setuptools", lambda _: {}),
            PluginWrapper("distutils", lambda _: {}),
            PluginWrapper("poetry", lambda _: {}),
        ]

    def test_all(self, plugins):
        assert config.select_plugins(plugins) == plugins

    def test_enable(self, plugins):
        result = config.select_plugins(plugins, enabled=("setuptools",))
        assert len(result) == 1
        assert result[0].tool == "setuptools"

    def test_disable(self, plugins):
        result = config.select_plugins(plugins, disabled=("setuptools",))
        assert len(result) == 2
        assert all(p.tool != "setuptools" for p in result)

    def test_enable_and_disable(self, plugins):
        # enable wins first, then disable applied to the remaining
        result = config.select_plugins(
            plugins, enabled=("setuptools", "distutils"), disabled=("distutils",)
        )
        assert len(result) == 1
        assert result[0].tool == "setuptools"


class TestApplyConfig:
    @pytest.fixture
    def plugins(self):
        return [
            PluginWrapper("setuptools", lambda _: {}),
            PluginWrapper("distutils", lambda _: {}),
        ]

    def test_no_args_uses_all(self, plugins):
        assert config.apply_config(plugins) == plugins

    def test_cli_overrides_toml(self, plugins):
        pyproject = _toml("[tool.validate-pyproject]\ndisable = ['setuptools']")
        result = config.apply_config(plugins, pyproject=pyproject, cli_enable=("setuptools",))
        assert len(result) == 1
        assert result[0].tool == "setuptools"

    def test_cli_overrides_env(self, monkeypatch, plugins):
        monkeypatch.setenv("VALIDATE_PYPROJECT_DISABLE", "setuptools")
        result = config.apply_config(
            plugins, cli_enable=("distutils",), cli_disable=()
        )
        assert result[0].tool == "distutils"

    def test_env_overrides_toml(self, monkeypatch, plugins):
        pyproject = _toml("[tool.validate-pyproject]\ndisable = ['distutils']")
        monkeypatch.setenv("VALIDATE_PYPROJECT_DISABLE", "setuptools")
        result = config.apply_config(plugins, pyproject=pyproject)
        # env disables setuptools, not distutils
        assert all(p.tool != "setuptools" for p in result)
        assert any(p.tool == "distutils" for p in result)

    def test_toml_used_when_no_env_or_cli(self, plugins):
        pyproject = _toml("[tool.validate-pyproject]\nenable = ['distutils']")
        result = config.apply_config(plugins, pyproject=pyproject)
        assert len(result) == 1
        assert result[0].tool == "distutils"
