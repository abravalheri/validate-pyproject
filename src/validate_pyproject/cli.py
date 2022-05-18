# The code in this module is based on a similar code from `ini2toml` (originally
# published under the MPL-2.0 license)
# https://github.com/abravalheri/ini2toml/blob/49897590a9254646434b7341225932e54f9626a3/LICENSE.txt

import argparse
import io
import json
import logging
import sys
from contextlib import contextmanager
from itertools import chain
from textwrap import dedent, wrap
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    NamedTuple,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)

from . import __version__
from .api import Validator
from .errors import ValidationError
from .plugins import PluginWrapper
from .plugins import list_from_entry_points as list_plugins_from_entry_points

_logger = logging.getLogger(__package__)
T = TypeVar("T", bound=NamedTuple)


try:  # pragma: no cover
    if sys.version_info[:2] >= (3, 11):
        from tomllib import TOMLDecodeError, loads
    else:
        from tomli import TOMLDecodeError, loads
except ImportError:  # pragma: no cover
    try:
        from toml import TomlDecodeError as TOMLDecodeError  # type: ignore
        from toml import loads  # type: ignore
    except ImportError as ex:
        raise ImportError("Please install `tomli` (TOML parser)") from ex

_REGULAR_EXCEPTIONS = (ValidationError, TOMLDecodeError)


@contextmanager
def critical_logging():
    """Make sure the logging level is set even before parsing the CLI args"""
    try:
        yield
    except Exception:  # pragma: no cover
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
        dest="input_file",
        nargs="*",
        default=[argparse.FileType("r")("-")],
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
    "dump_json": dict(
        flags=("--dump-json",),
        action="store_true",
        help="Print the JSON equivalent to the given TOML",
    ),
}


class CliParams(NamedTuple):
    input_file: List[io.TextIOBase]
    plugins: List[PluginWrapper]
    loglevel: int = logging.WARNING
    dump_json: bool = False


def __meta__(plugins: Sequence[PluginWrapper]) -> Dict[str, dict]:
    """'Hyper parameters' to instruct :mod:`argparse` how to create the CLI"""
    meta = {k: v.copy() for k, v in META.items()}
    meta["enable"]["choices"] = set([p.tool for p in plugins])
    return meta


@critical_logging()
def parse_args(
    args: Sequence[str],
    plugins: Sequence[PluginWrapper],
    description: str = "Validate a given TOML file",
    get_parser_spec: Callable[[Sequence[PluginWrapper]], Dict[str, dict]] = __meta__,
    params_class: Type[T] = CliParams,  # type: ignore[assignment]
) -> T:
    """Parse command line parameters

    Args:
      args: command line parameters as list of strings (for example  ``["--help"]``).

    Returns: command line parameters namespace
    """
    epilog = ""
    if plugins:
        epilog = f"The following plugins are available:\n\n{plugins_help(plugins)}"

    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=Formatter
    )
    for cli_opts in get_parser_spec(plugins).values():
        parser.add_argument(*cli_opts.pop("flags", ()), **cli_opts)

    parser.set_defaults(loglevel=logging.WARNING)
    params = vars(parser.parse_args(args))
    enabled = params.pop("enable", ())
    disabled = params.pop("disable", ())
    params["plugins"] = select_plugins(plugins, enabled, disabled)
    return params_class(**params)


def select_plugins(
    plugins: Sequence[PluginWrapper],
    enabled: Sequence[str] = (),
    disabled: Sequence[str] = (),
) -> List[PluginWrapper]:
    available = list(plugins)
    if enabled:
        available = [p for p in available if p.tool in enabled]
    if disabled:
        available = [p for p in available if p.tool not in disabled]
    return available


def setup_logging(loglevel: int):
    """Setup basic logging

    Args:
      loglevel: minimum loglevel for emitting messages
    """
    logformat = "[%(levelname)s] %(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stderr, format=logformat)


@contextmanager
def exceptions2exit():
    try:
        yield
    except _ExceptionGroup as group:
        for prefix, ex in group:
            print(prefix)
            _logger.error(str(ex) + "\n")
        raise SystemExit(1)
    except _REGULAR_EXCEPTIONS as ex:
        _logger.error(str(ex))
        raise SystemExit(1)
    except Exception as ex:  # pragma: no cover
        _logger.error(f"{ex.__class__.__name__}: {ex}\n")
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
    plugins: List[PluginWrapper] = list_plugins_from_entry_points()
    params: CliParams = parse_args(args, plugins)
    setup_logging(params.loglevel)
    validator = Validator(plugins=params.plugins)

    exceptions = _ExceptionGroup()
    for file in params.input_file:
        try:
            toml_equivalent = loads(file.read())
            validator(toml_equivalent)
            if params.dump_json:
                print(json.dumps(toml_equivalent, indent=2))
            else:
                print(f"Valid {_format_file(file)}")
        except _REGULAR_EXCEPTIONS as ex:
            exceptions.add(f"Invalid {_format_file(file)}", ex)

    exceptions.raise_if_any()

    return 0


main = exceptions2exit()(run)


class Formatter(argparse.RawTextHelpFormatter):
    # Since the stdlib does not specify what is the signature we need to implement in
    # order to create our own formatter, we are left no choice other then overwrite a
    # "private" method considered to be an implementation detail.

    def _split_lines(self, text, width):
        return list(chain.from_iterable(wrap(x, width) for x in text.splitlines()))


def plugins_help(plugins: Sequence[PluginWrapper]) -> str:
    return "\n".join(_format_plugin_help(p) for p in plugins)


def _flatten_str(text: str) -> str:
    text = " ".join(x.strip() for x in dedent(text).splitlines()).strip()
    text = text.rstrip(".,;").strip()
    return (text[0].lower() + text[1:]).strip()


def _format_plugin_help(plugin: PluginWrapper) -> str:
    help_text = plugin.help_text
    help_text = f": {_flatten_str(help_text)}" if help_text else ""
    return f'* "{plugin.tool}"{help_text}'


def _format_file(file: io.TextIOBase) -> str:
    if hasattr(file, "name") and file.name:  # type: ignore[attr-defined]
        return f"file: {file.name}"  # type: ignore[attr-defined]
    return "file"  # pragma: no cover


class _ExceptionGroup(Exception):
    def __init__(self):
        self._members: List[Tuple[str, Exception]] = []
        super().__init__()

    def add(self, prefix: str, ex: Exception):
        self._members.append((prefix, ex))

    def __iter__(self) -> Iterator[Tuple[str, Exception]]:
        return iter(self._members)

    def raise_if_any(self):
        number = len(self._members)
        if number == 1:
            print(self._members[0][0])
            raise self._members[0][1]
        if number > 0:
            raise self
