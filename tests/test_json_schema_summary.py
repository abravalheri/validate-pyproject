"""Test summary generation from schema examples"""
import json
from pathlib import Path

import pytest

from validate_pyproject.error_reporting import _SummaryWriter

EXAMPLE_FOLDER = Path(__file__).parent / "json_schema_summary"
EXAMPLES = (p.name for p in EXAMPLE_FOLDER.glob("*"))


def load_example(file):
    text = file.read_text(encoding="utf-8")
    schema, _, summary = text.partition("# - # - # - #\n")

    # # Auto fix examples:
    # fixed = _SummaryWriter()(json.loads(schema))
    # file.write_text(text.replace(summary, fixed), encoding="utf-8")

    return json.loads(schema), summary


@pytest.mark.parametrize("example", EXAMPLES)
def test_summary_generation(example):
    schema, expected = load_example(EXAMPLE_FOLDER / example)
    summarize = _SummaryWriter()
    summary = summarize(schema)
    assert summary == expected
