import json
from pathlib import Path
from typing import Dict

HERE = Path(__file__).parent.resolve()


def error_file(p: Path) -> Path:
    try:
        files = (p.with_name("errors.txt"), p.with_suffix(".errors.txt"))
        return next(f for f in files if f.exists())
    except StopIteration:
        raise FileNotFoundError(f"No error file found for {p}") from None


def get_test_config(example: Path) -> Dict[str, str]:
    test_config = example.with_name("test_config.json")
    if test_config.is_file():
        with test_config.open(encoding="utf-8") as f:
            return json.load(f)
    return {}
