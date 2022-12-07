#!/usr/bin/env python

"""
tablet_qt/tools/clang_format_camcops.py

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

Run clang-format over all our C++ code.

"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import glob
import logging
import os
import shutil
from subprocess import Popen, PIPE
import sys
import tempfile
from typing import List, Tuple

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from rich_argparse import RichHelpFormatter

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

CLANG_FORMAT_EXECUTABLE = "clang-format-14"
DIFFTOOL = "meld"
ENC = sys.getdefaultencoding()


# =============================================================================
# Directories
# =============================================================================

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
CLANG_FORMAT_STYLE_FILE = os.path.abspath(
    os.path.join(THIS_DIR, "clang_format_camcops.yaml")
)
CAMCOPS_CPP_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))


# =============================================================================
# Apply clang-format to our source code
# =============================================================================


def runit(cmdargs: List[str]) -> Tuple[str, str, int]:
    log.debug(cmdargs)
    p = Popen(cmdargs, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
    output = output.decode(ENC)
    error = error.decode(ENC)
    return output, error, p.returncode


def clang_format_camcops_source() -> None:
    """
    Apply clang-format to CamCOPS C++ source code, to standardize code style.
    """
    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="Be verbose")
    parser.add_argument(
        "--clangformat",
        type=str,
        default=shutil.which(CLANG_FORMAT_EXECUTABLE),
        help=f"Path to clang-format. Priority: (1) this argument, (2) the "
        f"results of 'which {CLANG_FORMAT_EXECUTABLE}'.",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Diff the first file only, then stop.",
    )
    parser.add_argument(
        "--modify",
        action="store_true",
        help="Modify files in place. Otherwise, files written to stdout only.",
    )
    parser.add_argument(
        "--difftool",
        type=str,
        default=shutil.which(DIFFTOOL),
        help=f"Tool to use for diff. Priority: (1) this argument, (2) the "
        f"results of 'which {DIFFTOOL}'",
    )
    parser.add_argument(
        "files",
        type=str,
        nargs="*",
        help="Files to modify (leave blank for all).",
    )
    args = parser.parse_args()
    if args.diff and args.modify:
        raise ValueError("The options --diff and --modify are incompatible")

    main_only_quicksetup_rootlogger(
        level=logging.DEBUG if args.verbose else logging.INFO
    )

    # -------------------------------------------------------------------------
    # Files
    # -------------------------------------------------------------------------

    # Files to process:
    if args.files:
        cpp_files = args.files
    else:
        cpp_files = list(glob.glob(f"{CAMCOPS_CPP_DIR}/**/*.cpp")) + list(
            glob.glob(f"{CAMCOPS_CPP_DIR}/**/*.h")
        )

    # -------------------------------------------------------------------------
    # Build clazy command
    # -------------------------------------------------------------------------
    # Basic arguments
    common_clangformat_args = [
        args.clangformat,  # executable
        "--Werror",  # warnings as errors
        f"-style=file:{CLANG_FORMAT_STYLE_FILE}",  # style control file
    ]
    if args.modify:
        common_clangformat_args.append("-i")  # edit in place
    if args.verbose:
        common_clangformat_args.append("--verbose")  # be verbose

    # -------------------------------------------------------------------------
    # Run it
    # -------------------------------------------------------------------------
    for filename in cpp_files:
        filename = os.path.abspath(filename)
        if args.modify:
            log.info(f"Modifying: {filename}")
        elif args.diff:
            log.info(f"Diff: {filename}")
        else:
            log.info(f"Printing only: {filename}")
        clangformatcmd = common_clangformat_args + [filename]
        output, error, retcode = runit(clangformatcmd)
        if retcode:
            raise RuntimeError("clang-format error: \n" + error)
        if args.diff:
            with tempfile.TemporaryDirectory() as tempdir:
                newfilename = os.path.join(
                    tempdir, os.path.basename(filename) + ".altered"
                )
                with open(newfilename, "wt") as f:
                    f.write(output)
                diffcmd = [args.difftool, filename, newfilename]
                runit(diffcmd)
                break  # no more files
        if not args.modify:
            print(output)


# =============================================================================
# Command-line entry point
# =============================================================================

if __name__ == "__main__":
    clang_format_camcops_source()
