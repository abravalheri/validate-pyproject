=======
Schemas
=======

The following sections represent the schemas used in ``validate-pyproject``.
You can also have a look on the raw JSON files in :doc:`json-schemas`.

.. _pyproject.toml:
.. jsonschema:: ../src/validate_pyproject/pep517_518.schema.json


.. _project_table:
.. jsonschema:: ../src/validate_pyproject/pep621_project.schema.json


``tool`` table
==============

According to PEP 518, tools can define their own configuration inside
``pyproject.toml`` by using custom subtables under ``tool``.

In ``validate-pyproject``, schemas for these subtables can be specified
via plugins. The following subtables are defined by *built-in* plugins (i.e.
plugins that are included in the default distribution of
``validate-pyproject``):

.. _tool.setuptools:
.. jsonschema:: ../src/validate_pyproject/plugins/setuptools.schema.json