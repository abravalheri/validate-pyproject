import logging
from inspect import cleandoc

import pytest
from validate_pyproject._vendor.fastjsonschema import validate

from validate_pyproject.api import FORMAT_FUNCTIONS
from validate_pyproject.error_reporting import ValidationError, detailed_errors

EXAMPLES = {
    "const": {
        "schema": {"const": 42},
        "value": 13,
        "message": "`data` must be 42",
        "debug_info": "**SKIP-TEST**",
    },
    "container": {
        "schema": {"type": "array", "contains": True},
        "value": [],
        "message": "`data` must not be empty",
        "debug_info": "**SKIP-TEST**",
    },
    "type": {
        "schema": {"anyOf": [{"not": {"type": ["string", "number"]}}]},
        "value": 42,
        "message": """
            `data` cannot be validated by any definition:

                - (*NOT* the following):
                    type: [string, number]
        """,
        "debug_info": "**SKIP-TEST**",
    },
    "oneOf": {
        "schema": {
            "oneOf": [{"type": "string", "format": "pep440"}, {"type": "integer"}]
        },
        "value": {"use_scm": True},
        "message": """
            `data` must be valid exactly by one definition (0 matches found):

                - {type: string, format: 'pep440'}
                - {type: integer}
        """,
        "debug_info": """
            GIVEN VALUE:
                {
                    "use_scm": true
                }

            OFFENDING RULE: 'oneOf'

            DEFINITION:
                {
                    "oneOf": [
                        {
                            "type": "string",
                            "format": "pep440"
                        },
                        {
                            "type": "integer"
                        }
                    ]
                }
        """,
    },
    "description": {
        "schema": {"type": "string", "description": "Lorem ipsum dolor sit amet"},
        "value": {"name": 42},
        "message": "`data` must be string",
        "debug_info": """
            DESCRIPTION:
                Lorem ipsum dolor sit amet
        """,
    },
    "$$description": {
        "schema": {
            "properties": {
                "name": {
                    "type": "string",
                    "$$description": [
                        "Lorem ipsum dolor sit amet, consectetur adipiscing elit,",
                        "sed do eiusmod tempor incididunt ut labore et dolore magna",
                        "aliqua. Ut enim ad minim veniam, quis nostrud exercitation",
                        "ullamco laboris nisi ut aliquip ex ea commodo consequat.",
                    ],
                }
            }
        },
        "value": {"name": 42},
        "message": "`name` must be string",
        "debug_info": """
            DESCRIPTION:
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
                tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
                quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
                consequat.

            GIVEN VALUE:
                42

            OFFENDING RULE: 'type'

            DEFINITION:
                {
                    "type": "string"
                }
        """,  # noqa
    },
}


@pytest.mark.parametrize("example", EXAMPLES.keys())
def test_error_reporting(caplog, example):
    schema = EXAMPLES[example]["schema"]
    value = EXAMPLES[example]["value"]
    message = cleandoc(EXAMPLES[example]["message"])
    debug_info = cleandoc(EXAMPLES[example]["debug_info"])

    try:
        with caplog.at_level(logging.CRITICAL), detailed_errors():
            validate(schema, value, formats=FORMAT_FUNCTIONS)
    except ValidationError as ex:
        assert ex.message.strip() == message
        assert ex.message == ex.summary
        assert "GIVEN VALUE:" in ex.details
        assert "DEFINITION:" in ex.details

    try:
        with caplog.at_level(logging.DEBUG), detailed_errors():
            validate(schema, value, formats=FORMAT_FUNCTIONS)
    except ValidationError as ex:
        assert "GIVEN VALUE:" in ex.message
        assert "DEFINITION:" in ex.message
        assert ex.summary in ex.message
        if debug_info != "**SKIP-TEST**":
            assert debug_info in ex.details
