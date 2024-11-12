import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent.resolve()
PROJECT = HERE.parent

sys.path.insert(0, str(PROJECT / "src"))  # <-- Use development version of library
logging.basicConfig(level=logging.DEBUG)

from validate_pyproject import caching, http  # noqa: E402

SCHEMA_STORE = "https://json.schemastore.org/pyproject.json"


def iter_test_urls():
    with caching.as_file(http.open_url, SCHEMA_STORE) as f:
        store = json.load(f)
        for _, tool in store["properties"]["tool"]["properties"].items():
            if "$ref" in tool and tool["$ref"].startswith(("http://", "https://")):
                yield tool["$ref"]

    files = PROJECT.glob("**/test_config.json")
    for file in files:
        content = json.loads(file.read_text("utf-8"))
        for _, url in content.get("tools", {}).items():
            if url.startswith(("http://", "https://")):
                yield url


def download(url):
    return caching.as_file(http.open_url, url).close()
    # ^-- side-effect only: write cached file


def download_all(cache: str):
    with ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(download, set(iter_test_urls())))  # Consume iterator


if __name__ == "__main__":
    cache = os.getenv("VALIDATE_PYPROJECT_CACHE_REMOTE")
    if not cache:
        raise SystemExit("Please define VALIDATE_PYPROJECT_CACHE_REMOTE")

    Path(cache).mkdir(parents=True, exist_ok=True)
    downloads = download_all(cache)
    assert len(downloads) > 0, f"empty {downloads=!r}"  # noqa
    files = list(map(print, Path(cache).iterdir()))
    assert len(files) > 0, f"empty {files=!r}"  # noqa
