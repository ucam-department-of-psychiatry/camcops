#!/usr/bin/env python
# cc_version.py

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
"""

from semantic_version import Version

# =============================================================================
# Version constants and configuration variables read by shell scripts
# =============================================================================

CAMCOPS_SERVER_VERSION = Version("2.0.0")
CAMCOPS_CHANGEDATE = "2016-12-06"
MINIMUM_TABLET_VERSION = Version("1.14.0")


# =============================================================================
# For converting from older formats
# =============================================================================

def make_version(vstr: str) -> Version:
    try:
        return Version(vstr)
    except ValueError:
        # e.g. "1.14"
        parts = vstr.split(".")
        if len(parts) == 2:
            return Version(vstr + ".0")
        elif len(parts) == 1:
            return Version(vstr + ".0.0")
        else:
            raise


# =============================================================================
# Notable previous versions
# =============================================================================

TABLET_VERSION_2_0_0 = Version("2.0.0")  # move to C++ version
