import logging
from itertools import chain

import pytest

from validate_pyproject import formats

_chain_iter = chain.from_iterable

# The following examples were taken by inspecting some opensource projects in the python
# community
ENTRYPOINT_EXAMPLES = {
    "django": {
        "console_scripts": {
            "django-admin": "django.core.management:execute_from_command_line"
        }
    },
    "pandas": {
        "pandas_plotting_backends": {"matplotlib": "pandas:plotting._matplotlib"},
    },
    "PyScaffold": {
        "console_scripts": {"putup": "pyscaffold.cli:run"},
        "pyscaffold.cli": {
            "config": "pyscaffold.extensions.config:Config",
            "interactive": "pyscaffold.extensions.interactive:Interactive",
            "venv": "pyscaffold.extensions.venv:Venv",
            "namespace": "pyscaffold.extensions.namespace:Namespace",
            "no_skeleton": "pyscaffold.extensions.no_skeleton:NoSkeleton",
            "pre_commit": "pyscaffold.extensions.pre_commit:PreCommit",
            "no_tox": "pyscaffold.extensions.no_tox:NoTox",
            "gitlab": "pyscaffold.extensions.gitlab_ci:GitLab",
            "cirrus": "pyscaffold.extensions.cirrus:Cirrus",
            "no_pyproject": "pyscaffold.extensions.no_pyproject:NoPyProject",
        },
    },
    "setuptools-scm": {
        "distutils.setup_keywords": {
            "use_scm_version": "setuptools_scm.integration:version_keyword",
        },
        "setuptools.file_finders": {
            "setuptools_scm": "setuptools_scm.integration:find_files",
        },
        "setuptools.finalize_distribution_options": {
            "setuptools_scm": "setuptools_scm.integration:infer_version",
        },
        "setuptools_scm.files_command": {
            ".hg": "setuptools_scm.file_finder_hg:hg_find_files",
            ".git": "setuptools_scm.file_finder_git:git_find_files",
        },
        "setuptools_scm.local_scheme": {
            "node-and-date": "setuptools_scm.version:get_local_node_and_date",
            "node-and-timestamp": "setuptools_scm.version:get_local_node_and_timestamp",
            "dirty-tag": "setuptools_scm.version:get_local_dirty_tag",
            "no-local-version": "setuptools_scm.version:get_no_local_node",
        },
        "setuptools_scm.parse_scm": {
            ".hg": "setuptools_scm.hg:parse",
            ".git": "setuptools_scm.git:parse",
        },
        "setuptools_scm.parse_scm_fallback": {
            ".hg_archival.txt": "setuptools_scm.hg:parse_archival",
            "PKG-INFO": "setuptools_scm.hacks:parse_pkginfo",
            "pip-egg-info": "setuptools_scm.hacks:parse_pip_egg_info",
            "setup.py": "setuptools_scm.hacks:fallback_version",
        },
        "setuptools_scm.version_scheme": {
            "guess-next-dev": "setuptools_scm.version:guess_next_dev_version",
            "post-release": "setuptools_scm.version:postrelease_version",
            "python-simplified-semver": "setuptools_scm.version:simplified_semver_version",  # noqa
            "release-branch-semver": "setuptools_scm.version:release_branch_semver_version",  # noqa
            "no-guess-dev": "setuptools_scm.version:no_guess_dev_version",
            "calver-by-date": "setuptools_scm.version:calver_by_date",
        },
    },
}


@pytest.mark.parametrize(
    "example", _chain_iter(v.keys() for v in ENTRYPOINT_EXAMPLES.values())
)
def test_entrypoint_group(example):
    assert formats.python_entrypoint_group(example)


@pytest.mark.parametrize(
    "example",
    _chain_iter(
        _chain_iter(e.keys() for e in v.values()) for v in ENTRYPOINT_EXAMPLES.values()
    ),
)
def test_entrypoint_name(example):
    assert formats.python_entrypoint_name(example)


@pytest.mark.parametrize("example", [" invalid", "=invalid", "[invalid]", "[invalid"])
def test_entrypoint_invalid_name(example):
    assert formats.python_entrypoint_name(example) is False


@pytest.mark.parametrize("example", ["val[id", "also valid"])
def test_entrypoint_name_not_recommended(example, caplog):
    caplog.set_level(logging.WARNING)
    assert formats.python_entrypoint_name(example) is True
    assert "does not follow recommended pattern" in caplog.text


@pytest.mark.parametrize(
    "example",
    _chain_iter(
        _chain_iter(e.values() for e in v.values())
        for v in ENTRYPOINT_EXAMPLES.values()
    ),
)
def test_entrypoint_references(example):
    assert formats.python_entrypoint_reference(example)
    assert formats.pep517_backend_reference(example)
    assert formats.pep517_backend_reference(example.replace(":", "."))


def test_entrypoint_references_with_extras():
    example = "test.module:func [invalid"
    assert formats.python_entrypoint_reference(example) is False

    example = "test.module:func [valid]"
    assert formats.python_entrypoint_reference(example)
    assert formats.pep517_backend_reference(example) is False

    example = "test.module:func [valid, extras]"
    assert formats.python_entrypoint_reference(example)

    example = "test.module:func [??inva#%@!lid??]"
    assert formats.python_entrypoint_reference(example) is False


@pytest.mark.parametrize("example", ["module" "invalid-module"])
def test_invalid_entrypoint_references(example):
    assert formats.python_entrypoint_reference(example) is False


@pytest.mark.parametrize("example", ["λ", "a", "_"])
def test_valid_python_identifier(example):
    assert formats.python_identifier(example)


@pytest.mark.parametrize("example", ["a.b", "x+y", " a", "☺"])
def test_invalid_python_identifier(example):
    assert formats.python_identifier(example) is False


@pytest.mark.parametrize(
    "example",
    [
        "0.9.10",
        "1988.12",
        "1.01rc1",
        "0.99a9",
        "3.14b5",
        "1.42.post0",
        "1.73a2.post0",
        "2.23.post6.dev0",
        "3!6.0",
        "1.0+abc.7",
        "v4.0.1",
    ],
)
def test_valid_pep440(example):
    assert formats.pep440(example)


@pytest.mark.parametrize(
    "example",
    [
        "0-9-10",
        "v4.0.1.mysuffix",
        "p4.0.2",
    ],
)
def test_invalid_pep440(example):
    assert formats.pep440(example) is False


@pytest.mark.parametrize(
    "example",
    [
        "~= 0.9, >= 1.0, != 1.3.4.*, < 2.0",
        ">= 1.4.5, == 1.4.*",
        "~= 2.2.post3",
        "!= 1.1.post1",
    ],
)
def test_valid_pep508_versionspec(example):
    assert formats.pep508_versionspec(example)


@pytest.mark.parametrize(
    "example",
    [
        "~ 0.9, ~> 1.0, - 1.3.4.*",
        "- 1.3.4.*",
        "~> 1.0",
        "~ 0.9",
        "@ file:///localbuilds/pip-1.3.1.zip",
        'v1.0; python_version<"2.7"',
    ],
)
def test_invalid_pep508_versionspec(example):
    assert formats.pep508_versionspec(example) is False


@pytest.mark.parametrize(
    "example",
    [
        "https://python.org",
        "http://python.org",
        "http://localhost:8000",
        "ftp://python.org",
        "scheme://netloc/path;parameters?query#fragment",
    ],
)
def test_valid_url(example):
    assert formats.url(example)


@pytest.mark.parametrize(
    "example",
    [
        "",
        42,
        "p@python.org",
        "python.org",
        "http:python.org",
        "/python.org",
    ],
)
def test_invalid_url(example):
    assert formats.url(example) is False


@pytest.mark.parametrize(
    "example",
    [
        "ab",
        "ab.c.d",
        "abc._d.λ",
    ],
)
def test_valid_module_name(example):
    assert formats.python_module_name(example) is True


@pytest.mark.parametrize(
    "example",
    [
        "-",
        " ",
        "ab-cd",
        ".example",
    ],
)
def test_invalid_module_name(example):
    assert formats.python_module_name(example) is False
