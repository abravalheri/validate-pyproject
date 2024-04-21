"""``sphinx-apidoc`` only allows users to specify "exclude patterns" but not
"include patterns". This module solves that gap.
"""

import shutil
from pathlib import Path

MODULE_TEMPLATE = """
``{name}``
~~{underline}~~

.. automodule:: {name}
   :members:{_members}
   :undoc-members:
   :show-inheritance:
   :special-members: __call__
"""

__location__ = Path(__file__).parent


def gen_stubs(module_dir: str, output_dir: str):
    shutil.rmtree(output_dir, ignore_errors=True)  # Always start fresh
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = shutil.copy(__location__ / "modules.rst.in", out / "modules.rst")
    for module in iter_public(manifest):
        text = module_template(module)
        Path(output_dir, f"{module}.rst").write_text(text, encoding="utf-8")


def iter_public(manifest):
    toc = Path(manifest).read_text(encoding="utf-8")
    lines = (x.strip() for x in toc.splitlines())
    return (x for x in lines if x.startswith("validate_pyproject."))


def module_template(name: str, *members: str) -> str:
    underline = "~" * len(name)
    _members = (" " + ", ".join(members)) if members else ""
    return MODULE_TEMPLATE.format(name=name, underline=underline, _members=_members)
