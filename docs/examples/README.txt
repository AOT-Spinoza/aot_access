Examples gallery
================

Short, executable scripts that double as documentation. Each `plot_*.py`
script is rendered by Sphinx-Gallery into a page with the script source,
narrative blocks, and any output / figures produced when it ran.

Scripts assume access to the real AOT dataset on the lab cluster. They
execute by default when building the docs locally (`sphinx-build`); on
ReadTheDocs they're rendered as code listings only — the build there
sets ``SPHINX_GALLERY_EXECUTE=0`` because the dataset isn't reachable.
