import pytest

from validate_pyproject import api
from validate_pyproject.error_reporting import ValidationError
from validate_pyproject.extra_validations import _normalise_group_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("test", "test"),
        ("Test", "test"),
        ("Test.Tools", "test-tools"),
        ("test_tools", "test-tools"),
        ("test--tools", "test-tools"),
        ("Test.-_.Tools", "test-tools"),
        ("Friendly.Bard", "friendly-bard"),
    ],
)
def test_normalise_group_name(raw, expected):
    assert _normalise_group_name(raw) == expected


def _validator():
    return api.Validator(plugins=[])


@pytest.mark.parametrize(
    ("declared", "included"),
    [
        ("Test.Tools", "test_tools"),
        ("Test.Tools", "Test.Tools"),
        ("friendly.bard", "friendly_bard"),
        ("Alpha--Beta", "alpha.beta"),
        ("UPPER_case.Dot", "upper-case-dot"),
    ],
)
def test_include_group_normalised(declared, included):
    document = {
        "dependency-groups": {
            declared: ["pytest"],
            "dev": [{"include-group": included}],
        }
    }
    assert _validator()(document) is not None


@pytest.mark.parametrize("included", ["missing", "missing_group", "Test.Tools-extra"])
def test_include_group_missing_raises(included):
    document = {
        "dependency-groups": {
            "Test.Tools": ["pytest"],
            "dev": [{"include-group": included}],
        }
    }
    with pytest.raises(ValidationError) as exc_info:
        _validator()(document)
    message = str(exc_info.value)
    assert included in message
    assert "doesn't exist" in message
