#!/usr/bin/env python
# camcops_server/cc_modules/cc_filename.py

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

import datetime
import os
from typing import List, TYPE_CHECKING, Union

from cardinal_pythonlib.stringfunc import mangle_unicode_to_ascii

from .cc_dt import format_datetime, get_now_localtz
from .cc_constants import (
    DATEFORMAT,
    FP_ID_NUM,
    FP_ID_SHORT_DESC,
)

if TYPE_CHECKING:
    from .cc_patientidnum import PatientIdNum


# =============================================================================
# Ancillary functions for export filenames
# =============================================================================

def patient_spec_for_filename_is_valid(patient_spec: str,
                                       valid_which_idnums: List[int]) -> bool:
    """Returns True if the patient_spec appears valid; otherwise False."""
    testdict = dict(
        surname="surname",
        forename="forename",
        dob="dob",
        sex="sex",
        allidnums="allidnums",
    )
    for n in valid_which_idnums:
        nstr = str(n)
        testdict[FP_ID_SHORT_DESC + nstr] = FP_ID_SHORT_DESC + nstr
        testdict[FP_ID_NUM + nstr] = FP_ID_NUM + nstr
    # noinspection PyBroadException
    try:
        # Legal substitutions only?
        patient_spec.format(**testdict)
        return True
    except:  # duff patient_spec; details unimportant
        return False


def filename_spec_is_valid(filename_spec: str,
                           valid_which_idnums: List[int]) -> bool:
    """Returns True if the filename_spec appears valid; otherwise False."""
    testdict = dict(
        # As above:
        surname="surname",
        forename="forename",
        dob="dob",
        sex="sex",
        allidnums="allidnums",
        # Plus:
        patient="patient",
        created="created",
        now="now",
        tasktype="tasktype",
        serverpk="serverpk",
        filetype="filetype",
        anonymous="anonymous",
    )
    for n in valid_which_idnums:
        nstr = str(n)
        testdict[FP_ID_SHORT_DESC + nstr] = FP_ID_SHORT_DESC + nstr
        testdict[FP_ID_NUM + nstr] = FP_ID_NUM + nstr
    # noinspection PyBroadException
    try:
        # Legal substitutions only?
        filename_spec.format(**testdict)
        return True
    except:  # duff filename_spec; details unimportant
        return False


def get_export_filename(patient_spec_if_anonymous: str,
                        patient_spec: str,
                        filename_spec: str,
                        task_format: str,
                        is_anonymous: bool = False,
                        surname: str = None,
                        forename: str = None,
                        dob: Union[datetime.date, datetime.datetime] = None,
                        sex: str = None,
                        idnum_objects: List['PatientIdNum'] = None,
                        creation_datetime: datetime.datetime = None,
                        basetable: str = None,
                        serverpk: int = None) -> str:
    """Get filename, for file exports/transfers."""
    idnum_objects = idnum_objects or []  # type: List['PatientIdNum']
    d = dict(
        surname=surname or "",
        forename=forename or "",
        dob=(
            format_datetime(dob, DATEFORMAT.FILENAME_DATE_ONLY, "")
            if dob else ""
        ),
        sex=sex or "",
    )
    all_id_components = []
    for idobj in idnum_objects:
        if idobj.which_idnum is not None:
            nstr = str(idobj.which_idnum)
            has_num = idobj.idnum_value is not None
            d[FP_ID_NUM + nstr] = str(idobj.idnum_value) if has_num else ""
            d[FP_ID_SHORT_DESC + nstr] = idobj.short_description() or ""
            if has_num and idobj.short_description():
                all_id_components.append(idobj.get_filename_component())
    d["allidnums"] = "_".join(all_id_components)
    if is_anonymous:
        patient = patient_spec_if_anonymous
    else:
        patient = str(patient_spec).format(**d)
    d.update(dict(
        patient=patient,
        created=format_datetime(creation_datetime, DATEFORMAT.FILENAME, ""),
        now=format_datetime(get_now_localtz(), DATEFORMAT.FILENAME),
        tasktype=str(basetable or ""),
        serverpk=str(serverpk or ""),
        filetype=task_format.lower(),
        anonymous=patient_spec_if_anonymous if is_anonymous else "",
    ))
    return convert_string_for_filename(
        str(filename_spec).format(**d), allow_paths=True)


def convert_string_for_filename(s: str, allow_paths: bool = False) -> str:
    """Remove characters that don't play nicely in filenames across multiple
    operating systems."""
    # http://stackoverflow.com/questions/7406102
    # ... modified
    s = mangle_unicode_to_ascii(s)
    s = s.replace(" ", "_")
    keepcharacters = ['.', '_', '-']
    if allow_paths:
        keepcharacters.extend([os.sep])  # '/' under UNIX; '\' under Windows
    s = "".join(c for c in s if c.isalnum() or c in keepcharacters)
    return s


def change_filename_ext(filename: str, new_extension_with_dot: str) -> str:
    """Replaces the extension, i.e. the part of the filename after its last
    '.'."""
    (root, ext) = os.path.splitext(filename)
    # ... converts "blah.blah.txt" to ("blah.blah", ".txt")
    return root + new_extension_with_dot
