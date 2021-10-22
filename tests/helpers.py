from pathlib import Path

HERE = Path(__file__).parent
EXAMPLES = HERE / "examples"
INVALID = HERE / "invalid-examples"


def examples():
    return [str(f.relative_to(EXAMPLES)) for f in EXAMPLES.glob("**/*.toml")]


def invalid_examples():
    return [str(f.relative_to(INVALID)) for f in INVALID.glob("**/*.toml")]


def error_file(p: Path) -> Path:
    try:
        files = (p.with_name("errors.txt"), p.with_suffix(".errors.txt"))
        return next(f for f in files if f.exists())
    except StopIteration:
        raise FileNotFoundError(f"No error file found for {p}")
