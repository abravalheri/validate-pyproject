from ..pre_compile import cli
from . import _deprecated


def run(*args, **kwargs):
    return _deprecated(run, cli.run)(*args, **kwargs)


def main(*args, **kwargs):
    return _deprecated(run, cli.main)(*args, **kwargs)
