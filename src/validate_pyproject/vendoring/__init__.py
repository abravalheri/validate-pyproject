import warnings
from functools import wraps
from inspect import cleandoc

from ..pre_compile import pre_compile


def _deprecated(orig, repl):
    msg = f"""
    `{orig.__module__}:{orig.__name__}` is deprecated and will be removed in future
    versions of `validate-pyproject`.

    Please use `{repl.__module__}:{repl.__name__}` instead.
    """

    @wraps(orig)
    def _wrapper(*args, **kwargs):
        warnings.warn(cleandoc(msg), category=DeprecationWarning)
        return repl(*args, **kwargs)

    return _wrapper


def vendorify(*args, **kwargs):
    return _deprecated(vendorify, pre_compile)(*args, **kwargs)
