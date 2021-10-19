# The code in this module is based on a similar code from `ini2toml` (originally
# published under the MPL-2.0 license)
# https://github.com/abravalheri/ini2toml/blob/49897590a9254646434b7341225932e54f9626a3/LICENSE.txt

import argparse
import io
import logging
import sys
from contextlib import contextmanager
from itertools import chain
from os import pathsep
from pathlib import Path
from textwrap import dedent, wrap
from typing import Dict, List, NamedTuple, Optional, Sequence

from . import __version__
from .api import Validator, plugin_id
from .types import Plugin

_logger = logging.getLogger(__package__)

DEFAULT_PROFILE = "best_effort"


try:
    from tomli import loads
except ImportError:
    try:
        from toml import loads
    except ImportError as ex:
        raise ImportError("Please install a TOML parser (e.g. `tomli`)") from ex


@contextmanager
def critical_logging():
    """Make sure the logging level is set even before parsing the CLI args"""
    try:
        yield
    except Exception:
        if "-vv" in sys.argv or "--very-verbose" in sys.argv:
            setup_logging(logging.DEBUG)
        raise


META: Dict[str, dict] = {
    "version": dict(
        flags=("-V", "--version"),
        action="version",
        version=f"{__package__} {__version__}",
    ),
    "input_file": dict(
        flags=("-i", "--input-file"),
        default="-",
        type=argparse.FileType("r"),
        help="TOML file to be verified (`stdin` by default)",
    ),
    "enable": dict(
        flags=("-E", "--enable-plugins"),
        nargs="+",
        default=(),
        dest="enable",
        metavar="PLUGINS",
        help="Enable ONLY the given plugins (ALL plugins are enabled by default).",
    ),
    "disable": dict(
        flags=("-D", "--disable-plugins"),
        nargs="+",
        dest="disable",
        default=(),
        metavar="PLUGINS",
        help="Enable ALL plugins, EXCEPT the ones given.",
    ),
    "verbose": dict(
        flags=("-v", "--verbose"),
        dest="loglevel",
        action="store_const",
        const=logging.INFO,
        help="set logging level to INFO",
    ),
    "very_verbose": dict(
        flags=("-vv", "--very-verbose"),
        dest="loglevel",
        action="store_const",
        const=logging.DEBUG,
        help="set logging level to DEBUG",
    ),
}


class CliParams(NamedTuple):
    input_file: io.TextIOBase
    plugins: List[Plugin]
    loglevel: int


def __meta__(plugins: Sequence[Plugin]) -> Dict[str, dict]:
    """'Hyper parameters' to instruct :mod:`argparse` how to create the CLI"""
    return {k: v.copy() for k, v in META.items()}


@critical_logging()
def parse_args(args: Sequence[str], plugins: Sequence[Plugin]) -> CliParams:
    """Parse command line parameters

    Args:
      args: command line parameters as list of strings (for example  ``["--help"]``).

    Returns: command line parameters namespace
    """
    description = "Validate a given TOML file"
    epilog = "The following plugins are available:\n" + _plugins_help(plugins)

    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=Formatter
    )
    for cli_opts in __meta__(plugins).values():
        parser.add_argument(*cli_opts.pop("flags", ()), **cli_opts)

    parser.set_defaults(loglevel=logging.WARNING)
    params = vars(parser.parse_args(args))
    enabled = params.pop("enabled", ())
    disabled = params.pop("disabled", ())
    params["plugins"] = select_plugins(plugins, enabled, disabled)
    return CliParams(**params)


def select_plugins(
    plugins: Sequence[Plugin], enabled: Sequence[str] = (), disabled: Sequence[str] = ()
) -> List[Plugin]:
    available = list(plugins)
    if enabled:
        available = [p for p in available if plugin_id(p) in enabled]
    if disabled:
        available = [p for p in available if plugin_id(p) not in disabled]
    return available


def setup_logging(loglevel: int):
    """Setup basic logging

    Args:
      loglevel: minimum loglevel for emitting messages
    """
    logformat = "[%(levelname)s] %(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stderr, format=logformat)


@contextmanager
def exceptisons2exit():
    try:
        yield
    except Exception as ex:
        _logger.error(f"{ex.__class__.__name__}: {ex}")
        _logger.debug("Please check the following information:", exc_info=True)
        raise SystemExit(1)


def run(args: Sequence[str] = ()):
    """Wrapper allowing :obj:`Translator` to be called in a CLI fashion.

    Instead of returning the value from :func:`Translator.translate`, it prints the
    result to the given ``output_file`` or ``stdout``.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "setup.cfg"]``).
    """
    args = args or sys.argv[1:]
    plugins: List[Plugin] = []  # TODO: load from entry_points
    params = parse_args(args, plugins)
    setup_logging(params.loglevel)
    validator = Validator(plugins=params.plugins)
    toml_equivalent = loads(params.input_file.read())
    return validator(toml_equivalent)


main = exceptisons2exit()(run)


class Formatter(argparse.RawTextHelpFormatter):
    # Since the stdlib does not specify what is the signature we need to implement in
    # order to create our own formatter, we are left no choice other then overwrite a
    # "private" method considered to be an implementation detail.

    def _split_lines(self, text, width):
        return list(chain.from_iterable(wrap(x, width) for x in text.splitlines()))


def guess_profile(profile: Optional[str], file_name: str, available: List[str]) -> str:
    if profile:
        return profile

    name = Path(file_name).name
    if name in available:
        # Optimize for the easy case
        _logger.info(f"Profile not explicitly set, {name!r} inferred.")
        return name

    fname = file_name.replace(pathsep, "/")
    for name in available:
        if fname.endswith(name):
            _logger.info(f"Profile not explicitly set, {name!r} inferred.")
            return name

    _logger.warning(f"Profile not explicitly set, using {DEFAULT_PROFILE!r}.")
    return DEFAULT_PROFILE


def _plugins_help(plugins: Sequence[Plugin]) -> str:
    return "\n".join(_format_plugin_help(p) for p in plugins)


def _flatten_str(text: str) -> str:
    if not text:
        return text
    text = " ".join(x.strip() for x in dedent(text).splitlines()).strip()
    text = text.rstrip(".,;").strip()
    return (text[0].lower() + text[1:]).strip()


def _format_plugin_help(plugin: Plugin) -> str:
    return f'- "{plugin_id(plugin)}": {_flatten_str(plugin.help_text)}.'
