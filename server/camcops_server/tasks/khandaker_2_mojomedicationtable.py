#!/usr/bin/env python

"""
camcops_server/tasks/khandaker_2_mojomedicationtable.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_db import (
    ancillary_relationship,
    GenericTabletRecordMixin,
    TaskDescendant,
)
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
)
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
)


class Khandaker2MojoMedicationItem(GenericTabletRecordMixin, Base,
                                   TaskDescendant):
    __tablename__ = "khandaker_2_mojomedication_item"

    medicationtable_id = CamcopsColumn(
        "medicationtable_id", Integer, nullable=False,
        comment="FK to medicationtable"
    )

    seqnum = CamcopsColumn(
        "seqnum", Integer, nullable=False,
        comment="Sequence number of this medication"
    )

    medication_name = CamcopsColumn(
        "medication_name", UnicodeText,
        comment="Medication name"
    )

    chemical_name = CamcopsColumn(
        "chemical_name", UnicodeText,
        comment="Chemical name for study team"
    )

    dosage = CamcopsColumn(
        "dosage", UnicodeText,
        comment="Dosage"
    )

    duration = CamcopsColumn(
        "duration", Integer,
        comment="Duration (months)"
    )

    indication = CamcopsColumn(
        "indication", UnicodeText,
        comment="Indication (what is the medication used for?)"
    )

    response = CamcopsColumn(
        "response", Integer,
        comment=("1 = treats all symptoms, "
                 "2 = most symptoms, "
                 "3 = some symptoms, "
                 "4 = no symptoms)")
    )


class Khandaker2MojoMedicationTable(TaskHasPatientMixin, Task):
    """
    Server implementation of the Khandaker_2_MOJOMedicationTable task
    """
    __tablename__ = "khandaker_2_mojomedicationtable"
    shortname = "Khandaker_2_MOJOMedicationTable"
    provides_trackers = False  # TODO: Check

    items = ancillary_relationship(
        parent_class_name="Khandaker2MojoMedicationTable",
        ancillary_class_name="Khandaker2MojoMedicationItem",
        ancillary_fk_to_parent_attr_name="medicationtable_id",
        ancillary_order_by_attr_name="seqnum"
    )

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Khandaker GM — 2 MOJO Study — Medications and Treatment")
