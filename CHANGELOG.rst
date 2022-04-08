=========
Changelog
=========

Version 0.7.2
=============

- ``setuptools`` plugin:
    - Allow ``dependencies``/``optional-dependencies`` to use file directives (#37)

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
