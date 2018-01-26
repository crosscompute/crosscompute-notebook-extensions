CrossCompute Extensions for Jupyter Notebook
============================================

Thanks to `Salah Ahmed <https://github.com/salah93>`_ for prototyping these extensions.

Installation
------------
::

    sudo dnf -y install procps
    pip install crosscompute-notebook-extensions
    jupyter nbextension install \
        --py --sys-prefix crosscompute_notebook_extensions
    jupyter nbextension enable \
        --py --sys-prefix crosscompute_notebook_extensions
    jupyter serverextension enable \
        --py --sys-prefix crosscompute_notebook_extensions

Usage via command-line
----------------------
::

    git clone https://github.com/crosscompute/crosscompute-notebook-examples
    cd crosscompute-notebook-examples/Examples
    crosscompute serve "Suggest Concepts.ipynb"

Usage via Jupyter Notebook
--------------------------
::

    cd tests/notebooks
    jupyter notebook

- Click the blue paper plane icon (or press SHIFT-C SHIFT-P) to preview the notebook as a tool.
- Click the red paper plane icon (or press SHIFT-C SHIFT-D) to deploy the notebook as a tool.
