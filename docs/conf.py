"""Sphinx configuration for the AOTaccess documentation site."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import AOTaccess  # noqa: E402

# -- Project information -----------------------------------------------------

project = "AOTaccess"
author = "Knapen Lab"
copyright = "2026, Knapen Lab"
release = AOTaccess.__version__
version = AOTaccess.__version__

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_gallery.gen_gallery",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "auto_examples/index.rst"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Autosummary / autodoc ---------------------------------------------------

autosummary_generate = True
autosummary_imported_members = False

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# -- MyST (markdown) ---------------------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "tasklist",
    "fieldlist",
]
myst_heading_anchors = 3

# -- Intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "nibabel": ("https://nipy.org/nibabel/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

# -- Sphinx-Gallery ----------------------------------------------------------
# The gallery executes scripts at build time. On the cluster (where the real
# data is mounted) this produces full outputs and figures. On ReadTheDocs the
# data is unreachable, so we skip execution via the SPHINX_GALLERY_EXECUTE=0
# env var (set in .readthedocs.yaml) — the scripts are still rendered as code
# listings with their narrative blocks; only outputs / figures are omitted.

_execute_gallery = os.environ.get("SPHINX_GALLERY_EXECUTE", "1") != "0"

sphinx_gallery_conf = {
    "examples_dirs": "examples",
    "gallery_dirs": "auto_examples",
    "filename_pattern": r"^plot_",
    "plot_gallery": _execute_gallery,
    "remove_config_comments": True,
    "download_all_examples": False,
    "within_subsection_order": "FileNameSortKey",
}

# -- HTML output -------------------------------------------------------------

html_theme = "furo"
html_title = "AOTaccess"
html_static_path = ["_static"]
html_show_sourcelink = False

# -- Sphinx-copybutton -------------------------------------------------------

copybutton_prompt_text = r">>> |\$ "
copybutton_prompt_is_regexp = True
