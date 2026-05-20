.. _installation_label:

~~~~~~~~~~~~
Installation
~~~~~~~~~~~~

Installation of heatpumps is very easy using pip. If you are using
`Miniforge <https://github.com/conda-forge/miniforge>`__, you can create and
activate a clean environment like this:

.. code-block:: console

    conda create -n my_new_env python=3.11

.. code-block:: console

    conda activate my_new_env


Then simply install heatpumps with the following command:

.. code-block:: console

    python -m pip install heatpumps


If you want to use an editable version of the package, e.g. if you want to
contribute to the project and test your own changes, skip the command above,
clone the repository from GitHub and use this one:


.. code-block:: console

    python -m pip install -e "C:\path\to\the\package"[dev]

.. note::

    The addition of the "-e" flag allows for changes to directly have an effect
    and adding "[dev]" to the installation path tells pip to also install the
    optional dependencies for developers.

.. tip::

    If you have already navigated your terminal (e.g. cmd) to the package
    directory, the path string in the command above simplifies to a single
    period character ("."), which means the current working directory.
