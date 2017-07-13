#!/usr/bin/env python
# cc_baseconstants.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================

Constants required during package creation, which therefore can't rely on
anything except the Python standard library.
"""

import os

_this_directory = os.path.dirname(os.path.abspath(__file__))
CAMCOPS_SERVER_DIRECTORY = os.path.abspath(
    os.path.join(_this_directory,  # cc_modules
                 os.pardir))  # camcops_server
TABLET_SOURCE_COPY_DIR = os.path.join(CAMCOPS_SERVER_DIRECTORY,
                                      "tablet_source_copy")

INTROSPECTABLE_EXTENSIONS = [".cpp", ".h", ".html", ".js", ".jsx",
                             ".py", ".pl", ".qml", ".xml"]
