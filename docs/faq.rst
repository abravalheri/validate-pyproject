===
FAQ
===


Why JSON Schema?
================

This design was initially inspired by an issue_ in the ``setuptools`` repository,
and brings a series of advantages and disadvantages.

Disadvantages include the fact that `JSON Schema`_ might be limited at times and
incapable of describing more complex checks. Additionally, error messages
produced by JSON Schema libraries might not be as pretty as the ones used
when bespoke validation is in place.

On the other hand, the fact that JSON Schema is standardised and have a
widespread usage among several programming language communities, means that a
bigger number of people can easily understand the schemas and modify them if
necessary.

Additionally, :pep:`518` already includes a JSON Schema representation, which
suggests that it can be used at the same time as specification language and
validation tool.


Why ``fastjsonschema``?
=======================

While there are other (more popular) `JSON Schema`_ libraries in the Python
community, none of the ones the original author of this package investigated
(other than :pypi:`fastjsonschema`) fulfilled the following requirements:

- Minimal number of dependencies (ideally 0)
- Easy to "vendorise", i.e. copy the source code of the package to be used
  directly without requiring installation.

:pypi:`fastjsonschema` has no dependency and can generate validation code directly,
which bypass the need for copying most of the files when :doc:`"vendoring"
<embedding>`.


Why draft-07 of JSON Schema and not a more modern version?
==========================================================

The most modern version of JSON Schema supported by :pypi:`fastjsonschema` is Draft 07.
It is not as bad as it may sound, it even supports `if-then-else`_-style conditions…


Why the schemas use URLs that do not point for themselves?
==========================================================

According to the JSON Schema, the `$id keyword`_ doesn't have to be the address
of the schemas themselves:

    Note that this URI is an identifier and not necessarily a network locator.
    In the case of a network-addressable URL, a schema need not be downloadable
    from its canonical URI.


.. _if-then-else: https://json-schema.org/understanding-json-schema/reference/conditionals.html
.. _issue: https://github.com/pypa/setuptools/issues/2671
.. _JSON Schema: https://json-schema.org/
.. _$id keyword: https://json-schema.org/draft/2020-12/json-schema-core.html#rfc.section.8.2.1
