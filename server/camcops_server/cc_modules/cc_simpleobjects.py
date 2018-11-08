#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_simpleobjects.py

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

**Simple struct-like classes.**

"""

from typing import List, TYPE_CHECKING

from pendulum import Date

from cardinal_pythonlib.reprfunc import auto_repr

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

    It's not stored in the database -- it's just an object to be passed around
    that encapsulates ``which_idnum`` and ``idnum_value``.

    As an example, suppose our administrator has defined ID type
    (``which_idnum``) 7 to be "NHS number". Then if a patient has NHS number
    9999999999, we might represent this ID of theirs as
    ``IdNumReference(which_idnum=7, idnum_value=9999999999)``.
    """
    def __init__(self, which_idnum: int, idnum_value: int) -> None:
        self.which_idnum = which_idnum
        self.idnum_value = idnum_value

    def __repr__(self) -> str:
        return auto_repr(self)

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
    """
    Represents a patient identifier for the HL7 protocol.
    """
    def __init__(self, id: str, id_type: str,
                 assigning_authority: str) -> None:
        self.id = id
        self.id_type = id_type
        self.assigning_authority = assigning_authority


# =============================================================================
# BarePatientInfo
# =============================================================================

class BarePatientInfo(object):
    """
    Represents information about a patient using a simple object with no
    connection to a database.

    In some situations we avoid using
    :class:`camcops_server.cc_modules.cc_patient.Patient`: specifically, when
    we would otherwise have to deal with mutual dependency problems and the use
    of the database (prior to full database initialization).
    """
    def __init__(self,
                 forename: str = None,
                 surname: str = None,
                 sex: str = None,
                 dob: Date = None,
                 address: str = None,
                 gp: str = None,
                 other: str = None,
                 idnum_definitions: List[IdNumReference] = None) -> None:
        self.forename = forename
        self.surname = surname
        self.sex = sex
        self.dob = dob
        self.address = address
        self.gp = gp
        self.otherdetails = other
        self.idnum_definitions = idnum_definitions or []  # type: List[IdNumReference]  # noqa

    def __repr__(self) -> str:
        return auto_repr(self)


# =============================================================================
# Raw XML value
# =============================================================================

class XmlSimpleValue(object):
    """
    Represents XML lowest-level items. See functions in ``cc_xml.py``.
    """
    def __init__(self, value) -> None:
        self.value = value
