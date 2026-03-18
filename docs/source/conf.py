import os
import sys

# 1. Path Setup
# Points to C:\Users\adamz\conn\
sys.path.insert(0, os.path.abspath('../../'))

# 2. Project Info
project = 'pfw'
copyright = '2026, adam'
author = 'adam'
release = '2026'

# 3. Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]

# 4. The "Safe" Mocking List
# We include 'time' and 'utime' here. Sphinx will create its own
# mock objects that ARE pickleable.
autodoc_mock_imports = [
    "machine",
    "network",
    "gc",
    "uarray",
    "ujson",
    "micropython",
    "time",
    "utime"
]

# 5. Options for HTML output
html_theme = 'alabaster'
autodoc_member_order = 'bysource'

# 6. Ensure __init__ shows up
def setup(app):
    app.connect('autodoc-skip-member', lambda app, what, name, obj, skip, options:
                False if name == "__init__" else skip)