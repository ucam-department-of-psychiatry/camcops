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

import argparse
import logging
import os
import shutil
import subprocess

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from rich_argparse import RichHelpFormatter

from camcops_server.cc_modules.cc_baseconstants import (
    ENVVARS_PROHIBITED_DURING_DOC_BUILD,
)

log = logging.getLogger(__name__)


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

DEST_DIRS: list[str] = [
    # SERVER_DOCS_DIR,
    # WEBSITE_DOCS_DIR,
]


# =============================================================================
# Build documentation
# =============================================================================

if __name__ == "__main__":
    main_only_quicksetup_rootlogger()
    # Remove anything old
    shutil.rmtree(BUILD_HTML_DIR, ignore_errors=True)
    for destdir in DEST_DIRS:
        print("Deleting directory {!r}".format(destdir))
        shutil.rmtree(destdir, ignore_errors=True)

    # Build docs
    print("Making HTML version of documentation")
    os.chdir(THIS_DIR)

    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatter)
    parser.add_argument(
        "--skip_client_help",
        action="store_true",
        help="Don't try to build the client help file",
        default=False,
    )

    parser.add_argument(
        "--warnings_as_errors",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args()

    # This one first, as it has requirements and may crash:
    for ev in ENVVARS_PROHIBITED_DURING_DOC_BUILD:
        os.environ.pop(ev, None)
    recreate_args = [
        "python",
        os.path.join(THIS_DIR, "recreate_inclusion_files.py"),
    ]

    if args.skip_client_help:
        recreate_args.append("--skip_client_help")

    subprocess.check_call(recreate_args)

    cmdargs = ["make", "html"]
    if args.warnings_as_errors:
        cmdargs.append('SPHINXOPTS="-W"')

    try:
        subprocess.check_call(cmdargs)
    except subprocess.CalledProcessError as e:
        log.debug(
            "\n\nTroubleshooting Sphinx/docutils errors:\n\n"
            "Document may not end with a transition\n"
            "--------------------------------------\n"
            "For auto-generated code docs, ensure there is a description "
            "beneath the row of '=' in the copyright block of the python "
            "file.\n\n"
            'Could not lex literal block as "C++". Highlighting skipped.\n'
            "-----------------------------------------------------------\n"
            "The Pygments C++ lexer is never going to be as good as a "
            "compiler and has problems with some of our code. Use the "
            "debug_highlighting.py script to track down bugs for "
            "reporting. Files can be skipped by adding them to the "
            "PYGMENTS_OVERRIDE dictionary in create_all_autodocs.py."
        )

        raise e

    # Copy
    for destdir in DEST_DIRS:
        print("Copying {!r} -> {!r}".format(BUILD_HTML_DIR, destdir))
        shutil.copytree(BUILD_HTML_DIR, destdir)
