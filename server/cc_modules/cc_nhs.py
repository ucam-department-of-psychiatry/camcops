#!/usr/bin/env python3
# cc_nhs.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from cc_string import WSTRING


# =============================================================================
# Permitted values in fields and corresponding dictionaries
# =============================================================================

# Do not use WSTRING in the module-level code; the strings file is only
# initialized later. However, PV* fields are used at table creation.

PV_NHS_MARITAL_STATUS = ['S', 'M', 'D', 'W', 'P', 'N']
PV_NHS_ETHNIC_CATEGORY = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K',
                          'L', 'M', 'N', 'P', 'R', 'S', 'Z']


def get_nhs_dd_person_marital_status():
    return {
        None: None,
        "S": WSTRING("nhs_person_marital_status_code_S"),
        "M": WSTRING("nhs_person_marital_status_code_M"),
        "D": WSTRING("nhs_person_marital_status_code_D"),
        "W": WSTRING("nhs_person_marital_status_code_W"),
        "P": WSTRING("nhs_person_marital_status_code_P"),
        "N": WSTRING("nhs_person_marital_status_code_N"),
    }


def get_nhs_dd_ethnic_category_code():
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
