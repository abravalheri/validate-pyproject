from inspect import cleandoc

import pytest

from validate_pyproject.pretty_errors import _Formatter


def format(spec):
    return _Formatter()(spec)


@pytest.mark.parametrize(
    "example, expected",
    [
        ({"type": "array"}, "an array (list)"),
        (
            {"type": "array", "items": {"type": "number"}},
            """
            an array (list)
            - with any items in the form of:
              * a number value
            """,
        ),
        (
            {
                "type": "array",
                "items": {"type": "number"},
                "contains": {"type": "string", "pattern": "a*", "maxLength": 8},
            },
            """
            an array (list)
            - with any items in the form of:
              * a number value
            - with at least one item in the form of:
              * a string value (pattern: 'a*', max length: 8)
            """,
        ),
        (
            {
                "type": "array",
                "prefixItems": [
                    {"type": "number"},
                    {"type": "boolean"},
                ],
                "contains": {"type": "string", "pattern": "a*", "maxLength": 8},
                "minItems": 5,
                "uniqueItems": True,
            },
            """
            an array (list)
            - with the following items:
              * a number value
              * a boolean value
            - with at least one item in the form of:
              * a string value (pattern: 'a*', max length: 8)
            - min items: 5
            - unique items: True
            """,
        ),
    ],
)
def test_array(example, expected):
    formatted = format(example)
    expected = f"{cleandoc(expected)}\n"
    assert formatted == expected
