#!/usr/bin/env python

"""
tablet_qt/tools/clazy_camcops.py

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

Run clazy over all our C++ code.

"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import glob
import logging
import os
import shutil
import subprocess
import sys
import tempfile

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from rich_argparse import RichHelpFormatter

from camcops_server.cc_modules.cc_baseconstants import (
    EXIT_FAILURE,
)

log = logging.getLogger(__name__)


# =============================================================================
# Environment variables
# =============================================================================

ENVVAR_CLAZY = "CLAZY"
ENVVAR_QT_INSTALLATION_ROOT = "QT_INSTALLATION_ROOT"


# =============================================================================
# Directories
# =============================================================================

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
CAMCOPS_CPP_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))

DEFAULT_QT_INSTALLATION_ROOT = "~/dev/qt_local_build/qt_linux_x86_64_install"

CAMCOPS_CPP_INCLUDE_DIRS = [CAMCOPS_CPP_DIR]
CAMCOPS_CPP_INCLUDE_DIRS.sort()


# =============================================================================
# Apply clazy to our source code
# =============================================================================

CHECKS = [
    "level2",  # the basic level
    # Use the "no-" prefix to disable a check:
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # LEVEL 2 CHECKS TO DISABLE:
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # As clazy points out, (global) static variables are fine in executables,
    # but not in libraries; clazy doesn't know which is being built, so issues
    # the warning. The standard sort of code that generates this warning is
    # file-level code like
    #       const QString SOME_STRING("hello world");
    # https://github.com/KDE/clazy/blob/master/docs/checks/README-non-pod-global-static.md  # noqa: E501
    "no-non-pod-global-static",
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # MANUAL LEVEL CHECKS TO DISABLE:
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # e.g. "emit someSignal()"
    "no-qt-keywords",
]

_ = """
Other things to note:

AVOID:
    const QString s("text");
PREFER:
    const QString s = QStringLiteral("text");
OR BETTER:
    const QString s(QStringLiteral("text"));
See https://github.com/KDE/clazy/blob/master/docs/checks/README-qstring-allocations.md.

For empty strings, use QLatin1String(""), QLatin1String(), or QString().
The last of these is simplest and shortest.

"""  # noqa: E501


def clazy_camcops_source() -> None:
    """
    Apply clazy to CamCOPS C++ source code, to detect errors.
    """
    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="Be verbose")
    parser.add_argument(
        "--assemble",
        action="store_true",
        help=(
            "Assemble (produce .s file) rather than compile (produce .o file)"
        ),
    )
    parser.add_argument(
        "--clazy",
        type=str,
        default=os.environ.get(ENVVAR_CLAZY, shutil.which("clazy")),
        help=f"Path to clazy. Priority: (1) this argument, (2) the "
        f"{ENVVAR_CLAZY} environment variable, (3) the results of "
        f"'which clazy'.",
    )
    parser.add_argument(
        "--qt_installation_root",
        type=str,
        default=os.environ.get(
            ENVVAR_QT_INSTALLATION_ROOT,
            os.path.expanduser(DEFAULT_QT_INSTALLATION_ROOT),
        ),
        help=(
            f"Path to your installed copy of Qt. Priority: (1) this argument, "
            f"(2) the {ENVVAR_QT_INSTALLATION_ROOT} environment variable, "
            f"(3) a default of {DEFAULT_QT_INSTALLATION_ROOT}."
        ),
    )
    parser.add_argument(
        "files",
        type=str,
        nargs="*",
        help="Files to scan (leave blank for all).",
    )
    args = parser.parse_args()

    if args.clazy is None:
        log.error(
            "No clazy executable was found on the path and no "
            "--clazy argument was specified"
        )
        sys.exit(EXIT_FAILURE)

    main_only_quicksetup_rootlogger(
        level=logging.DEBUG if args.verbose else logging.INFO
    )

    # -------------------------------------------------------------------------
    # Environment variables and files
    # -------------------------------------------------------------------------

    # Directories:
    qt_include_root = f"{args.qt_installation_root}/include"
    # qt_library_root = f"{args.qt_installation_root}/lib"
    # noinspection PyUnresolvedReferences
    system_cpp_include_dirs = [qt_include_root] + [
        # All immediate subdirectories of qt_include_root
        x.path
        for x in os.scandir(qt_include_root)
    ]
    system_cpp_include_dirs.sort()

    # Files to process:
    if args.files:
        cpp_files = args.files
    else:
        cpp_files = list(glob.glob(f"{CAMCOPS_CPP_DIR}/**/*.cpp"))

    # -------------------------------------------------------------------------
    # Build clazy command
    # -------------------------------------------------------------------------
    # Basic arguments
    cmdargs = [
        args.clazy,
        "-fPIC",  # https://gcc.gnu.org/onlinedocs/gcc-4.0.4/gccint/PIC.html
        "--assemble" if args.assemble else "--compile",
        # --assemble produces ".s" files  (preprocess/assemble);
        # --compile produces ".o" files (preprocess/assemble/compile);
        # either way, we don't want to link.
    ]
    if args.verbose:
        cmdargs.append("-v")  # be verbose

    # C++ include paths
    # (a) #include "blah"
    for d in CAMCOPS_CPP_INCLUDE_DIRS:
        cmdargs += ["-I", d]
    # (b) #include <blah>
    for d in system_cpp_include_dirs:
        # https://github.com/KDE/clazy/blob/master/README.md#selecting-which-checks-to-enable  # noqa
        # "If you want to suppress warnings from headers of Qt or 3rd party
        # code, include them with -isystem instead of -I (gcc/clang only)."
        #
        # https://gitlab.kitware.com/cmake/cmake/-/issues/16915
        # ... suggests in fact "-isystem=..."
        # ... but actually, separate arguments is what works:
        cmdargs += ["-isystem", d]

    # Linker paths
    # cmdargs += ["--library-directory", QT_LIBRARY_ROOT]
    # ... or "-Lblah"
    # https://clang.llvm.org/docs/ClangCommandLineReference.html#linker-flags
    # ... actually, better to disable the linker! See "--compile" above, and
    # https://clang.llvm.org/docs/ClangCommandLineReference.html#actions

    # Additional switches to suppress warnings:
    # https://github.com/KDE/clazy
    clazy_checks = ",".join(CHECKS)
    log.info(f"CLAZY_CHECKS: {clazy_checks}")
    os.environ["CLAZY_CHECKS"] = clazy_checks

    # Files to process:
    cmdargs += [os.path.abspath(x) for x in cpp_files]
    # ... absolute path because we'll change directory in a moment.

    # -------------------------------------------------------------------------
    # Run it
    # -------------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        # clazy creates .s/.o files in the directory you call it from, so this
        # does automatic cleanup.
        os.chdir(tmpdir)
        log.debug(cmdargs)
        subprocess.run(cmdargs)


# =============================================================================
# Command-line entry point
# =============================================================================

if __name__ == "__main__":
    clazy_camcops_source()
