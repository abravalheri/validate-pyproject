from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar

from .plugins import PluginProtocol

T = TypeVar("T", bound=Mapping)

_TOOL_TABLE = "tool.validate-pyproject"
_ENV_PREFIX = "VALIDATE_PYPROJECT_"


@dataclass(frozen=True)
class Config:
    """Configuration for ``validate-pyproject``."""

    enable: tuple[str, ...] = ()
    disable: tuple[str, ...] = ()


@dataclass(frozen=True)
class _PyprojectConfig:
    """Configuration read from pyproject.toml."""

    enable: tuple[str, ...] = ()
    disable: tuple[str, ...] = ()


@dataclass(frozen=True)
class _EnvConfig:
    """Configuration read from environment variables."""

    enable: tuple[str, ...] = ()
    disable: tuple[str, ...] = ()


def _split(value: str) -> tuple[str, ...]:
    """Split a comma-separated string into a tuple of stripped values."""
    return tuple(x.strip() for x in value.split(",") if x.strip())


def read_env_config(prefix: str = _ENV_PREFIX) -> _EnvConfig:
    """Read configuration from environment variables.

    Variables recognised (case-sensitive):

    * ``<prefix>ENABLE`` — comma-separated list of plugins to enable.
    * ``<prefix>DISABLE`` — comma-separated list of plugins to disable.
    """
    enable = _split(os.environ.get(f"{prefix}ENABLE", ""))
    disable = _split(os.environ.get(f"{prefix}DISABLE", ""))
    return _EnvConfig(enable=enable, disable=disable)


def read_toml_config(pyproject: T) -> _PyprojectConfig:
    """Read the ``[tool.validate-pyproject]`` table from a parsed *pyproject.toml*.

    Args:
        pyproject: a :class:`dict`-like object representing the parsed TOML.
    """
    table: Mapping = pyproject.get("tool", {}).get("validate-pyproject", {})

    def _get_list(key: str) -> tuple[str, ...]:
        value = table.get(key, ())
        if isinstance(value, str):
            return _split(value)
        return tuple(str(x) for x in value) if value else ()

    return _PyprojectConfig(enable=_get_list("enable"), disable=_get_list("disable"))


def select_plugins(
    plugins: Sequence[PluginProtocol],
    enabled: Sequence[str] = (),
    disabled: Sequence[str] = (),
) -> list[PluginProtocol]:
    """Filter *plugins* according to *enabled* and *disabled*.

    If *enabled* is given, only plugins whose :attr:`~PluginProtocol.tool`
    name appears in *enabled* are kept.
    If *disabled* is given, plugins whose tool name appears in *disabled*
    are removed.
    """
    available = list(plugins)
    if enabled:
        available = [p for p in available if p.tool in enabled]
    if disabled:
        available = [p for p in available if p.tool not in disabled]
    return available


def apply_config(
    plugins: Sequence[PluginProtocol],
    *,
    pyproject: T | None = None,
    cli_enable: Sequence[str] = (),
    cli_disable: Sequence[str] = (),
) -> list[PluginProtocol]:
    """Resolve plugin list with precedence **CLI > env var > pyproject.toml**.

    Args:
        plugins: full list of plugins (e.g. from entry-points).
        pyproject: optional parsed *pyproject.toml* dict used for config lookup.
        cli_enable: plugins explicitly enabled on the CLI.
        cli_disable: plugins explicitly disabled on the CLI.
    """
    if cli_enable or cli_disable:
        return select_plugins(plugins, enabled=cli_enable, disabled=cli_disable)

    env_config = read_env_config()
    if env_config.enable or env_config.disable:
        return select_plugins(
            plugins, enabled=env_config.enable, disabled=env_config.disable
        )

    if pyproject is not None:
        toml_config = read_toml_config(pyproject)
        return select_plugins(
            plugins, enabled=toml_config.enable, disabled=toml_config.disable
        )

    return list(plugins)
