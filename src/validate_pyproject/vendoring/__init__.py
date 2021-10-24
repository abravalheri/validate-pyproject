import logging
import os
import re
import sys
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Dict, Mapping, Optional, Sequence, Union

import fastjsonschema as FJS

from .. import api, dist_name, types

if sys.version_info[:2] >= (3, 8):  # pragma: no cover
    from importlib import metadata as _M
    from re import Pattern
else:  # pragma: no cover
    from typing import Pattern

    import importlib_metadata as _M

if TYPE_CHECKING:  # pragma: no cover
    from ..plugins import PluginWrapper  # noqa


_logger = logging.getLogger(__name__)


TEXT_REPLACEMENTS = MappingProxyType(
    {
        "from fastjsonschema import": "from .fastjsonschema_exceptions import",
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
    code = replace_text(_fix_generated_code(code), replacements)
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
    code = replace_text(api.read_text("fastjsonschema", "exceptions.py"), replacements)
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
        "fastjsonschema_license": _find_and_load_licence(_M.files("fastjsonschema")),
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
PICKLED_PATTERNS = r"^REGEX_PATTERNS = pickle.loads\((.*)\)$"
PICKLED_PATTERNS_REGEX = re.compile(PICKLED_PATTERNS, re.M)
VALIDATION_FN_DEF_PATTERN = r"^([\t ])*def\s*validate(_[\w_]+)?\(data\):"
VALIDATION_FN_DEF = re.compile(VALIDATION_FN_DEF_PATTERN, re.M | re.I)
VALIDATION_FN_CALL_PATTERN = r"(?!def\s+)\bvalidate([_\w]+)\(([_\w]+)\)"
VALIDATION_FN_CALL = re.compile(VALIDATION_FN_CALL_PATTERN, re.M | re.I)


def _fix_generated_code(code: str) -> str:
    # Currently fastjsonschema relies on a global variable for custom_formats,
    # but that is not compatible with creating a static file,
    # so we need to patch the compiled code and add a second argument for the function
    # definitions and function calls
    code = VALIDATION_FN_DEF.sub(r"\1def validate\2(data, custom_formats):", code)
    code = VALIDATION_FN_CALL.sub(r"validate\1(\2, custom_formats)", code)

    # Replace the pickled regexes with calls to `re.compile` (better to read)
    match = PICKLED_PATTERNS_REGEX.search(code)
    if match:
        import ast
        import pickle

        pickled_regexes = ast.literal_eval(match.group(1))
        regexes = pickle.loads(pickled_regexes).items()
        regexes_ = (f"{k!r}: {_repr_regex(v)}" for k, v in regexes)
        repr_ = "{\n    " + ",\n    ".join(regexes_) + "\n}"
        subst = f"REGEX_PATTERNS = {repr_}"
        code = code.replace(match.group(0), subst)
        code = code.replace("import re, pickle", "import re")

    return "\n".join(NOCHECK_HEADERS) + code


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


def _repr_regex(regex: Pattern) -> str:
    # Unfortunately using `pprint.pformat` is causing errors
    all_flags = ("A", "I", "DEBUG", "L", "M", "S", "X")
    flags = " | ".join(f"re.{f}" for f in all_flags if regex.flags & getattr(re, f))
    flags = ", " + flags if flags else ""
    return f"re.compile({regex.pattern!r}{flags})"
