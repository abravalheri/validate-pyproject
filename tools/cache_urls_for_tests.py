import json
import logging
import os
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent.resolve()
PROJECT = HERE.parent

sys.path.insert(0, str(PROJECT / "src"))  # <-- Use development version of library
logging.basicConfig(level=logging.DEBUG)

from validate_pyproject import caching, http  # noqa: E402

SCHEMA_STORE = "https://json.schemastore.org/pyproject.json"


def _iter_nested_refs(base_url: str):
    """Yield nested $ref URLs found inside a schema's properties."""
    with caching.as_file(http.open_url, base_url) as f:
        try:
            schema = json.load(f)
        except json.JSONDecodeError:
            return
    for values in schema.get("properties", {}).values():
        ref_url = values.get("$ref", "")
        if ref_url:
            nested = urllib.parse.urljoin(base_url, ref_url)
            if nested.startswith(("http://", "https://")):
                yield nested


def iter_test_urls():
    with caching.as_file(http.open_url, SCHEMA_STORE) as f:
        store = json.load(f)
        for tool in store["properties"]["tool"]["properties"].values():
            if "$ref" in tool:
                url = urllib.parse.urljoin(SCHEMA_STORE, tool["$ref"])
                if url.startswith(("http://", "https://")):
                    yield url
                    yield from _iter_nested_refs(url)
    files = PROJECT.glob("**/test_config.json")
    for file in files:
        content = json.loads(file.read_text("utf-8"))
        for url in content.get("tools", {}).values():
            if url.startswith(("http://", "https://")):
                yield url


def download(url):
    return caching.as_file(http.open_url, url).close()
    # ^-- side-effect only: write cached file


def download_all(cache: str):  # noqa: ARG001
    with ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(download, set(iter_test_urls())))  # Consume iterator


if __name__ == "__main__":
    cache = os.getenv("VALIDATE_PYPROJECT_CACHE_REMOTE")
    if not cache:
        msg = "Please define VALIDATE_PYPROJECT_CACHE_REMOTE"
        raise SystemExit(msg)

    Path(cache).mkdir(parents=True, exist_ok=True)
    downloads = download_all(cache)
    assert len(downloads) > 0, f"empty {downloads=!r}"
    files = list(map(print, Path(cache).iterdir()))
    assert len(files) > 0, f"empty {files=!r}"
