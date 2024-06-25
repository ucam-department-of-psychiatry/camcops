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
from enum import Enum
import filecmp
import glob
import logging
import os
import shutil
from subprocess import Popen, PIPE
import sys
import tempfile
from typing import List, Set, Tuple

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from rich_argparse import RichHelpFormatter
from semantic_version import Version

from camcops_server.cc_modules.cc_baseconstants import (
    EXIT_SUCCESS,
    EXIT_FAILURE,
)

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

CLANG_FORMAT_VERSION = 14
CLANG_FORMAT_EXECUTABLE = "clang-format-{CLANG_FORMAT_VERSION}"
DIFFTOOL = "meld"
ENC = sys.getdefaultencoding()


class Command(Enum):
    CHECK = "check"
    DIFF = "diff"
    MODIFY = "modify"
    LIST = "list"
    PRINT = "print"


# =============================================================================
# Directories
# =============================================================================

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
CLANG_FORMAT_STYLE_FILE = os.path.abspath(
    os.path.join(THIS_DIR, "clang_format_camcops.yaml")
)
CAMCOPS_CPP_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))

INCLUDE_GLOBS = [
    f"{CAMCOPS_CPP_DIR}/**/*.cpp",
    f"{CAMCOPS_CPP_DIR}/**/*.h",
]
EXCLUDE_GLOBS = [
    # Code by Qt whose format we won't fiddle with too much.
    f"{CAMCOPS_CPP_DIR}/**/boxlayouthfw.*",
    f"{CAMCOPS_CPP_DIR}/**/qcustomplot.*",
    f"{CAMCOPS_CPP_DIR}/**/qtlayouthelpers.*",
    f"{CAMCOPS_CPP_DIR}/**/sqlcachedresult.*",
    f"{CAMCOPS_CPP_DIR}/**/sqlcipherdriver.*",
    f"{CAMCOPS_CPP_DIR}/**/sqlcipherhelpers.*",
    f"{CAMCOPS_CPP_DIR}/**/sqlcipherresult.*",
]


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
    parser.add_argument(
        "command",
        type=str,
        choices=[x.value for x in Command],
        help=f"Command to execute. "
        f"{Command.CHECK.value!r}: ensure nothing needs modifying; return "
        f"exit code {EXIT_SUCCESS} if everything is OK and {EXIT_FAILURE} if "
        f"something needs fixing. "
        f"{Command.DIFF.value!r}: launch a diff for the first file specified. "
        f"{Command.LIST.value!r}: list files only. "
        f"{Command.MODIFY.value!r}: modify all files in place. "
        f"{Command.PRINT.value!r}: print all results to stdout.",
    )
    parser.add_argument(
        "files",
        type=str,
        nargs="*",
        help="Files to modify (leave blank for all).",
    )
    parser.add_argument("--verbose", action="store_true", help="Be verbose")
    parser.add_argument(
        "--clangformat",
        type=str,
        default=shutil.which(CLANG_FORMAT_EXECUTABLE),
        help=f"Path to clang-format. Priority: (1) this argument, (2) the "
        f"results of 'which {CLANG_FORMAT_EXECUTABLE}'.",
    )
    parser.add_argument(
        "--diffall",
        action="store_true",
        help=f"For {Command.DIFF.value!r}: proceed to diff all files, not "
        f"just the first",
    )
    parser.add_argument(
        "--diffskipidentical",
        action="store_true",
        help=f"For {Command.DIFF.value!r}: skip files that are identical "
        f"after reformatting",
    )
    parser.add_argument(
        "--difftool",
        type=str,
        default=shutil.which(DIFFTOOL),
        help=f"Tool to use for diff. Priority: (1) this argument, (2) the "
        f"results of 'which {DIFFTOOL}'",
    )
    args = parser.parse_args()

    if args.clangformat is None:
        log.error(
            "No clangformat executable was found on the path and no "
            "--clangformat argument was specified"
        )
        sys.exit(EXIT_FAILURE)

    output, error, retcode = runit([args.clangformat, "--version"])
    if retcode:
        raise RuntimeError(f"clang-format error: \n{error}")

    version_words = output.split()
    version_number_index = version_words.index("version") + 1

    version = Version(version_words[version_number_index])
    if version.major != CLANG_FORMAT_VERSION:
        log.error(
            f"clang-format version {version.major} != {CLANG_FORMAT_VERSION}"
        )
        sys.exit(EXIT_FAILURE)

    command = Command(args.command)

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
        cpp_files = set()  # type: Set[str]
        for inc in INCLUDE_GLOBS:
            cpp_files = cpp_files.union(glob.glob(inc))
        for exc in EXCLUDE_GLOBS:
            cpp_files = cpp_files.difference(glob.glob(exc))
        cpp_files = sorted(cpp_files)  # type: List[str]

    # -------------------------------------------------------------------------
    # Build clazy command
    # -------------------------------------------------------------------------
    # Basic arguments
    common_clangformat_args = [
        args.clangformat,  # executable
        "--Werror",  # warnings as errors
        f"-style=file:{CLANG_FORMAT_STYLE_FILE}",  # style control file
    ]
    if command == Command.MODIFY:
        common_clangformat_args.append("-i")  # edit in place
    if args.verbose:
        common_clangformat_args.append("--verbose")  # be verbose

    # -------------------------------------------------------------------------
    # Run it
    # -------------------------------------------------------------------------
    success = True
    for filename in cpp_files:
        filename = os.path.abspath(filename)
        if command == Command.CHECK:
            log.info(f"Checking: {filename}")
        elif command == Command.DIFF:
            log.info(f"Diff: {filename}")
        elif command == Command.LIST:
            print(filename)
            continue
        elif command == Command.MODIFY:
            log.info(f"Modifying: {filename}")
        else:
            log.info(f"Printing: {filename}")
        # If we are in modification mode, the next command does the
        # modification directly:
        clangformatcmd = common_clangformat_args + [filename]
        output, error, retcode = runit(clangformatcmd)
        if retcode:
            raise RuntimeError("clang-format error: \n" + error)
        if command in (Command.CHECK, Command.DIFF):
            with tempfile.TemporaryDirectory() as tempdir:
                newfilename = os.path.join(
                    tempdir, os.path.basename(filename) + ".altered"
                )
                with open(newfilename, "wt") as f:
                    f.write(output)
                if command == Command.DIFF:
                    # Diff
                    if args.diffskipidentical and filecmp.cmp(
                        filename, newfilename
                    ):
                        log.info(f"Skipping unmodified file: {filename}")
                        continue
                    diffcmd = [args.difftool, filename, newfilename]
                    runit(diffcmd)
                    if not args.diffall:
                        log.info("Stopping after first diff")
                        break  # no more files
                else:
                    # Check
                    if not filecmp.cmp(filename, newfilename):
                        # Files differ
                        log.warning(f"File would be modified: {filename}")
                        success = False

        elif command == Command.PRINT:
            # Print
            print(output)

    sys.exit(EXIT_SUCCESS if success else EXIT_FAILURE)


# =============================================================================
# Command-line entry point
# =============================================================================

if __name__ == "__main__":
    clang_format_camcops_source()
