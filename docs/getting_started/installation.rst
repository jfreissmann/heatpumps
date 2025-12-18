.. _installation_label:

~~~~~~~~~~~~
Installation
~~~~~~~~~~~~

For now, only direct download from the
`GitHub Repository <https://github.com/jfreissmann/heatpumps>`__ is supported,
so just clone it locally or download a ZIP file of the code. If you are using
`Miniforge <https://github.com/conda-forge/miniforge>`__, you can create and
activate a clean environment like this:

.. code-block:: console

    conda create -n my_new_env python=3.11

.. code-block:: console

    conda activate my_new_env


To use heatpumps, the necessary dependencies have to be installed. In a clean
environment from the root directory the installation from this file could look
like this:

.. code-block:: console

    python -m pip install "C:\path\to\the\package"

.. tip::

    If you have already navigated your terminal (e.g. cmd) to the package
    directory, the path string in the command above simplifies to a single
    period character ("."), which means the current working directory.


If you want to use an editable version of the package, e.g. if you want to
contribute to the project and test your own changes, skip the command above and
use this one:

.. code-block:: console

    python -m pip install -e .
