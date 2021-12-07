=========
Changelog
=========

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
