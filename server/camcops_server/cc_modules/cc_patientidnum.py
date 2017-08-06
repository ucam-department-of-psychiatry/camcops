#!/usr/bin/env python
# camcops_server/cc_modules/cc_patientidnum.py

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
import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.sql.schema import Column

from .cc_constants import FP_ID_NUM
from .cc_db import GenericTabletRecordMixin
from .cc_sqla_coltypes import (
    BigIntUnsigned,
    CamcopsColumn,
    IntUnsigned,
)
from .cc_sqlalchemy import Base

if TYPE_CHECKING:
    from .cc_config import CamcopsConfig

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# PatientIdNum class
# =============================================================================

class PatientIdNum(GenericTabletRecordMixin, Base):
    __tablename__ = "patient_idnum"

    id = Column(
        "id", IntUnsigned,
        nullable=False,
        comment="Primary key on the source tablet device"
    )
    patient_id = Column(
        "patient_id", IntUnsigned,
        nullable=False,
        comment="FK to patient.id (for this device/era)"
    )
    which_idnum = Column(
        "which_idnum", IntUnsigned,
        nullable=False,
        comment="Which of the server's ID numbers is this?"
    )
    idnum_value = CamcopsColumn(
        "idnum_value", BigIntUnsigned,
        anon=True,
        comment="The value of the ID number"
    )

    def description(self, cfg: CamcopsConfig) -> str:
        which_idnum = self.which_idnum  # type: int
        return cfg.get_id_desc(which_idnum, default="?")

    def short_description(self, cfg: CamcopsConfig) -> str:
        which_idnum = self.which_idnum  # type: int
        return cfg.get_id_shortdesc(which_idnum, default="?")

    def get_html(self, cfg: CamcopsConfig,
                 longform: bool, label_id_numbers: bool = False) -> str:
        """
        Returns description HTML.

        Args:
            cfg: CamcopsConfig instance
            longform: verbose (for most HTML) or not (for PDF headers)
            label_id_numbers: whether to use prefix
        """
        if self.which_idnum is None:
            return ""
        nstr = str(self.which_idnum)  # which ID number?
        prefix = ("<i>(" + FP_ID_NUM + nstr + ")</i> "
                  if label_id_numbers else "")
        if longform:
            return "<br>{}{}: <b>{}</b>".format(
                prefix,
                ws.webify(self.description(cfg)),
                self.idnum_value
            )
        else:
            return "{}{}: {}.".format(
                prefix,
                ws.webify(self.short_description(cfg)),
                self.idnum_value
            )

    def get_filename_component(self, cfg: CamcopsConfig) -> str:
        if self.which_idnum is None or self.idnum_value is None:
            return ""
        return "{}-{}".format(self.short_description(cfg),
                              self.idnum_value)

    def set_idnum(self, idnum_value: int) -> None:
        self.idnum_value = idnum_value
