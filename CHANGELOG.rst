=========
Changelog
=========

..
   Development Version
   ====================

Version 0.21
============
* Added support PEP 735, #208
* Added support PEP 639, #210
* Renamed ``testing`` extra to ``test``, #212
* General updates in CI setup

Version 0.20
============
- ``setuptools`` plugin:
   * Update ``setuptools.schema.json``, #206

Maintenance and Minor Changes
-----------------------------
- Fix misplaced comments on ``formats.py``, #184
- Adopt ``--import-mode=importlib`` for pytest to prevent errors with ``importlib.metadata``, #203
- Update CI configs, #195 #202, #204, #205

Version 0.19
============
- Relax requirements about module names to also allow dash characters, #164
- Migrate metadata to ``pyproject.toml`` , #192

Version 0.18
============
- Allow overwriting schemas referring to the same ``tool``, #175

Version 0.17
============
- Update version regex according to latest packaging version, #153
- Remove duplicate ``# ruff: noqa``, #158
- Remove invalid top-of-the-file ``# type: ignore`` statement, #159
- Align ``tool.setuptools.dynamic.optional-dependencies`` with ``project.optional-dependencies``, #170
- Bump min Python version to 3.8, #167

Version 0.16
============
- Fix setuptools ``readme`` field , #116
- Fix ``oneOf <> anyOf`` in setuptools schema, #117
- Add previously omitted type keywords for string values, #117
- Add schema validator check, #118
- Add ``SchemaStore`` conversion script, #119
- Allow tool(s) to be specified via URL (added CLI option: ``--tool``), #121
- Support ``uint`` formats (as used by Ruff's schema), #128
- Allow schemas to be loaded from ``SchemaStore`` (added CLI option: ``--store``), #133

Version 0.15
============
- Update ``setuptools`` schema definitions, #112
- Add ``__repr__`` to plugin wrapper, by @henryiii #114
- Fix standard ``$schema`` ending ``#``, by @henryiii #113

Version 0.14
============

- Ensure reporting show more detailed error messages for ``RedefiningStaticFieldAsDynamic``, #104
- Add support for ``repo-review``, by @henryiii in #105

Version 0.13
============

- Make it clear when using input from ``stdin``, #96
- Fix summary for ``allOf``, #100
- ``setuptools`` plugin:
    - Improve validation of ``attr`` directives, #101

Version 0.12.2
==============

- ``setuptools`` plugin:
    - Fix problem with ``license-files`` patterns,
      by removing ``default`` value.

Version 0.12.1
==============

- ``setuptools`` plugin:
    - Allow PEP 561 stub names in ``tool.setuptools.package-dir``, #87

Version 0.12
============

- ``setuptools`` plugin:
    - Allow PEP 561 stub names in ``tool.setuptools.packages``, #86

Version 0.11
============

- Improve error message for invalid replacements in the ``pre_compile`` CLI, #71
- Allow package to be build from git archive, #53
- Improve error message for invalid replacements in the ``pre_compile`` CLI, #71
- Error-out when extra keys are added to ``project.authors/maintainers``, #82
- De-vendor ``fastjsonschema``, #83

Version 0.10.1
==============

- Ensure ``LICENSE.txt`` is added to wheel.

Version 0.10
============

- Add ``NOTICE.txt`` to ``license_files``, #58
- Use default SSL context when downloading classifiers from PyPI, #57
- Remove ``setup.py``, #52
- Explicitly limit oldest supported Python version
- Replace usage of ``cgi.parse_header`` with ``email.message.Message``

Version 0.9
===========

- Use ``tomllib`` from the standard library in Python 3.11+, #42

Version 0.8.1
=============

- Workaround typecheck inconsistencies between different Python versions
- Publish :pep:`561` type hints, #43

Version 0.8
===========

- New :pypi:`pre-commit` hook, #40
- Allow multiple TOML files to be validated at once via **CLI**
  (*no changes regarding the Python API*).

Version 0.7.2
=============

- ``setuptools`` plugin:
    - Allow ``dependencies``/``optional-dependencies`` to use file directives, #37

Version 0.7.1
=============

- CI: Enforced doctests
- CI: Add more tests for situations when downloading classifiers is disabled

Version 0.7
===========

- **Deprecated** use of ``validate_pyproject.vendoring``.
  This module is replaced by ``validate_pyproject.pre_compile``.

Version 0.6.1
=============

- Fix validation of ``version`` to ensure it is given either statically or dynamically, #29

Version 0.6
=============

- Allow private classifiers, #26
- ``setuptools`` plugin:
   - Remove ``license`` and ``license-files`` from ``tool.setuptools.dynamic``, #27

Version 0.5.2
=============

- Exported ``ValidationError`` from the main file when vendored, :pr:`23`
- Removed ``ValidationError`` traceback to avoid polluting the user logs with generate code, :pr:`24`

Version 0.5.1
=============

- Fixed typecheck errors (only found against GitHub Actions, not Cirrus CI), :pr:`22`

Version 0.5
===========

- Fixed entry-points format to allow values without the ``:obj.attr part``, :pr:`8`
- Improved trove-classifier validation, even when the package is not installed, :pr:`9`
- Improved URL validation when scheme prefix is not present, :pr:`14`
- Vendor :pypi:`fastjsonschema` to facilitate applying patches and latest updates, :pr:`15`
- Remove fixes for old version of :pypi:`fastjsonschema`, :pr:`16`, :pr:`19`
- Replaced usage of :mod:`importlib.resources` legacy functions with the new API, :pr:`17`
- Improved error messages, :pr:`18`
- Added GitHub Actions for automatic test and release of tags, :pr:`11`

Version 0.4
===========

- Validation now fails when non-standardised fields to be added to the
  project table (:issue:`4`, :pr:`5`)
- Terminology and schema names were also updated to avoid specific PEP numbers
  and refer instead to living standards (:issue:`6`, :pr:`7`)

Version 0.3.3
=============

- Remove upper pin from the :pypi:`tomli` dependency by :user:`hukkin` (:pr:`1`)
- Fix failing :pypi:`blacken-docs` pre-commit hook by :user:`hukkin` (:pr:`2`)
- Update versions of tools and containers used in the CI setup (:pr:`3`)

Version 0.3.2
=============

- Updated ``fastjsonschema`` dependency version.
- Removed workarounds for ``fastjsonschema``  pre 2.15.2

Version 0.3.1
=============

- ``setuptools`` plugin:
   - Fixed missing ``required`` properties for the ``attr:`` and ``file:``
     directives (previously empty objects were allowed).

Version 0.3
===========

- ``setuptools`` plugin:
   - Added support for ``readme``, ``license`` and ``license-files`` via ``dynamic``.

     .. warning::
         ``license`` and ``license-files`` in ``dynamic`` are **PROVISIONAL**
         they are likely to change depending on :pep:`639`

   - Removed support for ``tool.setuptools.dynamic.{scripts,gui-scripts}``.
     Dynamic values for ``project.{scripts,gui-scripts}`` are expected to be
     dynamically derived from ``tool.setuptools.dynamic.entry-points``.

Version 0.2
===========

- ``setuptools`` plugin:
   - Added ``cmdclass`` support

Version 0.1
===========

- ``setuptools`` plugin:
   - Added ``data-files``  support (although this option is marked as deprecated).
   - Unified ``tool.setuptools.packages.find`` and ``tool.setuptools.packages.find-namespace``
     options by adding a new keyword ``namespaces``
   - ``tool.setuptools.packages.find.where`` now accepts a list of directories
     (previously only one directory was accepted).

Version 0.0.1
=============

- Initial release with basic functionality
