#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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


# =============================================================================
# Processing names
# =============================================================================

TITLES = [
    "DR",
    "PROF",
    "MR",
    "MISS",
    "MRS",
    "MS",
    "SR"
]


def guess_name_components(s, uppercase=True):
    """Takes a string such as 'Dr James T. Smith, M.D.' and returns parts.

    This will not be perfect! If it isn't reasonably sure, it returns
    everything in the surname field.

    Examples it will fail on:
        Nurse Specialist Jones

    Returns:
        dictionary with members: "surname", "forename", "prefix"
    """
    # Hard.
    # http://stackoverflow.com/questions/4276905/

    prefix = ""
    forename = ""
    surname = ""

    # 1. Separate on spaces, chucking any blanks
    if s:
        parts = [p for p in s.split(" ") if p]
    else:
        parts = []

    # 2. Prefix?
    if len(parts) > 0:
        p = parts[0]
        if ("." in p or p.replace(".", "").upper() in TITLES):
            prefix = p
            parts = parts[1:]

    # 3. Forename, surname
    if len(parts) == 2:
        if parts[0][-1] == ",":  # SURNAME, FORENAME
            forename = parts[1]
            surname = parts[0]
        else:  # FORENAME SURNAME
            forename = parts[0]
            surname = parts[1]
    else:  # No idea, really; shove it all in the surname component.
        surname = " ".join(parts)

    if uppercase:
        surname = surname.upper()
        forename = forename.upper()
        prefix = prefix.upper()
    return dict(
        surname=surname,
        forename=forename,
        prefix=prefix
    )
