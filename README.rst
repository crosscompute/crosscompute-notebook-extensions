CrossCompute Extensions for Jupyter Notebook
============================================

Thanks to `Salah Ahmed <https://github.com/salah93>`_ for prototyping these extensions.

Installation
------------
::

    pip install crosscompute-notebook-extensions
    jupyter nbextension install \
        --sys-prefix --py crosscompute_notebook_extensions
    jupyter nbextension enable \
        --sys-prefix --py crosscompute_notebook_extensions
    jupyter serverextension enable \
        --sys-prefix --py crosscompute_notebook_extensions

Usage via command-line
----------------------
::

    crosscompute serve tests/notebooks/add-integers.ipynb
    crosscompute serve tests/notebooks/map-locations.ipynb

Usage via Jupyter Notebook
--------------------------
::

    cd tests/notebooks
    jupyter notebook

Click the green paper plane icon (or press SHIFT-C SHIFT-P) to preview the notebook as a tool.
