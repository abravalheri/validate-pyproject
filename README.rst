.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://img.shields.io/conda/vn/conda-forge/validate-pyproject.svg
        :alt: Conda-Forge
        :target: https://anaconda.org/conda-forge/validate-pyproject
    .. image:: https://pepy.tech/badge/validate-pyproject/month
        :alt: Monthly Downloads
        :target: https://pepy.tech/project/validate-pyproject
    .. image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter
        :alt: Twitter
        :target: https://twitter.com/validate-pyproject

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/
.. image:: https://api.cirrus-ci.com/github/abravalheri/validate-pyproject.svg?branch=main
    :alt: Built Status
    :target: https://cirrus-ci.com/github/abravalheri/validate-pyproject
.. image:: https://readthedocs.org/projects/validate-pyproject/badge/?version=latest
    :alt: ReadTheDocs
    :target: https://validate-pyproject.readthedocs.io
.. image:: https://img.shields.io/coveralls/github/abravalheri/validate-pyproject/main.svg
    :alt: Coveralls
    :target: https://coveralls.io/r/abravalheri/validate-pyproject
.. image:: https://img.shields.io/pypi/v/validate-pyproject.svg
    :alt: PyPI-Server
    :target: https://pypi.org/project/validate-pyproject/

|

==================
validate-pyproject
==================


    Automated checks on ``pyproject.toml`` powered by JSON Schema definitions


.. important:: This project is **experimental** and under active development.
   Issue reports and contributions are very welcome.


Description
===========

With the approval of `PEP 517`_ and `PEP 518`_, the Python community shifted
towards a strong focus on standardisation for packaging software, which allows
more freedom when choosing tools during development and make sure packages
created using different technologies can interoperate without the need for
custom installation procedures.

This shift became even more clear when `PEP 621`_ was also approved, as a
standardised way of specifying project metadata and dependencies.

``validate-pyproject`` was born in this context, with the mission of validating
``pyproject.toml`` files, and make sure they are compliant with the standards
and PEPs. Behind the scenes, ``validate-pyproject`` relies on `JSON Schema`_
files, which, in turn, are also a standardised way of checking if a given data
structure complies with a certain specification.


.. _installation:

Usage
=====

The easiest way of using ``validate-pyproject`` is via CLI.
To get started, you need to install the package, which can be easily done
using |pipx|_:

.. code-block:: bash

    $ pipx install 'validate-pyproject[all]'

Now you can use ``validate-pyproject`` as a command line tool:

.. code-block:: bash

    # in you terminal
    $ validate-pyproject --help
    $ validate-pyproject path/to/your/pyproject.toml

You can also use ``validate-pyproject`` in your Python scripts or projects:

.. _example-api:

.. code-block:: python

    # in your python code
    from validate_pyproject import api, errors

    # let's assume that you have access to a `loads` function
    # responsible for parsing a string representing the TOML file
    # (you can check the `toml` or `tomli` projects for that)
    pyproject_as_dict = loads(pyproject_toml_str)

    # now we can use validate-pyproject
    validator = Validator()

    try:
        validator(pyproject_as_dict)
    except errors.JsonSchemaValueException:
        print("Invalid Document")

To do so, don't forget to add it to your `virtual environment`_ or specify it as a
`project`_ or `library dependency`_.

.. note::
   When you install ``validate-pyproject[all]``, the packages ``tomli``,
   ``packaging`` and ``trove-classifiers`` will be automatically pulled as
   dependencies. ``tomli`` is a lightweight parser for TOML, while
   ``packaging`` and ``trove-classifiers`` are used to validate aspects of `PEP
   621`_

   If you are only interested in using the Python API and wants to keep the
   depedependencies minimal, you can also install ``validate-pyproject``
   (without the ``[all]`` extra dependencies group).
   If you don't install ``trove-classifiers``, ``validate-pyproject`` will
   perform a weaker validation. On the other hand, if ``validate-pyproject``
   cannot find a copy of ``packaging`` in your environment, the validation will
   fail.

More details about ``validate-pyproject`` and its Python API can be found in
`our docs`_, which includes a description of the `used JSON schemas`_,
instructions for using it in a |vendored way|_ and information about
extending the validation with your own plugins_.

.. _pyscaffold-notes:

.. tip::
   If you consider contributing to this project, have a look on our
   `contribution guides`_.

Note
====

This project and its sister project ini2toml_ were initially created in the
context of PyScaffold, with the purpose of helping migrating existing projects
to `PEP 621`_-style configuration when it is made available on ``setuptools``.
For details and usage information on PyScaffold see https://pyscaffold.org/.


.. |pipx| replace:: ``pipx``
.. |vendored way| replace:: *"vendored" way*


.. _contribution guides: https://validate-pyproject.readthedocs.io/en/latest/contributing.html
.. _our docs: https://validate-pyproject.readthedocs.io
.. _ini2toml: https://ini2toml.readthedocs.io
.. _JSON Schema: https://json-schema.org/
.. _library dependency: https://setuptools.pypa.io/en/latest/userguide/dependency_management.html
.. _PEP 517: https://www.python.org/dev/peps/pep-0517/
.. _PEP 518: https://www.python.org/dev/peps/pep-0518/
.. _PEP 621: https://www.python.org/dev/peps/pep-0621/
.. _pipx: https://pypa.github.io/pipx/
.. _project: https://packaging.python.org/tutorials/managing-dependencies/
.. _setuptools: https://setuptools.pypa.io/en/stable/
.. _used JSON schemas: https://validate-pyproject.readthedocs.io/en/latest/schemas.html
.. _vendored way: https://validate-pyproject.readthedocs.io/en/latest/embedding.html
.. _plugins: https://validate-pyproject.readthedocs.io/en/latest/dev-guide.html
.. _virtual environment: https://realpython.com/python-virtual-environments-a-primer/
