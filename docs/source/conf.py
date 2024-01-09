# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from datetime import date

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
# project root
# sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../.."))


# -- Project information -----------------------------------------------------

project = 'Qiskit-pQCee-provider'
copyright = '2023, Stefan Dan Ciocirlan'
author = 'Stefan Dan Ciocirlan'

# The full version, including alpha/beta/rc tags
release = '0.1.1'
version = '0.1.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # "sphinx.ext.autodoc",
    # "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    # "numpydoc",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.imgmath",
    'sphinx.ext.napoleon',
    "autoapi.extension",
    "sphinx_autodoc_typehints",
    # "sphinxarg.ext",
    "sphinxcontrib.autoprogram",
]
autoapi_type = 'python'
autoapi_dirs = ['../../qiskit_pqcee_provider']
autoapi_keep_files = True
autoapi_member_order = "groupwise"
autoapi_options = ['members', 'undoc-members', 'show-inheritance',
                   'show-module-summary', 'special-members',
                   'imported-members']

autosummary_generate = True
autosummary_imported_members = True
autosummary_generate_overwrite = True

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = {
    'typing.Any': ':obj:`Any`',
    'array_like': ':term:`array_like`',
    'np.ndarray': ':obj:`numpy.ndarray`',
}
napoleon_attr_annotations = True

# autodoc settings
autoclass_content = "class"
autodoc_default_options = {
    'members':          True,
    'undoc-members':    True,
    'inherited-members': True,
    'show-inheritance': True,
}
# autodoc_member_order = 'bysource'
# autodoc_typehints = "both"
# autodoc_typehints_description_target = "documented_params"
# Add any paths that contain templates here, relative to this directory.
typehints_fully_qualified = False
typehints_document_rtype = True
typehints_defaults = 'braces'
simplify_optional_unions = False
typehints_use_signature = True
typehints_use_signature_return = True
templates_path = ['_templates']


# numpydoc_xref_param_type = True
# numpydoc_xref_ignore = {"optional", "type_without_description", "BadException"}
# Run docstring validation as part of build process
# numpydoc_validation_checks = {"all", "GL01", "SA04", "RT03"}


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "show_nav_level": 2,
    "show_prev_next": False,
    "navbar_end": ["theme-switcher", "search-field.html",
                   "navbar-icon-links.html"],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/sdcioc/QuantumLeaderElection",
            "icon": "fab fa-github-square",
            "type": "fontawesome",
        },
    ],
}

html_sidebars = {
    "**": ["sidebar-nav-bs", "sidebar-ethical-ads"]
}
html_context = {
    "default_mode": "light",
}

html_title = f"{project} v{version} Manual"
html_last_updated_fmt = "%b %d, %Y"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Intersphinx setup ----------------------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/devdocs/", None),
}
