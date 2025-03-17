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

To use a plugin you can pass an ``extra_plugins`` argument to the
:class:`~validate_pyproject.api.Validator` constructor, but you will need to
wrap it with :class:`~validate_pyproject.plugins.PluginWrapper` to be able to
specify which ``tool`` subtable it would be checking:

.. code-block:: python

    from validate_pyproject import api


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
        plugins.PluginWrapper("your-tool", your_plugin),
    ]
    validator = api.Validator(extra_plugins=available_plugins)

Please notice that you can also make your plugin "autoloadable" by creating and
distributing your own Python package as described in the following section.

If you want to disable the automatic discovery of all "autoloadable" plugins you
can pass ``plugins=[]`` to the constructor; or, for example in the snippet
above, we could have used ``plugins=...`` instead of ``extra_plugins=...``
to ensure only the explicitly given plugins are loaded.


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


Providing multiple schemas
--------------------------

A second system is defined for providing multiple schemas in a single plugin.
This is useful when a single plugin is responsible for multiple subtables
under the ``tool`` table, or if you need to provide multiple schemas for a
a single subtable.

To use this system, the plugin function, which does not take any arguments,
should return a dictionary with two keys: ``tools``, which is a dictionary of
tool names to schemas, and optionally ``schemas``, which is a list of schemas
that are not associated with any specific tool, but are loaded via ref's from
the other tools.

When using a :pep:`621`-compliant backend, the following can be add to your
``pyproject.toml`` file:

.. code-block:: toml

    # in pyproject.toml
    [project.entry-points."validate_pyproject.multi_schema"]
    arbitrary = "your_package.your_module:your_plugin"

An example of the plugin structure needed for this system is shown below:

.. code-block:: python

    def your_plugin(tool_name: str) -> dict:
        return {
            "tools": {"my-tool": my_schema},
            "schemas": [my_extra_schema],
        }

Fragments for schemas are also supported with this system; use ``#`` to split
the tool name and fragment path in the dictionary key.


.. admonition:: Experimental: Conflict Resolution

   Please notice that when two plugins define the same ``tool``
   (or auxiliary schemas with the same ``$id``),
   an internal conflict resolution heuristic is employed to decide
   which schema will take effect.

   To influence this heuristic you can:

   - Define a numeric ``.priority`` property in the functions
     pointed by the ``validate_pyproject.tool_schema`` entry-points.
   - Add a ``"priority"`` key with a numeric value into the dictionary
     returned by the ``validate_pyproject.multi_schema`` plugins.

   Typical values for ``priority`` are ``0`` and ``1``.

   The exact order in which the plugins are loaded is considered an
   implementation detail.


.. _entry-point: https://setuptools.pypa.io/en/stable/userguide/entry_point.html#entry-points
.. _JSON Schema: https://json-schema.org/
.. _Python package: https://packaging.python.org/
.. _setuptools: https://setuptools.pypa.io/en/stable/
