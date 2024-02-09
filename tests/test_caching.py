import io
import os
from unittest.mock import Mock

import pytest

from validate_pyproject import caching, http, remote


@pytest.fixture(autouse=True)
def no_cache_env_var(monkeypatch):
    monkeypatch.delenv("VALIDATE_PYPROJECT_CACHE_REMOTE", raising=False)


def fn1(arg: str) -> io.StringIO:
    return io.StringIO("42")


def fn2(arg: str) -> io.StringIO:
    raise RuntimeError("should not be called")


def test_as_file(tmp_path):
    # The first call should create a file and return its contents
    cache_path = caching.path_for("hello-world", tmp_path)
    assert not cache_path.exists()

    with caching.as_file(fn1, "hello-world", tmp_path) as f:
        assert f.read() == b"42"

    assert cache_path.exists()
    assert cache_path.read_text("utf-8") == "42"

    # Any further calls using the same ``arg`` should reuse the file
    # and NOT call the function
    with caching.as_file(fn2, "hello-world", tmp_path) as f:
        assert f.read() == b"42"

    # If the file is deleted, then the function should be called
    cache_path.unlink()
    with pytest.raises(RuntimeError, match="should not be called"):
        caching.as_file(fn2, "hello-world", tmp_path)


def test_as_file_no_cache():
    # If no cache directory is passed, the orig function should
    # be called straight away:
    with pytest.raises(RuntimeError, match="should not be called"):
        caching.as_file(fn2, "hello-world")


def test_path_for_no_cache(monkeypatch):
    cache_path = caching.path_for("hello-world", None)
    assert cache_path is None


@pytest.mark.uses_network
@pytest.mark.skipif(
    os.getenv("VALIDATE_PYPROJECT_NO_NETWORK") or os.getenv("NO_NETWORK"),
    reason="Disable tests that depend on network",
)
class TestIntegration:
    def test_cache_open_url(self, tmp_path, monkeypatch):
        open_url = Mock(wraps=http.open_url)
        monkeypatch.setattr(http, "open_url", open_url)

        # The first time it is called, it will cache the results into a file
        url = (
            "https://raw.githubusercontent.com/abravalheri/validate-pyproject/main/"
            "src/validate_pyproject/pyproject_toml.schema.json"
        )
        cache_path = caching.path_for(url, tmp_path)
        assert not cache_path.exists()

        with caching.as_file(http.open_url, url, tmp_path) as f:
            assert b"build-system" in f.read()

        open_url.assert_called_once()
        assert cache_path.exists()
        assert "build-system" in cache_path.read_text("utf-8")

        # The second time, it will not reach the network, and use the file contents
        open_url.reset_mock()
        _, contents = remote.load_from_uri(url, cache_dir=tmp_path)

        assert "build-system" in contents["properties"]
        open_url.assert_not_called()
