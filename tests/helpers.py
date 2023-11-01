from pathlib import Path

HERE = Path(__file__).parent.resolve()


def error_file(p: Path) -> Path:
    try:
        files = (p.with_name("errors.txt"), p.with_suffix(".errors.txt"))
        return next(f for f in files if f.exists())
    except StopIteration:
        raise FileNotFoundError(f"No error file found for {p}") from None
