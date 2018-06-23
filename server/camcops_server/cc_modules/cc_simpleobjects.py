#!/usr/bin/env python
# camcops_server/cc_modules/cc_simpleobjects.py

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

from typing import List, TYPE_CHECKING

from cardinal_pythonlib.reprfunc import simple_repr
from pendulum import Date

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest

# Prefer classes to collections.namedtuple; both support type checking but
# classes support better parameter checking (and refactoring) via PyCharm.


# =============================================================================
# IdNumReference
# =============================================================================

class IdNumReference(object):
    """
    A simple way of referring to an ID number.
    Not stored in the database - just an object to be passed around that
    encapsulates which_idnum and idnum_value.
    """
    def __init__(self, which_idnum: int, idnum_value: int) -> None:
        self.which_idnum = which_idnum
        self.idnum_value = idnum_value

    def is_valid(self) -> bool:
        return (
            self.which_idnum is not None and self.which_idnum > 0 and
            self.idnum_value is not None and self.idnum_value > 0
        )

    def __eq__(self, other: "IdNumReference") -> bool:
        if not isinstance(other, IdNumReference):
            return False
        return (
            self.which_idnum == other.which_idnum and
            self.idnum_value == other.idnum_value
        )

    def description(self, req: "CamcopsRequest") -> str:
        if not self.is_valid():
            return "[invalid_IdNumReference]"
        return "{d} = {v}".format(d=req.get_id_shortdesc(self.which_idnum),
                                  v=self.idnum_value)


# =============================================================================
# HL7PatientIdentifier
# =============================================================================

# noinspection PyShadowingBuiltins
class HL7PatientIdentifier(object):
    def __init__(self, id: str, id_type: str,
                 assigning_authority: str) -> None:
        self.id = id
        self.id_type = id_type
        self.assigning_authority = assigning_authority


# =============================================================================
# BarePatientInfo
# =============================================================================
# We avoid using Patient because otherwise we have to deal
# with mutual dependency problems and the use of the database (prior to full
# database initialization)

class BarePatientInfo(object):
    def __init__(self,
                 forename: str = None,
                 surname: str = None,
                 dob: Date = None,
                 sex: str = None,
                 idnum_definitions: List[IdNumReference] = None) -> None:
        self.forename = forename
        self.surname = surname
        self.dob = dob
        self.sex = sex
        self.idnum_definitions = idnum_definitions or []  # type: List[IdNumReference]  # noqa


# =============================================================================
# Raw XML value
# =============================================================================

class XmlSimpleValue(object):
    """
    Represents XML lowest-level items. See functions in cc_xml.py
    """
    def __init__(self, value) -> None:
        self.value = value


# =============================================================================
# IntrospectionFileDetails
# =============================================================================

class IntrospectionFileDetails(object):
    def __init__(self, fullpath: str, prettypath: str, ext: str) -> None:
        self.fullpath = fullpath
        self.prettypath = prettypath
        self.ext = ext

    def __repr__(self) -> str:
        return simple_repr(self, ["prettypath", "ext", "fullpath"],
                           with_addr=False)
