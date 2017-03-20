#!/usr/bin/env python
# cc_nhs.py

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

from typing import Dict, Optional
from .cc_string import wappstring


# =============================================================================
# Permitted values in fields and corresponding dictionaries
# =============================================================================

# Do not use WSTRING in the module-level code; the strings file is only
# initialized later. However, PV* fields are used at table creation.

PV_NHS_MARITAL_STATUS = ['S', 'M', 'D', 'W', 'P', 'N']
PV_NHS_ETHNIC_CATEGORY = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K',
                          'L', 'M', 'N', 'P', 'R', 'S', 'Z']


def get_nhs_dd_person_marital_status() -> Dict[Optional[str], Optional[str]]:
    return {
        None: None,
        "S": wappstring("nhs_person_marital_status_code_S"),
        "M": wappstring("nhs_person_marital_status_code_M"),
        "D": wappstring("nhs_person_marital_status_code_D"),
        "W": wappstring("nhs_person_marital_status_code_W"),
        "P": wappstring("nhs_person_marital_status_code_P"),
        "N": wappstring("nhs_person_marital_status_code_N"),
    }


def get_nhs_dd_ethnic_category_code() -> Dict[Optional[str], Optional[str]]:
    return {
        None: None,
        "A": wappstring("nhs_ethnic_category_code_A"),
        "B": wappstring("nhs_ethnic_category_code_B"),
        "C": wappstring("nhs_ethnic_category_code_C"),
        "D": wappstring("nhs_ethnic_category_code_D"),
        "E": wappstring("nhs_ethnic_category_code_E"),
        "F": wappstring("nhs_ethnic_category_code_F"),
        "G": wappstring("nhs_ethnic_category_code_G"),
        "H": wappstring("nhs_ethnic_category_code_H"),
        "J": wappstring("nhs_ethnic_category_code_J"),
        "K": wappstring("nhs_ethnic_category_code_K"),
        "L": wappstring("nhs_ethnic_category_code_L"),
        "M": wappstring("nhs_ethnic_category_code_M"),
        "N": wappstring("nhs_ethnic_category_code_N"),
        "P": wappstring("nhs_ethnic_category_code_P"),
        "R": wappstring("nhs_ethnic_category_code_R"),
        "S": wappstring("nhs_ethnic_category_code_S"),
        "Z": wappstring("nhs_ethnic_category_code_Z"),
    }
