The following assumptions are taken for the vendored packages:

- The upstream package is being patched in a separated repository controlled by
  the owner/maintainers of ``validate_pyproject``.
- The Python package leaves in a subfolder of the forked repository
- Only the package subfolder should be added to the ``_vendor`` folder
- ``git subtree`` is used to perform the vendoring


The following examples illustrate how ``fastjsonschema`` was vendored into
``validate_pyproject``:


.. code-block:: bash

    git remote add fastjsonschema git@github.com:abravalheri/python-fastjsonschema.git -t patched -m patched

    git checkout -b patched/fastjsonschema fastjsonschema/patched

    # split off the subdir into separate branch
    git subtree split --squash --prefix fastjsonschema --annotate="[vendoring] " --rejoin -b intermediate/vendoring/fastjsonschema

    # add separate branch as subdirectory
    git checkout main
    git checkout -b vendoring/fastjsonschema
    git subtree add --squash --prefix src/validate_pyproject/_vendor/fastjsonschema intermediate/vendoring/fastjsonschema


Later, when fetching new changes is needed:

.. code-block:: bash

   # switch back to the branch referencing the other repo
   git checkout patched/fastjsonschema
   git fetch --all
   git pull fastjsonschema/patched

   # update the separate branch with changes from upstream
   git subtree split -q --prefix fastjsonschema --annotate="[vendoring] " --rejoin -b intermediate/vendoring/fastjsonschema

   # switch back to the working branch or main to update subdirectory
   git checkout vendoring/fastjsonschema
   git subtree merge --squash --prefix src/validate_pyproject/_vendor/fastjsonschema intermediate/vendoring/fastjsonschema


References:

    - https://gist.github.com/tswaters/542ba147a07904b1f3f5
