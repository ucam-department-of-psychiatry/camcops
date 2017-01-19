#!/usr/bin/env python
# cc_nhs.py

"""
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
"""

from typing import Dict, Optional
from .cc_string import WSTRING


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
        "S": WSTRING("nhs_person_marital_status_code_S"),
        "M": WSTRING("nhs_person_marital_status_code_M"),
        "D": WSTRING("nhs_person_marital_status_code_D"),
        "W": WSTRING("nhs_person_marital_status_code_W"),
        "P": WSTRING("nhs_person_marital_status_code_P"),
        "N": WSTRING("nhs_person_marital_status_code_N"),
    }


def get_nhs_dd_ethnic_category_code() -> Dict[Optional[str], Optional[str]]:
    return {
        None: None,
        "A": WSTRING("nhs_ethnic_category_code_A"),
        "B": WSTRING("nhs_ethnic_category_code_B"),
        "C": WSTRING("nhs_ethnic_category_code_C"),
        "D": WSTRING("nhs_ethnic_category_code_D"),
        "E": WSTRING("nhs_ethnic_category_code_E"),
        "F": WSTRING("nhs_ethnic_category_code_F"),
        "G": WSTRING("nhs_ethnic_category_code_G"),
        "H": WSTRING("nhs_ethnic_category_code_H"),
        "J": WSTRING("nhs_ethnic_category_code_J"),
        "K": WSTRING("nhs_ethnic_category_code_K"),
        "L": WSTRING("nhs_ethnic_category_code_L"),
        "M": WSTRING("nhs_ethnic_category_code_M"),
        "N": WSTRING("nhs_ethnic_category_code_N"),
        "P": WSTRING("nhs_ethnic_category_code_P"),
        "R": WSTRING("nhs_ethnic_category_code_R"),
        "S": WSTRING("nhs_ethnic_category_code_S"),
        "Z": WSTRING("nhs_ethnic_category_code_Z"),
    }
