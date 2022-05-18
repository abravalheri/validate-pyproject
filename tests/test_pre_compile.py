import builtins
import re
import shutil
import subprocess
import sys
from inspect import cleandoc
from pathlib import Path

import pytest
from validate_pyproject._vendor.fastjsonschema import JsonSchemaValueException

from validate_pyproject.pre_compile import cli, pre_compile

from .helpers import EXAMPLES, INVALID, error_file, examples, invalid_examples, toml_

MAIN_FILE = "hello_world.py"  # Let's use something different that `__init__.py`


def _pre_compile_checks(path: Path):
    assert (path / "__init__.py").exists()
    assert (path / "__init__.py").read_text() == ""
    assert (path / MAIN_FILE).exists()
    files = [
        (MAIN_FILE, "def validate("),
        (MAIN_FILE, "from .error_reporting import detailed_errors, ValidationError"),
        ("error_reporting.py", "def detailed_errors("),
        ("fastjsonschema_exceptions.py", "class JsonSchemaValueException"),
        ("fastjsonschema_validations.py", "def validate("),
        ("extra_validations.py", "def validate"),
        ("formats.py", "def pep508("),
        ("NOTICE", "The relevant copyright notes and licenses are included below"),
    ]
    for file, content in files:
        assert (path / file).exists()
        assert content in (path / file).read_text()

    # Make sure standard replacements work
    for file in ("fastjsonschema_validations.py", "error_reporting.py"):
        file_contents = (path / file).read_text()
        assert "from fastjsonschema" not in file_contents
        assert "from ._vendor.fastjsonschema" not in file_contents
        assert "from validate_pyproject._vendor.fastjsonschema" not in file_contents
        assert "from .fastjsonschema_exceptions" in file_contents

    # Make sure the pre-compiled lib works
    script = f"""
    from {path.stem} import {Path(MAIN_FILE).stem} as mod

    assert issubclass(mod.ValidationError, mod.JsonSchemaValueException)

    example = {{
        "project": {{"name": "proj", "version": 42}}
    }}
    assert mod.validate(example) == example
    """
    cmd = [sys.executable, "-c", cleandoc(script)]
    error = r".project\.version. must be string"
    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        subprocess.check_output(cmd, cwd=path.parent, stderr=subprocess.STDOUT)

    assert re.search(error, str(exc_info.value.output, "utf-8"))


def test_pre_compile_api(tmp_path):
    path = Path(tmp_path)
    pre_compile(path, MAIN_FILE)
    _pre_compile_checks(path)
    # Let's make sure it also works for __init__
    shutil.rmtree(str(path), ignore_errors=True)
    replacements = {"from fastjsonschema import": "from _vend.fastjsonschema import"}
    pre_compile(path, text_replacements=replacements)
    assert "def validate(" in (path / "__init__.py").read_text()
    assert not (path / MAIN_FILE).exists()
    file_contents = (path / "fastjsonschema_validations.py").read_text()
    assert "from _vend" in file_contents
    assert "from fastjsonschema" not in file_contents


def test_vendoring_cli(tmp_path):
    path = Path(tmp_path)
    cli.run(["-O", str(path), "-M", MAIN_FILE])
    _pre_compile_checks(Path(path))
    # Let's also try to test JSON replacements
    shutil.rmtree(str(path), ignore_errors=True)
    replacements = '{"from fastjsonschema import": "from _vend.fastjsonschema import"}'
    cli.run(["-O", str(path), "-R", replacements])
    file_contents = (path / "fastjsonschema_validations.py").read_text()
    assert "from _vend" in file_contents
    assert "from fastjsonschema" not in file_contents


# ---- Examples ----


PRE_COMPILED_NAME = "_validation"


def api_pre_compile(tmp_path) -> Path:
    return pre_compile(Path(tmp_path / PRE_COMPILED_NAME))


def cli_pre_compile(tmp_path) -> Path:
    path = Path(tmp_path / PRE_COMPILED_NAME)
    cli.run(["-O", str(path)])
    return path


_PRE_COMPILED = (api_pre_compile, cli_pre_compile)


@pytest.fixture
def pre_compiled_validate(monkeypatch):
    def _validate(vendored_path, toml_equivalent):
        assert PRE_COMPILED_NAME not in sys.modules
        with monkeypatch.context() as m:
            # Make sure original imports are not used
            _disable_import(m, "fastjsonschema")
            _disable_import(m, "validate_pyproject")
            # Make newly generated package available for importing
            m.syspath_prepend(str(vendored_path.parent))
            mod = __import__(PRE_COMPILED_NAME)
            print(list(vendored_path.glob("*")))
            print(mod, "\n\n", dir(mod))
            try:
                return mod.validate(toml_equivalent)
            except mod.JsonSchemaValueException as ex:
                # Let's translate the exceptions so we have identical classes
                new_ex = JsonSchemaValueException(
                    ex.message, ex.value, ex.name, ex.definition, ex.rule
                )
                raise new_ex from ex
            finally:
                del sys.modules[PRE_COMPILED_NAME]

    return _validate


@pytest.mark.parametrize("example", examples())
@pytest.mark.parametrize("pre_compiled", _PRE_COMPILED)
def test_examples_api(tmp_path, pre_compiled_validate, example, pre_compiled):
    toml_equivalent = toml_.loads((EXAMPLES / example).read_text())
    pre_compiled_path = pre_compiled(Path(tmp_path))
    return pre_compiled_validate(pre_compiled_path, toml_equivalent) is not None


@pytest.mark.parametrize("example", invalid_examples())
@pytest.mark.parametrize("pre_compiled", _PRE_COMPILED)
def test_invalid_examples_api(tmp_path, pre_compiled_validate, example, pre_compiled):
    example_file = INVALID / example
    expected_error = error_file(example_file).read_text("utf-8")
    toml_equivalent = toml_.loads(example_file.read_text())
    pre_compiled_path = pre_compiled(Path(tmp_path))
    with pytest.raises(JsonSchemaValueException) as exc_info:
        pre_compiled_validate(pre_compiled_path, toml_equivalent)
    exception_message = str(exc_info.value)
    print("rule", "=", exc_info.value.rule)
    print("rule_definition", "=", exc_info.value.rule_definition)
    print("definition", "=", exc_info.value.definition)
    for error in expected_error.splitlines():
        assert error in exception_message


def _disable_import(monkeypatch, name):
    orig = builtins.__import__

    def _import(import_name, *args, **kwargs):
        if import_name == name or import_name.startswith(f"{name}."):
            raise ImportError(name)
        return orig(import_name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _import)
