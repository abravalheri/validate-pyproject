=========
Changelog
=========

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
