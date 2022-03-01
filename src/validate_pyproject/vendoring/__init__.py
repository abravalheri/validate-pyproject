import logging
import os
import sys
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Dict, Mapping, Optional, Sequence, Union

from .. import api, dist_name, types
from .._vendor import fastjsonschema as FJS

if sys.version_info[:2] >= (3, 8):  # pragma: no cover
    from importlib import metadata as _M
else:  # pragma: no cover
    import importlib_metadata as _M

if sys.version_info[:2] >= (3, 7):  # pragma: no cover
    from importlib import resources as _R
else:  # pragma: no cover
    import importlib_resources as _R

if TYPE_CHECKING:  # pragma: no cover
    from ..plugins import PluginWrapper  # noqa


_logger = logging.getLogger(__name__)


TEXT_REPLACEMENTS = MappingProxyType(
    {
        "from fastjsonschema import": "from .fastjsonschema_exceptions import",
        "from ._vendor.fastjsonschema import": "from .fastjsonschema_exceptions import",
    }
)


def vendorify(
    output_dir: Union[str, os.PathLike] = ".",
    main_file: str = "__init__.py",
    original_cmd: str = "",
    plugins: Union[api.AllPlugins, Sequence["PluginWrapper"]] = api.ALL_PLUGINS,
    text_replacements: Mapping[str, str] = TEXT_REPLACEMENTS,
) -> Path:
    """Populate the given ``output_dir`` with all files necessary to perform
    the validation.
    The validation can be performed by calling the ``validate`` function inside the
    the file named with the ``main_file`` value.
    ``text_replacements`` can be used to
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    replacements = {**TEXT_REPLACEMENTS, **text_replacements}

    validator = api.Validator(plugins)
    code = _compile_to_code(validator)
    code = replace_text(code, replacements)
    (out / "fastjsonschema_validations.py").write_text(code, "UTF-8")

    copy_fastjsonschema_exceptions(out, replacements)
    copy_module("extra_validations", out, replacements)
    copy_module("formats", out, replacements)
    write_main(out / main_file, validator.schema, replacements)
    write_notice(out, main_file, original_cmd, replacements)
    (out / "__init__.py").touch()

    return out


def _compile_to_code(validator: api.Validator):
    # This function is only needed while issue #129 of fastjsonschema is not solved
    # once it is solved we can use `fastjsonschema.compile_to_code` directly
    generator = validator._generator
    return (
        f'VERSION = "{FJS.VERSION}"\n'
        + f"{generator.global_state_code}\n"
        + generator.func_code
    )


def replace_text(text: str, replacements: Dict[str, str]) -> str:
    for orig, subst in replacements.items():
        text = text.replace(orig, subst)
    return text


def copy_fastjsonschema_exceptions(
    output_dir: Path, replacements: Dict[str, str]
) -> Path:
    file = output_dir / "fastjsonschema_exceptions.py"
    code = replace_text(api.read_text(FJS.__name__, "exceptions.py"), replacements)
    file.write_text(code, "UTF-8")
    return file


def copy_module(name: str, output_dir: Path, replacements: Dict[str, str]) -> Path:
    file = output_dir / f"{name}.py"
    code = api.read_text(api.__package__, f"{name}.py")
    code = replace_text(code, replacements)
    file.write_text(code, "UTF-8")
    return file


def write_main(
    file_path: Path, schema: types.Schema, replacements: Dict[str, str]
) -> Path:
    code = api.read_text(__name__, "main_file.template")
    code = replace_text(code, replacements)
    file_path.write_text(code, "UTF-8")
    return file_path


def write_notice(
    out: Path, main_file: str, cmd: str, replacements: Dict[str, str]
) -> Path:
    if cmd:
        opening = api.read_text(__name__, "cli-notice.template")
        opening = opening.format(command=cmd)
    else:
        opening = api.read_text(__name__, "api-notice.template")
    notice = api.read_text(__name__, "NOTICE.template")
    notice = notice.format(notice=opening, main_file=main_file, **load_licenses())
    notice = replace_text(notice, replacements)

    file = out / "NOTICE"
    file.write_text(notice, "UTF-8")
    return file


def load_licenses() -> Dict[str, str]:
    return {
        "fastjsonschema_license": _R.read_text(FJS, "LICENSE"),
        "validate_pyproject_license": _find_and_load_licence(_M.files(dist_name)),
    }


NOCHECK_HEADERS = (
    "# noqa",
    "# type: ignore",
    "# flake8: noqa",
    "# pylint: skip-file",
    "# mypy: ignore-errors",
    "# yapf: disable",
    "# pylama:skip=1",
    "\n\n# *** PLEASE DO NOT MODIFY DIRECTLY: Automatically generated code *** \n\n\n",
)


def _find_and_load_licence(files: Optional[Sequence[_M.PackagePath]]) -> str:
    if files is None:  # pragma: no cover
        raise ImportError("Could not find LICENSE for package")
    try:
        return next(f for f in files if f.stem.upper() == "LICENSE").read_text("UTF-8")
    except FileNotFoundError:  # pragma: no cover
        msg = (
            "Please make sure to install `validate-pyproject` and `fastjsonschema` "
            "in a NON-EDITABLE way. This is necessary due to the issue #112 in "
            "python/importlib_metadata."
        )
        _logger.warning(msg)
        raise
