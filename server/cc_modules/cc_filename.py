#!/usr/bin/env python3
# cc_filename.py

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

import os

from cc_constants import DATEFORMAT, NUMBER_OF_IDNUMS
import cc_dt
import cc_lang


# =============================================================================
# Ancillary functions for export filenames
# =============================================================================

def patient_spec_for_filename_is_valid(patient_spec):
    """Returns True if the patient_spec appears valid; otherwise False."""
    testdict = dict(
        surname="surname",
        forename="forename",
        dob="dob",
        sex="sex",
        allidnums="allidnums",
    )
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        nstr = str(n)
        testdict["idshortdesc"+nstr] = "idshortdesc"+nstr
        testdict["idnum"+nstr] = "idnum"+nstr
    try:
        # Legal substitutions only?
        patient_spec.format(**testdict)
        return True
    except:  # duff patient_spec; details unimportant
        return False


def filename_spec_is_valid(filename_spec):
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
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        nstr = str(n)
        testdict["idshortdesc"+nstr] = "idshortdesc"+nstr
        testdict["idnum"+nstr] = "idnum"+nstr
    try:
        # Legal substitutions only?
        filename_spec.format(**testdict)
        return True
    except:  # duff filename_spec; details unimportant
        return False


def get_export_filename(patient_spec_if_anonymous, patient_spec,
                        filename_spec, task_format,
                        is_anonymous=False,
                        surname=None, forename=None, dob=None, sex=None,
                        idnums=[None]*NUMBER_OF_IDNUMS,
                        idshortdescs=[""]*NUMBER_OF_IDNUMS,
                        creation_datetime=None, basetable=None, serverpk=None):
    """Get filename, for file exports/transfers."""
    if idnums is None:
        idnums = [None]*NUMBER_OF_IDNUMS
    if idshortdescs is None:
        idshortdescs = [""]*NUMBER_OF_IDNUMS
    d = dict(
        surname=surname or "",
        forename=forename or "",
        dob=(
            cc_dt.format_datetime(dob, DATEFORMAT.FILENAME_DATE_ONLY, "")
            if dob else ""
        ),
        sex=sex or "",
    )
    all_id_components = []
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        i = n - 1
        nstr = str(n)
        has_num = idnums[i] is not None
        has_desc = bool(idshortdescs[i])
        d["idshortdesc"+nstr] = idshortdescs[i] if has_num and has_desc else ""
        d["idnum"+nstr] = str(idnums[i]) if has_num else ""
        if has_num and has_desc:
            all_id_components.append(idshortdescs[i] + "-" + str(idnums[i]))
    d["allidnums"] = "_".join(all_id_components)
    if is_anonymous:
        patient = patient_spec_if_anonymous
    else:
        patient = unicode(patient_spec).format(**d)
    d.update(dict(
        patient=patient,
        created=cc_dt.format_datetime(creation_datetime,
                                      DATEFORMAT.FILENAME, ""),
        now=cc_dt.format_datetime(cc_dt.get_now_localtz(),
                                  DATEFORMAT.FILENAME),
        tasktype=str(basetable or ""),
        serverpk=str(serverpk or ""),
        filetype=task_format.lower(),
        anonymous=patient_spec_if_anonymous if is_anonymous else "",
    ))
    return convert_string_for_filename(
        unicode(filename_spec).format(**d), allow_paths=True)


def convert_string_for_filename(s, allow_paths=False):
    """Remove characters that don't play nicely in filenames across multiple
    operating systems."""
    # http://stackoverflow.com/questions/7406102
    # ... modified
    s = cc_lang.mangle_unicode_to_str(s)
    s = s.replace(" ", "_")
    keepcharacters = ['.', '_', '-']
    if allow_paths:
        keepcharacters.extend([os.sep])  # '/' under UNIX; '\' under Windows
    s = "".join(c for c in s if c.isalnum() or c in keepcharacters)
    return s


def change_filename_ext(filename, new_extension_with_dot):
    """Replaces the extension, i.e. the part of the filename after its last
    '.'."""
    (root, ext) = os.path.splitext(filename)
    # ... converts "blah.blah.txt" to ("blah.blah", ".txt")
    return root + new_extension_with_dot
