#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# flake8: noqa

import sys
import os

from setuptools_scm import get_version

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

autodoc_member_order = 'bysource'
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'pyvcd'
copyright = '2016, Western Digital Corporation'
author = 'Peter Grayson and Steven Sprouse'
version = get_version(root='..', relative_to=__file__)
# release = '0.0.1'
language = None
exclude_patterns = ['_build']
pygments_style = 'sphinx'
todo_include_todos = False

# Options for HTML output
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
htmlhelp_basename = 'pyvcddoc'

# Options for LaTeX output

latex_elements = {}
latex_documents = [
    (master_doc, 'pyvcd.tex', 'pyvcd Documentation',
     'Peter Grayson and Steven Sprouse', 'manual'),
]

# Options for manual page output
man_pages = [
    (master_doc, 'pyvcd', 'pyvcd Documentation',
     [author], 1)
]

# Options for Texinfo output
texinfo_documents = [
    (master_doc, 'pyvcd', 'pyvcd Documentation',
     author, 'pyvcd', 'One line description of project.',
     'Miscellaneous'),
]
