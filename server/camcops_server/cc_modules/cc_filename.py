#!/usr/bin/env python
# camcops_server/cc_modules/cc_filename.py

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

import logging
import os
from typing import List, TYPE_CHECKING

from cardinal_pythonlib.datetimefunc import (
    format_datetime,
    get_now_localtz_pendulum,
)
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.stringfunc import mangle_unicode_to_ascii
from pendulum import Date, DateTime as Pendulum

from .cc_constants import DateFormat

if TYPE_CHECKING:
    from .cc_patientidnum import PatientIdNum
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Ancillary functions for export filenames
# =============================================================================

class FileType(object):
    HTML = "html"
    PDF = "pdf"
    XML = "xml"


class PatientSpecElementForFilename(object):
    SURNAME = "surname"
    FORENAME = "forename"
    DOB = "dob"
    SEX = "sex"
    ALLIDNUMS = "allidnums"
    IDSHORTDESC_PREFIX = "idshortdesc"  # special
    IDNUM_PREFIX = "idnum"  # special


class FilenameSpecElement(object):
    PATIENT = "patient"
    CREATED = "created"
    NOW = "now"
    TASKTYPE = "tasktype"
    SERVERPK = "serverpk"
    FILETYPE = "filetype"
    ANONYMOUS = "anonymous"
    # ... plus all those from PatientSpecElementForFilename


def patient_spec_for_filename_is_valid(patient_spec: str,
                                       valid_which_idnums: List[int]) -> bool:
    """Returns True if the patient_spec appears valid; otherwise False."""
    pse = PatientSpecElementForFilename
    testdict = {
        pse.SURNAME: "surname",
        pse.FORENAME: "forename",
        pse.DOB: "dob",
        pse.SEX: "sex",
        pse.ALLIDNUMS: "allidnums",
    }
    for n in valid_which_idnums:
        nstr = str(n)
        testdict[pse.IDSHORTDESC_PREFIX + nstr] = pse.IDSHORTDESC_PREFIX + nstr
        testdict[pse.IDNUM_PREFIX + nstr] = pse.IDNUM_PREFIX + nstr
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
    pse = PatientSpecElementForFilename
    fse = FilenameSpecElement
    testdict = {
        # As above:
        pse.SURNAME: "surname",
        pse.FORENAME: "forename",
        pse.DOB: "dob",
        pse.SEX: "sex",
        pse.ALLIDNUMS: "allidnums",
        # Plus:
        fse.PATIENT: "patient",
        fse.CREATED: "created",
        fse.NOW: "now",
        fse.TASKTYPE: "tasktype",
        fse.SERVERPK: "serverpk",
        fse.FILETYPE: "filetype",
        fse.ANONYMOUS: "anonymous",
    }
    for n in valid_which_idnums:
        nstr = str(n)
        testdict[pse.IDSHORTDESC_PREFIX + nstr] = pse.IDSHORTDESC_PREFIX + nstr
        testdict[pse.IDNUM_PREFIX + nstr] = pse.IDNUM_PREFIX + nstr
    # noinspection PyBroadException
    try:
        # Legal substitutions only?
        filename_spec.format(**testdict)
        return True
    except:  # duff filename_spec; details unimportant
        return False


FORMAT_FAIL_EXCEPTIONS = (IndexError, KeyError)


def get_export_filename(req: "CamcopsRequest",
                        patient_spec_if_anonymous: str,
                        patient_spec: str,
                        filename_spec: str,
                        task_format: str,
                        is_anonymous: bool = False,
                        surname: str = None,
                        forename: str = None,
                        dob: Date = None,
                        sex: str = None,
                        idnum_objects: List['PatientIdNum'] = None,
                        creation_datetime: Pendulum = None,
                        basetable: str = None,
                        serverpk: int = None) -> str:
    """Get filename, for file exports/transfers."""
    idnum_objects = idnum_objects or []  # type: List['PatientIdNum']
    pse = PatientSpecElementForFilename
    fse = FilenameSpecElement
    d = {
        pse.SURNAME: surname or "",
        pse.FORENAME: forename or "",
        pse.DOB: (
            format_datetime(dob, DateFormat.FILENAME_DATE_ONLY, "")
            if dob else ""
        ),
        pse.SEX: sex or "",
    }
    all_id_components = []
    for idobj in idnum_objects:
        if idobj.which_idnum is not None:
            nstr = str(idobj.which_idnum)
            has_num = idobj.idnum_value is not None
            d[pse.IDNUM_PREFIX + nstr] = str(idobj.idnum_value) if has_num else ""  # noqa
            d[pse.IDSHORTDESC_PREFIX + nstr] = idobj.short_description(req) or ""  # noqa
            if has_num and idobj.short_description(req):
                all_id_components.append(idobj.get_filename_component(req))
    d[pse.ALLIDNUMS] = "_".join(all_id_components)
    if is_anonymous:
        patient = patient_spec_if_anonymous
    else:
        try:
            patient = str(patient_spec).format(**d)
        except FORMAT_FAIL_EXCEPTIONS:
            log.warning("Bad patient_spec: {!r}", patient_spec)
            patient = "invalid_patient_spec"
    d.update({
        fse.PATIENT: patient,
        fse.CREATED: format_datetime(creation_datetime,
                                     DateFormat.FILENAME, ""),
        fse.NOW: format_datetime(get_now_localtz_pendulum(),
                                 DateFormat.FILENAME),
        fse.TASKTYPE: str(basetable or ""),
        fse.SERVERPK: str(serverpk or ""),
        fse.FILETYPE: task_format.lower(),
        fse.ANONYMOUS: patient_spec_if_anonymous if is_anonymous else "",
    })
    try:
        formatted = str(filename_spec).format(**d)
    except FORMAT_FAIL_EXCEPTIONS:
        log.warning("Bad filename_spec: {!r}", filename_spec)
        formatted = "invalid_filename_spec"
    return convert_string_for_filename(formatted, allow_paths=True)


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
