.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/validate-pyproject.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/validate-pyproject
    .. image:: https://readthedocs.org/projects/validate-pyproject/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://validate-pyproject.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/validate-pyproject/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/validate-pyproject
    .. image:: https://img.shields.io/pypi/v/validate-pyproject.svg
        :alt: PyPI-Server
        :target: https://pypi.org/project/validate-pyproject/
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

|

==================
validate-pyproject
==================


    Validation library for simple checks on 'pyproject.toml'


A longer description of your project goes here...


.. _pyscaffold-notes:

Making Changes & Contributing
=============================

This project uses `pre-commit`_, please make sure to install it before making any
changes::

    pip install pre-commit
    cd validate-pyproject
    pre-commit install

It is a good idea to update the hooks to the latest version::

    pre-commit autoupdate

Don't forget to tell your contributors to also install and use pre-commit.

.. _pre-commit: https://pre-commit.com/

Note
====

This project has been set up using PyScaffold 4.1.1.post1.dev8+g609f548. For details and usage
information on PyScaffold see https://pyscaffold.org/.
