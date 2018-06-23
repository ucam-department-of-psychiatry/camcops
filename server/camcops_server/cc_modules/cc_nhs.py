#!/usr/bin/env python
# camcops_server/cc_modules/cc_nhs.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

from typing import Dict, Optional

from .cc_request import CamcopsRequest


# =============================================================================
# Permitted values in fields and corresponding dictionaries
# =============================================================================

# Do not use wappstring in the module-level code; the strings file is only
# initialized later. However, PV* fields are used at table creation.

PV_NHS_MARITAL_STATUS = ['S', 'M', 'D', 'W', 'P', 'N']
PV_NHS_ETHNIC_CATEGORY = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K',
                          'L', 'M', 'N', 'P', 'R', 'S', 'Z']


def get_nhs_dd_person_marital_status(
        req: CamcopsRequest) -> Dict[Optional[str], Optional[str]]:
    return {
        None: None,
        "S": req.wappstring("nhs_person_marital_status_code_S"),
        "M": req.wappstring("nhs_person_marital_status_code_M"),
        "D": req.wappstring("nhs_person_marital_status_code_D"),
        "W": req.wappstring("nhs_person_marital_status_code_W"),
        "P": req.wappstring("nhs_person_marital_status_code_P"),
        "N": req.wappstring("nhs_person_marital_status_code_N"),
    }


def get_nhs_dd_ethnic_category_code(
        req: CamcopsRequest) -> Dict[Optional[str], Optional[str]]:
    return {
        None: None,
        "A": req.wappstring("nhs_ethnic_category_code_A"),
        "B": req.wappstring("nhs_ethnic_category_code_B"),
        "C": req.wappstring("nhs_ethnic_category_code_C"),
        "D": req.wappstring("nhs_ethnic_category_code_D"),
        "E": req.wappstring("nhs_ethnic_category_code_E"),
        "F": req.wappstring("nhs_ethnic_category_code_F"),
        "G": req.wappstring("nhs_ethnic_category_code_G"),
        "H": req.wappstring("nhs_ethnic_category_code_H"),
        "J": req.wappstring("nhs_ethnic_category_code_J"),
        "K": req.wappstring("nhs_ethnic_category_code_K"),
        "L": req.wappstring("nhs_ethnic_category_code_L"),
        "M": req.wappstring("nhs_ethnic_category_code_M"),
        "N": req.wappstring("nhs_ethnic_category_code_N"),
        "P": req.wappstring("nhs_ethnic_category_code_P"),
        "R": req.wappstring("nhs_ethnic_category_code_R"),
        "S": req.wappstring("nhs_ethnic_category_code_S"),
        "Z": req.wappstring("nhs_ethnic_category_code_Z"),
    }
