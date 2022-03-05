import re
import shutil
import subprocess
import sys
from inspect import cleandoc
from itertools import product
from pathlib import Path

import pytest
import tomli
from validate_pyproject._vendor.fastjsonschema import JsonSchemaValueException

from validate_pyproject.vendoring import cli, vendorify

from .helpers import EXAMPLES, INVALID, error_file, examples, invalid_examples

MAIN_FILE = "hello_world.py"  # Let's use something different that `__init__.py`


def _vendoring_checks(path: Path):
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
        ("NOTICE", "The relevant copyright notes and licenses are included bellow"),
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

    # Make sure the vendored lib works
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


def test_vendoring_api(tmp_path):
    path = Path(tmp_path)
    vendorify(path, MAIN_FILE)
    _vendoring_checks(path)
    # Let's make sure it also works for __init__
    shutil.rmtree(str(path), ignore_errors=True)
    replacements = {"from fastjsonschema import": "from _vend.fastjsonschema import"}
    vendorify(path, text_replacements=replacements)
    assert "def validate(" in (path / "__init__.py").read_text()
    assert not (path / MAIN_FILE).exists()
    file_contents = (path / "fastjsonschema_validations.py").read_text()
    assert "from _vend" in file_contents
    assert "from fastjsonschema" not in file_contents


def test_vendoring_cli(tmp_path):
    path = Path(tmp_path)
    cli.run(["-O", str(path), "-M", MAIN_FILE])
    _vendoring_checks(Path(path))
    # Let's also try to test JSON replacements
    shutil.rmtree(str(path), ignore_errors=True)
    replacements = '{"from fastjsonschema import": "from _vend.fastjsonschema import"}'
    cli.run(["-O", str(path), "-R", replacements])
    file_contents = (path / "fastjsonschema_validations.py").read_text()
    assert "from _vend" in file_contents
    assert "from fastjsonschema" not in file_contents


# ---- Examples ----


VENDORED_NAME = "_vendored_validation"


def api_vendored(tmp_path) -> Path:
    return vendorify(Path(tmp_path / VENDORED_NAME))


def cli_vendored(tmp_path) -> Path:
    path = Path(tmp_path / VENDORED_NAME)
    cli.run(["-O", str(path)])
    return path


_VENDORING = (api_vendored, cli_vendored)


@pytest.fixture
def vendored_validate(monkeypatch):
    def _validate(vendored_path, toml_equivalent):
        assert VENDORED_NAME not in sys.modules
        with monkeypatch.context() as m:
            m.syspath_prepend(str(vendored_path.parent))
            mod = __import__(VENDORED_NAME)
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
                del sys.modules[VENDORED_NAME]

    return _validate


@pytest.mark.parametrize("example, vendored", product(examples(), _VENDORING))
def test_examples_api(tmp_path, vendored_validate, example, vendored):
    toml_equivalent = tomli.loads((EXAMPLES / example).read_text())
    vendored_path = vendored(Path(tmp_path))
    return vendored_validate(vendored_path, toml_equivalent) is not None


@pytest.mark.parametrize("example, vendored", product(invalid_examples(), _VENDORING))
def test_invalid_examples_api(tmp_path, vendored_validate, example, vendored):
    example_file = INVALID / example
    expected_error = error_file(example_file).read_text("utf-8")
    toml_equivalent = tomli.loads(example_file.read_text())
    vendored_path = vendored(Path(tmp_path))
    with pytest.raises(JsonSchemaValueException) as exc_info:
        vendored_validate(vendored_path, toml_equivalent)
    exception_message = str(exc_info.value)
    print("rule", "=", exc_info.value.rule)
    print("rule_definition", "=", exc_info.value.rule_definition)
    print("definition", "=", exc_info.value.definition)
    for error in expected_error.splitlines():
        assert error in exception_message
