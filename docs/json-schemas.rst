:orphan:

============
JSON Schemas
============

The following JSON schemas are used in ``validate-pyproject``.

``pyproject.toml``
==================

.. literalinclude:: ../src/validate_pyproject/pep517_518.schema.json

``project`` table
=================

.. literalinclude:: ../src/validate_pyproject/pep621_project.schema.json

``tool`` table
==============

``tool.setuptools``
-------------------

.. literalinclude:: ../src/validate_pyproject/plugins/setuptools.schema.json
