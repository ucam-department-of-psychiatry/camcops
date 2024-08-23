#!/usr/bin/env python3

"""
tablet_qt/tools/run_cpp_tests.py

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

**Run C++ self-tests (having built them separately) on a local machine.**

"""

# =============================================================================
# Libraries
# =============================================================================

import argparse
import logging
from os import getcwd, pardir, walk
from os.path import abspath, dirname, isdir, isfile, join, realpath
import subprocess
import sys

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

THIS_DIR = dirname(realpath(__file__))
CAMCOPS_ROOT = abspath(join(THIS_DIR, pardir))
CPP_ROOT = join(CAMCOPS_ROOT, "tablet_qt")
TEST_SRC_ROOT = join(CPP_ROOT, "tests")
TEST_PRO = join(TEST_SRC_ROOT, "tests.pro")

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


# =============================================================================
# Test runner
# =============================================================================


def heading(text: str) -> None:
    """
    Print a heading to the log.
    """
    sep = "=" * 79
    log.info(f"\n{sep}\n{text}\n{sep}")


def run_cpp_tests(testrootdir: str) -> int:
    required_dirs = [join(testrootdir, "auto")]
    required_files = [join(testrootdir, "Makefile")]
    for rd in required_dirs:
        if not isdir(rd):
            raise ValueError(
                f"Missing directory {rd!r}"
                f" -- are you running from the wrong directory?"
            )
    for rf in required_files:
        if not isfile(rf):
            raise ValueError(
                f"Missing file {rf!r}"
                f" -- are you running from the wrong directory?"
            )
    # walk() yields tuples: dirpath, dirnames, filenames
    bindir = "bin"
    num_tests = 0
    num_passed = 0
    for dirpath, dirnames, _ in walk(testrootdir):
        if bindir in dirnames:
            for binpath, _, filenames in walk(join(dirpath, bindir)):
                for exe in filenames:
                    full_exe = join(binpath, exe)
                    heading(f"Running: {full_exe}")
                    try:
                        num_tests += 1
                        subprocess.check_call([full_exe])
                        num_passed += 1
                    except subprocess.CalledProcessError:
                        pass

    heading(f"{num_passed}/{num_tests} tests passed")

    if num_passed == num_tests:
        return EXIT_SUCCESS

    return EXIT_FAILURE


# =============================================================================
# Main
# =============================================================================


def main() -> None:
    """
    Command-line entry point.
    """
    parser = argparse.ArgumentParser(
        description=f"Run CamCOPS C++ self-tests. You should have already "
        f"built them, e.g. by using Qt Creator to build {TEST_PRO}",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--testroot", default=getcwd(), help="Root directory of built tests"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)

    exit_code = run_cpp_tests(args.testroot)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
