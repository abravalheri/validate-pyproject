import os
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Mapping, Sequence, Union

import fastjsonschema as FJS

from .. import api, types

TEXT_REPLACEMENTS = MappingProxyType(
    {
        "from fastjsonschema import": "from .fastjsonschema_exceptions import",
    }
)


def vendorify(
    output_dir: Union[str, os.PathLike] = ".",
    main_file: str = "__init__.py",
    plugins: Union[api.AllPlugins, Sequence[types.Plugin]] = api.ALL_PLUGINS,
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
    code = FJS.compile_to_code(validator.schema, validator.handlers, validator.formats)
    code = replace_text(code, replacements)
    (out / "fastjsonschema_validate.py").write_text(code, "UTF-8")

    write_fastjsonschema_exceptions(out, replacements)
    write_main(out / main_file, validator.schema, replacements)
    write_notice(out, replacements)

    return out


def replace_text(text: str, replacements: Dict[str, str]) -> str:
    for orig, subst in replacements.items():
        if subst != orig:
            text = text.replace(orig, subst)
    return text


def write_fastjsonschema_exceptions(
    output_dir: Path, replacements: Dict[str, str]
) -> Path:
    file = output_dir / "fastjsonschema_exceptions.py"
    code = replace_text(api.read_text("fastjsonschema", "exceptisons.py"), replacements)
    file.write_text(code, "UTF-8")
    return file


def write_extra_validations(output_dir: Path, replacements: Dict[str, str]) -> Path:
    file = output_dir / "extra_validations.py"
    code = api.read_text(api.__package__, "extra_validations.py")
    code = replace_text(code, replacements)
    file.write_text(code, "UTF-8")
    return file


def write_main(
    file_path: Path, schema: types.Schema, replacements: Dict[str, str]
) -> Path:
    file_path.touch()
    # TODO write from template
    return file_path


def write_notice(out: Path, replacements: Dict[str, str]) -> Path:
    file = out / "NOTICE"
    # TODO write from template
    return file
