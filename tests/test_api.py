from validate_pyproject import api


def test_load():
    spec = api.load("pep517_518")
    assert isinstance(spec, dict)
    assert spec["$id"] == "https://www.python.org/dev/peps/pep-0517/"

    spec = api.load("pep621_project")
    assert spec["$id"] == "https://www.python.org/dev/peps/pep-0621/"
