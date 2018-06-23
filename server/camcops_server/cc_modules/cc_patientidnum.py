#!/usr/bin/env python
# camcops_server/cc_modules/cc_patientidnum.py

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

We were looking up ID descriptors from the device's stored variables.
However, that is a bit of a nuisance for a server-side researcher, and
it's a pain to copy the server's storedvar values (and -- all or some?)
when a patient gets individually moved off the tablet. Anyway, they're
important, so a little repetition is not the end of the world. So,
let's have the tablet store its current ID descriptors in the patient
record at the point of upload, and then it's available here directly.
Thus, always complete and contemporaneous.

... DECISION CHANGED 2017-07-08; see justification in tablet
    overall_design.txt

"""

import logging
from typing import TYPE_CHECKING

from cardinal_pythonlib.logs import BraceStyleAdapter
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, Integer

from .cc_constants import NUMBER_OF_IDNUMS_DEFUNCT
from .cc_db import GenericTabletRecordMixin
from .cc_idnumdef import IdNumDefinition
from .cc_simpleobjects import IdNumReference
from .cc_sqla_coltypes import CamcopsColumn
from .cc_sqlalchemy import Base

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# PatientIdNum class
# =============================================================================
# Stores ID numbers for a specific patient

class PatientIdNum(GenericTabletRecordMixin, Base):
    __tablename__ = "patient_idnum"

    id = Column(
        "id", Integer,
        nullable=False,
        comment="Primary key on the source tablet device"
    )
    patient_id = Column(
        "patient_id", Integer,
        nullable=False,
        comment="FK to patient.id (for this device/era)"
    )
    which_idnum = Column(
        "which_idnum", Integer, ForeignKey(IdNumDefinition.which_idnum),
        nullable=False,
        comment="Which of the server's ID numbers is this?"
    )
    idnum_value = CamcopsColumn(
        "idnum_value", BigInteger,
        identifies_patient=True,
        comment="The value of the ID number"
    )

    def get_idnum_reference(self) -> IdNumReference:
        return IdNumReference(which_idnum=self.which_idnum,
                              idnum_value=self.idnum_value)

    def is_valid(self) -> bool:
        return (
            self.which_idnum is not None and
            self.idnum_value is not None and
            self.which_idnum >= 0 and
            self.idnum_value >= 0
        )

    def description(self, req: "CamcopsRequest") -> str:
        which_idnum = self.which_idnum  # type: int
        return req.get_id_desc(which_idnum, default="?")

    def short_description(self, req: "CamcopsRequest") -> str:
        which_idnum = self.which_idnum  # type: int
        return req.get_id_shortdesc(which_idnum, default="?")

    def get_filename_component(self, req: "CamcopsRequest") -> str:
        if self.which_idnum is None or self.idnum_value is None:
            return ""
        return "{}-{}".format(self.short_description(req),
                              self.idnum_value)

    def set_idnum(self, idnum_value: int) -> None:
        self.idnum_value = idnum_value


# =============================================================================
# Fake ID values when upgrading from old ID number system
# =============================================================================

def fake_tablet_id_for_patientidnum(patient_id: int, which_idnum: int) -> int:
    return patient_id * NUMBER_OF_IDNUMS_DEFUNCT + which_idnum
