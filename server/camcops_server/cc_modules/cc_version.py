#!/usr/bin/env python3
# cc_version.py

"""
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
"""

# =============================================================================
# Version constants and configuration variables read by shell scripts
# =============================================================================

# Versions need to be FLOAT.
CAMCOPS_SERVER_VERSION = 1.5
CAMCOPS_CHANGEDATE = "2016-07-29"
# ... must use double quotes; read by a regex in MAKE_PACKAGE.py
MINIMUM_TABLET_VERSION = 1.14
