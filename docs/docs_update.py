# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Sphinx Documentation Builder
----------------------------

A simple Python module to build Sphinx documentation and automatically
open the index.html in a web browser.

Features
--------
* Run Sphinx build command
* Automatically open index.html in default web browser
* Cross-platform support

Overview
--------
This module allows developers to quickly generate HTML documentation from
their Sphinx `.rst` or `.md` files and view the result without manually
navigating to the build folder.

Examples
--------
Update docs

.. code-block:: bash

    python -m ./docs/docs_update.py



"""
import shutil

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import subprocess
import webbrowser
import glob, os
from pathlib import Path

# External imports
# =======================================================================
# None required

# Project-level imports
# =======================================================================
# None required


# CONSTANTS
# ***********************************************************************

# CONSTANTS -- Project-level
# =======================================================================
DOCS_DIR = Path("docs")
BUILD_DIR = DOCS_DIR / "_build"
INDEX_FILE = BUILD_DIR / "index.html"


# FUNCTIONS
# ***********************************************************************


# FUNCTIONS -- Project-level
# =======================================================================
def build_docs(open_site=False):
    """
    Build Sphinx documentation and open the index.html file.

    This function runs the Sphinx build command with HTML output, then
    opens the generated index.html in the default web browser.
    """
    # Clean generated files
    delete_generated()
    delete_build()
    # Run sphinx-build
    subprocess.run(
        ["sphinx-build", "-b", "html", str(DOCS_DIR), str(BUILD_DIR), "--write-all"],
        check=True,
    )

    # Open the generated index.html in the default web browser
    if open_site:
        webbrowser.open(INDEX_FILE.resolve().as_uri())
    print(f"Documentation built successfully! Opened {INDEX_FILE}")


# FUNCTIONS -- Module-level
# =======================================================================
def delete_generated():
    """
    Delete all ``rst`` generated files prior to build.
    """
    ls_files = glob.glob("./generated/*.rst")
    if len(ls_files) == 0:
        pass
    else:
        for f in ls_files:
            os.remove(f)
    return None


def delete_build():
    """
    Delete all items in _build
    """
    d = Path(__file__).parent
    d_build = d / "_build"
    ls_items = os.listdir(d_build)
    for item in ls_items:
        item_path = f"./_build/{item}"
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)

    return None


# CLASSES
# ***********************************************************************
# No classes needed for this module


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":

    # Script section
    # ===================================================================
    build_docs()
