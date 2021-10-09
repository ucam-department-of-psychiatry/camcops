#!/usr/bin/env python

"""
tablet_qt/tools/clazy_camcops.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

import logging
import os
import shutil
import subprocess

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger

log = logging.getLogger(__name__)


# =============================================================================
# Directories
# =============================================================================

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
CAMCOPS_CPP_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))

HOME = os.environ.get("HOME")
QT_INCLUDE_ROOT = f"{HOME}/dev/qt_local_build/qt_linux_x86_64_install/include"

# noinspection PyUnresolvedReferences
CPP_INCLUDE_DIRS = [
    CAMCOPS_CPP_DIR,
    QT_INCLUDE_ROOT
] + [
    # All immediate subdirectories of QT_INCLUDE_ROOT
    x.path
    for x in os.scandir(QT_INCLUDE_ROOT)
]
CPP_INCLUDE_DIRS.sort()

TEST_FILE = os.path.join(CAMCOPS_CPP_DIR, "main.cpp")


# =============================================================================
# clazy executable: the value of the CLAZY environment variable, or in its
# absence, whatever we find on the path.
# =============================================================================

CLAZY = os.environ.get("CLAZY", shutil.which("clazy"))


# =============================================================================
# clazy options -- many are passed to clang
# =============================================================================

def clazy_camcops_source() -> None:
    log.warning("Code in development! Not yet working.")
    include_dir_args = [
        f"-I{x}"
        for x in CPP_INCLUDE_DIRS
    ]
    log.warning("TODO: make QT_INCLUDE_ROOT system-independent, e.g. envvar")
    log.warning("TODO: fix initial errors/warnings")
    log.warning("TODO: expand to all .h/.cpp files")
    file_args = [TEST_FILE]
    cmdargs = [CLAZY] + include_dir_args + file_args
    # print(cmdargs)
    subprocess.run(cmdargs)


if __name__ == "__main__":
    main_only_quicksetup_rootlogger()
    clazy_camcops_source()
