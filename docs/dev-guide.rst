.. _dev-guide:

===============
Developer Guide
===============

This document describes the internal architecture and main concepts behind
``validate-pyproject`` and targets contributors and plugin writers.


.. _how-it-works:

How it works
============

``validate-pyproject`` relies mostly on a set of :doc:`specification documents
<json-schemas>` represented as `JSON Schema`_.
To run the checks encoded under these schema files ``validate-pyproject``
uses the :pypi:`fastjsonschema` package.

This procedure is defined in the :mod:`~validate_pyproject.api` module,
specifically under the :class:`~validate_pyproject.api.Validator` class.
:class:`~validate_pyproject.api.Validator` objects use
:class:`~validate_pyproject.api.SchemaRegistry` instances to store references
to the JSON schema documents being used for the validation.
The :mod:`~validate_pyproject.formats` module is also important to this
process, since it defines how to validate the custom values for the
``"format"`` field defined in JSON Schema, for ``"string"`` values.

Checks for :pep:`517`, :pep:`518` and :pep:`621` are performed by default,
however these standards do not specify how the ``tool`` table and its subtables
are populated.

Since different tools allow different configurations, it would be impractical
to try to create schemas for all of them inside the same project.
Instead, ``validate-pyproject`` allows :ref:`plugins` to provide extra JSON Schemas,
against which ``tool`` subtables can be checked.


.. _plugins:

Plugins
=======

Plugins are a way of extending the built-in functionality of
``validate-pyproject``, can be simply described as functions that return
a JSON schema parsed as a Python :obj:`dict`:

.. code-block:: python

   def plugin(tool_name: str) -> dict:
       ...

These functions receive as argument the name of the tool subtable and should
return a JSON schema for the data structure **under** this table (it **should**
not include the table name itself as a property).

To use a plugin you can pass a ``plugins`` argument to the
:class:`~validate_pyproject.api.Validator` constructor, but you will need to
wrap it with :class:`~validate_pyproject.plugins.PluginWrapper` to be able to
specify which ``tool`` subtable it would be checking:

.. code-block:: python

    from validate_pyproject import api, plugins


    def your_plugin(tool_name: str) -> dict:
        return {
            "$id": "https://your-urn-or-url",  # $id is mandatory
            "type": "object",
            "description": "Your tool configuration description",
            "properties": {
                "your-config-field": {"type": "string", "format": "python-module-name"}
            },
        }


    available_plugins = [
        *plugins.list_from_entry_points(),
        plugins.PluginWrapper("your-tool", your_plugin),
    ]
    validator = api.Validator(available_plugins)

Please notice that you can also make your plugin "autoloadable" by creating and
distributing your own Python package as described in the following section.


Distributing Plugins
--------------------

To distribute plugins, it is necessary to create a `Python package`_ with
a ``validate_pyproject.tool_schema`` entry-point_.

For the time being, if using setuptools_, this can be achieved by adding the following to your
``setup.cfg`` file:

.. code-block:: cfg

   # in setup.cfg
   [options.entry_points]
   validate_pyproject.tool_schema =
       your-tool = your_package.your_module:your_plugin

When using a :pep:`621`-compliant backend, the following can be add to your
``pyproject.toml`` file:

.. code-block:: toml

   # in pyproject.toml
   [project.entry-points."validate_pyproject.tool_schema"]
   your-tool = "your_package.your_module:your_plugin"

The plugin function will be automatically called with the ``tool_name``
argument as same name as given to the entrypoint (e.g. :samp:`your_plugin({"your-tool"})`).

Also notice plugins are activated in a specific order, using Python's built-in
``sorted`` function.


.. _entry-point: https://setuptools.pypa.io/en/stable/userguide/entry_point.html#entry-points
.. _JSON Schema: https://json-schema.org/
.. _Python package: https://packaging.python.org/
.. _setuptools: https://setuptools.pypa.io/en/stable/
