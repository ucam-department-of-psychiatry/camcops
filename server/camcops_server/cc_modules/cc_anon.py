#!/usr/bin/env python
# camcops_server/cc_modules/cc_sqlalchemy.py

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

from collections import OrderedDict
import re
from typing import Dict, List, Pattern, Tuple

from .cc_constants import TSV_PATIENT_FIELD_PREFIX
from . import cc_db


# =============================================================================
# For anonymisation
# =============================================================================

def get_literal_regex(x: str) -> Pattern:
    """Regex for anonymisation. Literal at word boundaries."""
    # http://stackoverflow.com/questions/919056
    wb = "\\b"  # word boundary; escape the slash
    return re.compile(wb + re.escape(x) + wb, re.IGNORECASE)


# =============================================================================
# For anonymisation staging database
# =============================================================================

def get_type_size_as_text_from_sqltype(sqltype: str) -> Tuple[str, str]:
    size = ""
    finaltype = sqltype
    m = re.match("(\w+)\((\w+)\)", sqltype)  # e.g. VARCHAR(10)
    if m:
        finaltype = m.group(1)
        size = m.group(2)
    return finaltype, size


def get_cris_dd_row(taskname: str,
                    tablename: str,
                    fieldspec: "FIELDSPEC_TYPE") -> Dict:
    """Returns an OrderedDict with information for a CRIS Data Dictionary row,
    given a fieldspec."""

    cc_db.add_sqltype_to_fieldspec_in_place(fieldspec)
    cctype = fieldspec["cctype"]
    sqltype = fieldspec["sqltype"]
    colname = fieldspec["name"]
    anon = fieldspec.get("anon", False)  # optional
    comment = fieldspec.get("comment", "")  # optional
    identifies_patient = fieldspec.get("identifies_patient", False)

    patientlen = len(TSV_PATIENT_FIELD_PREFIX)
    patientfield = (colname[:patientlen] == TSV_PATIENT_FIELD_PREFIX)

    finaltype, size = get_type_size_as_text_from_sqltype(sqltype)

    if "pv" in fieldspec:
        valid_values = ",".join([str(x) for x in fieldspec["pv"]])
    else:
        valid_values = ""

    might_need_scrubbing = cctype in ["TEXT"] and not anon
    tlfa = "Y" if might_need_scrubbing else ""

    system_id = (
        colname == "id" or
        colname == "patient_id" or
        colname == TSV_PATIENT_FIELD_PREFIX + "id" or
        (colname[:1] == "_" and colname[-3:] == "_pk")
    )
    internal_field = (
        colname[:1] == "_" and not patientfield
    ) or (
        patientfield and colname[patientlen:patientlen + 1] == "_"
    )

    if system_id or internal_field:
        security_status = "1"  # drop (e.g. for pointless internal keys)
    elif identifies_patient and colname == TSV_PATIENT_FIELD_PREFIX + "dob":
        security_status = "3"  # truncate (e.g. DOB, postcode)
    elif identifies_patient:
        security_status = "2"  # use to scrub
    else:
        security_status = "4"  # bring through

    if system_id:
        feft = "34"  # patient ID; other internal keys
    elif cc_db.cctype_is_date(cctype):
        feft = "4"  # dates
    else:
        feft = "1"  # text, numbers

    return OrderedDict([
        ("Tab", "CamCOPS"),
        ("Form name", taskname),
        ("CRIS tree label", colname),
        ("Source system table name", tablename),
        ("SQL column name", colname),
        ("Front end field type", feft),
        ("Valid values", valid_values),
        ("Result column name", colname),
        ("Family doc tab name", ""),
        ("Family doc form name", ""),
        ("Security status", security_status),
        ("Exclude", ""),
        ("End SQL Type", finaltype),
        ("Header field (Y/N)", ""),
        ("Header field name", ""),
        ("Header field active (Y/N)", ""),
        ("View name", ""),
        ("Exclude from family doc", ""),
        ("Tag list - fields anon", tlfa),
        ("Anon type", ""),  # formerly "Additional info"
        ("Form start date", ""),
        ("Form end date", ""),
        ("Source", ""),
        ("Size", size),
        ("Header logic", ""),
        ("Patient/contact", ""),
        ("Comments", comment),
    ])


def get_cris_dd_rows_from_fieldspecs(
        taskname: str,
        tablename: str,
        fieldspecs: "FIELDSPECLIST_TYPE") -> List[Dict]:
    rows = []
    for fs in fieldspecs:
        rows.append(get_cris_dd_row(taskname, tablename, fs))
    return rows
