import json
import logging
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, NamedTuple, Sequence

from .. import cli
from ..plugins import PluginWrapper
from ..plugins import list_from_entry_points as list_plugins_from_entry_points
from . import pre_compile

if sys.platform == "win32":  # pragma: no cover
    from subprocess import list2cmdline as arg_join
elif sys.version_info[:2] >= (3, 8):  # pragma: no cover
    from shlex import join as arg_join
else:  # pragma: no cover
    from shlex import quote

    def arg_join(args: Sequence[str]) -> str:
        return " ".join(quote(x) for x in args)


_logger = logging.getLogger(__package__)

META: Dict[str, dict] = {
    "output_dir": dict(
        flags=("-O", "--output-dir"),
        default=".",
        type=Path,
        help="Path to the directory where the files for embedding will be generated "
        "(default: current working directory)",
    ),
    "main_file": dict(
        flags=("-M", "--main-file"),
        default="__init__.py",
        help="Name of the file that will contain the main `validate` function"
        "(default: `%(default)s`)",
    ),
    "replacements": dict(
        flags=("-R", "--replacements"),
        default="{}",
        type=lambda x: ensure_dict("replacements", json.loads(x)),
        help="JSON string (don't forget to quote) representing a map between strings "
        "that should be replaced in the generated files and their replacement, "
        "for example: \n"
        '-R \'{"from packaging import": "from .._vendor.packaging import"}\'',
    ),
}


def ensure_dict(name: str, value: Any) -> dict:
    if not isinstance(value, dict):
        msg = f"`{value.__class__.__name__}` given (value = {value!r})."
        raise ValueError(f"`{name}` should be a dict. {msg}")
    return value


class CliParams(NamedTuple):
    plugins: List[PluginWrapper]
    output_dir: Path = Path(".")
    main_file: str = "__init__.py"
    replacements: Mapping[str, str] = MappingProxyType({})
    loglevel: int = logging.WARNING


def parser_spec(plugins: Sequence[PluginWrapper]) -> Dict[str, dict]:
    common = ("version", "enable", "disable", "verbose", "very_verbose")
    cli_spec = cli.__meta__(plugins)
    meta = {k: v.copy() for k, v in META.items()}
    meta.update({k: cli_spec[k].copy() for k in common})
    return meta


def run(args: Sequence[str] = ()):
    args = args if args else sys.argv[1:]
    cmd = f"python -m {__package__} " + arg_join(args)
    plugins = list_plugins_from_entry_points()
    desc = 'Generate files for "pre-compiling" `validate-pyproject`'
    prms = cli.parse_args(args, plugins, desc, parser_spec, CliParams)
    cli.setup_logging(prms.loglevel)
    pre_compile(prms.output_dir, prms.main_file, cmd, prms.plugins, prms.replacements)
    return 0


main = cli.exceptions2exit()(run)


if __name__ == "__main__":
    main()
