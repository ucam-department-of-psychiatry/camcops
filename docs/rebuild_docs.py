#!/usr/bin/env python

"""
docs/rebuild_docs.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

"""

# =============================================================================
# Imports
# =============================================================================

import os
import shutil
import subprocess

from camcops_server.cc_modules.cc_baseconstants import (
    ENVVARS_PROHIBITED_DURING_DOC_BUILD,
)


# =============================================================================
# Constants
# =============================================================================

# Work out directories
THIS_DIR = os.path.dirname(os.path.realpath(__file__))
CAMCOPS_ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))
BUILD_HTML_DIR = os.path.join(THIS_DIR, "build", "html")
# SERVER_DOCS_DIR = os.path.join(CAMCOPS_ROOT_DIR, "server", "camcops_server",
#                                "static", "documentation_copy")
# WEBSITE_DOCS_DIR = os.path.join(CAMCOPS_ROOT_DIR, "website", "documentation")

DEST_DIRS = [
    # SERVER_DOCS_DIR,
    # WEBSITE_DOCS_DIR,
]


# =============================================================================
# Build documentation
# =============================================================================

if __name__ == "__main__":
    # Remove anything old
    shutil.rmtree(BUILD_HTML_DIR, ignore_errors=True)
    for destdir in DEST_DIRS:
        print("Deleting directory {!r}".format(destdir))
        shutil.rmtree(destdir, ignore_errors=True)

    # Build docs
    print("Making HTML version of documentation")
    os.chdir(THIS_DIR)
    # This one first, as it has requirements and may crash:
    for ev in ENVVARS_PROHIBITED_DURING_DOC_BUILD:
        os.environ.pop(ev, None)
    subprocess.check_call(
        ["python", os.path.join(THIS_DIR, "recreate_inclusion_files.py")]
    )
    subprocess.check_call(["make", "html"])

    # Copy
    for destdir in DEST_DIRS:
        print("Copying {!r} -> {!r}".format(BUILD_HTML_DIR, destdir))
        shutil.copytree(BUILD_HTML_DIR, destdir)
