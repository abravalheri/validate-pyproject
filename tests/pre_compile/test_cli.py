import traceback

import pytest

from validate_pyproject.pre_compile import cli


@pytest.mark.parametrize("replacements", ['["a", "b"]', "{invalid: json}"])
def test_invalid_replacements(tmp_path, replacements):
    with pytest.raises(SystemExit) as exc:
        cli.run(["-O", str(tmp_path), "-R", replacements])

    e = exc.value
    trace = "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
    assert "--replacements: invalid" in trace
    assert replacements in trace
