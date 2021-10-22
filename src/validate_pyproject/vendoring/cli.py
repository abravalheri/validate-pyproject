import json
import logging
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, NamedTuple, Sequence

from .. import cli, types
from ..plugins import list_from_entry_points as list_plugins_from_entry_points
from . import vendorify

_logger = logging.getLogger(__package__)

META: Dict[str, dict] = {
    "output_dir": dict(
        flags=("-o", "--output-dir"),
        default=".",
        type=Path,
        help="Path to the directory where the files for embedding will be generated",
    ),
    "main_file": dict(
        flags=("-M", "--main-file"),
        default="__init__.py",
        help="Name of the file that will contain the main `validate` function"
        "(default: `__init__.py`)",
    ),
    "replacements": dict(
        flags=("-R", "--replacements"),
        metavar="REPLACEMENTS_JSON",
        type=lambda x: ensure_dict("replacements", json.loads(x)),
        help="JSON representing a map between strings that should be replaced "
        "in the generated files and their replacement "
        '(e.g. `-R \'{"from packaging import": "from .._vendor.packaging import"}\')',
    ),
}


def ensure_dict(name: str, value: Any) -> dict:
    if not isinstance(value, dict):
        msg = f"`{value.__class__.__name__}` given (value = {value!r})."
        raise ValueError(f"`{name}` should be a dict. {msg}")
    return value


class CliParams(NamedTuple):
    plugins: List[types.Plugin]
    output_dir: Path = Path(".")
    main_file: str = "__init__.py"
    replacements: Mapping[str, str] = MappingProxyType({})
    loglevel: int = logging.WARNING


def parser_spec(plugins: Sequence[types.Plugin]) -> Dict[str, dict]:
    common = ("version", "enable", "disable", "verbose", "very_verbose")
    cli_spec = cli.__meta__(plugins)
    meta = {k: v.copy() for k, v in META.items()}
    meta.update({k: cli_spec[k].copy() for k in common})
    return meta


def run(args: Sequence[str] = ()):
    args = args or sys.argv[1:]
    plugins = list_plugins_from_entry_points()
    desc = 'Generate files for "vendoring" `validate-pyproject`'
    params = cli.parse_args(args, plugins, desc, parser_spec, CliParams)  # type: ignore
    cli.setup_logging(params.loglevel)
    vendorify(params.output_dir, params.main_file, params.plugins, params.replacements)
    return 0


main = cli.exceptisons2exit()(run)


if __name__ == "__main__":
    main()
