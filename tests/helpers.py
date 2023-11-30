import functools
import json
from pathlib import Path
from typing import Dict, List, Union

from validate_pyproject.remote import RemotePlugin, load_store

HERE = Path(__file__).parent.resolve()


def error_file(p: Path) -> Path:
    try:
        files = (p.with_name("errors.txt"), p.with_suffix(".errors.txt"))
        return next(f for f in files if f.exists())
    except StopIteration:
        raise FileNotFoundError(f"No error file found for {p}") from None


def get_test_config(example: Path) -> Dict[str, Union[str, Dict[str, str]]]:
    test_config = example.with_name("test_config.json")
    if test_config.is_file():
        with test_config.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


@functools.lru_cache(maxsize=None)
def get_tools(example: Path) -> List[RemotePlugin]:
    config = get_test_config(example)
    tools: Dict[str, str] = config.get("tools", {})
    load_tools = [RemotePlugin.from_url(k, v) for k, v in tools.items()]
    store: str = config.get("store", "")
    if store:
        load_tools.extend(load_store(store))
    return load_tools


@functools.lru_cache(maxsize=None)
def get_tools_as_args(example: Path) -> List[str]:
    config = get_test_config(example)
    tools: Dict[str, str] = config.get("tools", {})
    load_tools = [f"--tool={k}={v}" for k, v in tools.items()]
    store: str = config.get("store", "")
    if store:
        load_tools.append(f"--store={store}")
    return load_tools
