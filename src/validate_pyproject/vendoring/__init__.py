import logging
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Sequence

import fastjsonschema as FJS

from . import api, cli, types
from .plugins import list_from_entry_points as list_plugins_from_entry_points

_logger = logging.getLogger(__package__)

META: Dict[str, dict] = {
    "output_dir": dict(
        flags=("-o", "--output-dir"),
        default=".",
        type=Path,
        help="Path to the directory where the files for embedding will be generated",
    ),
}


class CliParams(NamedTuple):
    plugins: List[types.Plugin]
    loglevel: int = logging.WARNING
    output_dir: Path = Path(".")


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
    validator = api.Validator(plugins=params.plugins)
    code = FJS.compile_to_code(validator.schema, validator.handlers, validator.formats)
    print(code)
    return 0


main = cli.exceptisons2exit()(run)


if __name__ == "__main__":
    main()
