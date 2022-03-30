import pytest

from validate_pyproject.vendoring import cli, vendorify


def test_api(tmp_path):
    with pytest.warns(DeprecationWarning, match="will be removed"):
        vendorify(tmp_path)


def test_cli(tmp_path):
    with pytest.warns(DeprecationWarning, match="will be removed"):
        cli.run(["-O", str(tmp_path)])


def test_main(tmp_path):
    with pytest.warns(DeprecationWarning, match="will be removed"):
        cli.main(["-O", str(tmp_path)])
