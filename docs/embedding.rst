=====================================
Embedding validations in your project
=====================================

``validate-pyproject`` can be used as a dependency in your project
in the same way you would use any other Python library,
i.e. by adding it to the same `virtual environment`_ you run your code in, or
by specifying it as a `project`_ or `library dependency`_ that
is automatically retrieved every time your project is installed.
Please check :ref:`this example <example-api>` for a quick overview on how to
use the Python API.

Alternatively, if you cannot afford having external dependencies in your
project you can also opt to *"vendorise"* [#vend1]_ ``validate-pyproject``.
This can be done automatically via tools such as :pypi:`vendoring` or
:pypi:`vendorize` and many others others, however this technique will copy
several files into your project.

If you want to keep the amount of files to a minimum,
``validate-pyproject`` offers a different solution that consists in generating
a validation file (thanks to :pypi:`fastjsonschema`'s ability to compile JSON Schemas
to code) and copying only the strictly necessary Python modules.

After :ref:`installing <installation>` ``validate-pyproject`` this can be done
via CLI as indicated in the command bellow:

.. code-block:: bash

    # in you terminal
    $ python -m validate_pyproject.vendoring --help
    $ python -m validate_pyproject.vendoring -O dir/for/genereated_files

This command will generate a few files under the directory given to the CLI.
Please notice this directory should, ideally, be empty, and will correspond to
a "sub-package" in your package (a ``__init__.py`` file will be generated,
together with a few other ones).

Assuming you have created a ``genereated_files`` directory, and that the value
for the ``--main-file`` option in the CLI was kept as the default
``__init__.py``, you should be able to invoke the validation function in your
code by doing:

.. code-block:: python

    from .genereated_files import validate, JsonSchemaValueException

    try:
        validate(dict_representing_the_parsed_toml_file)
    except JsonSchemaValueException:
        print("Invalid File")


.. [#vend1] The words "vendorise" or "vendoring" in this text refer to the act
   of copying external dependencies to a folder inside your project, so they
   are distributed in the same package and can be used directly without relying
   on installation tools, such as :pypi:`pip`.


.. _project: https://packaging.python.org/tutorials/managing-dependencies/
.. _library dependency: https://setuptools.pypa.io/en/latest/userguide/dependency_management.html
.. _virtual environment: https://realpython.com/python-virtual-environments-a-primer/
