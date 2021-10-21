import logging
import sys
from typing import Dict, List, NamedTuple, Sequence

import fastjsonschema as FJS

from . import api, cli, types
from .plugins import list_from_entry_points as list_plugins_from_entry_points

_logger = logging.getLogger(__package__)

META: Dict[str, dict] = {}


class CliParams(NamedTuple):
    plugins: List[types.Plugin]
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
    params = cli.parse_args(args, plugins, parser_spec, CliParams)
    cli.setup_logging(params.loglevel)
    validator = api.Validator(plugins=params.plugins)
    code = FJS.compile_to_code(validator.schema, validator.handlers, validator.formats)
    print(code)
    return 0


main = cli.exceptisons2exit()(run)


if __name__ == "__main__":
    main()
