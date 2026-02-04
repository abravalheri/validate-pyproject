from __future__ import annotations

import functools
import json
from pathlib import Path

from validate_pyproject.remote import RemotePlugin, load_store

HERE = Path(__file__).parent.resolve()


def error_file(p: Path) -> Path:
    try:
        files = (p.with_name("errors.txt"), p.with_suffix(".errors.txt"))
        return next(f for f in files if f.exists())
    except StopIteration:
        msg = f"No error file found for {p}"
        raise FileNotFoundError(msg) from None


def get_test_config(example: Path) -> dict[str, str | dict[str, str]]:
    test_config = example.with_name("test_config.json")
    if test_config.is_file():
        with test_config.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


@functools.cache
def get_tools(example: Path) -> list[RemotePlugin]:
    config = get_test_config(example)
    tools: dict[str, str] = config.get("tools", {})
    load_tools = [RemotePlugin.from_url(k, v) for k, v in tools.items()]
    store: str = config.get("store", "")
    if store:
        load_tools.extend(load_store(store))
    return load_tools


@functools.cache
def get_tools_as_args(example: Path) -> list[str]:
    config = get_test_config(example)
    tools: dict[str, str] = config.get("tools", {})
    load_tools = [f"--tool={k}={v}" for k, v in tools.items()]
    store: str = config.get("store", "")
    if store:
        load_tools.append(f"--store={store}")
    return load_tools
