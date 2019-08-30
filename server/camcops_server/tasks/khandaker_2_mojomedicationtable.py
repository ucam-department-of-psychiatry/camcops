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
from typing import List, Optional, Type

from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import (
    ancillary_relationship,
    GenericTabletRecordMixin,
    TaskDescendant,
)
from camcops_server.cc_modules.cc_html import answer, tr_qa
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
)
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
)


class Khandaker2MojoTableItem(GenericTabletRecordMixin, TaskDescendant):
    def any_fields_none(self) -> bool:
        for f in self.mandatory_fields():
            if getattr(self, f) is None:
                return True
        return False

    @classmethod
    def mandatory_fields(self) -> List[str]:
        raise NotImplementedError

    def get_response_option(self, req: "CamcopsRequest") -> str:
        if self.response is None:
            return None

        return self.task_ancestor().xstring(req, f"response_{self.response}")

    # -------------------------------------------------------------------------
    # TaskDescendant overrides
    # -------------------------------------------------------------------------

    @classmethod
    def task_ancestor_class(cls) -> Optional[Type["Task"]]:
        return Khandaker2MojoMedicationTable

    def task_ancestor(self) -> Optional["Khandaker2MojoMedicationTable"]:
        return Khandaker2MojoMedicationTable.get_linked(
            self.medicationtable_id, self)


class Khandaker2MojoMedicationItem(Khandaker2MojoTableItem, Base):
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

    frequency = CamcopsColumn(
        "frequency", UnicodeText,
        comment="Frequency"
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

    @classmethod
    def mandatory_fields(self) -> List[str]:
        return [
            "medication_name",
            "chemical_name",
            "dosage",
            "frequency",
            "duration",
            "indication",
            "response",
        ]

    def get_html_table_row(self, req: "CamcopsRequest") -> str:
        return f"""
            <tr>
                <td>{answer(self.medication_name)}</td>
                <td>{answer(self.chemical_name)}</td>
                <td>{answer(self.dosage)}</td>
                <td>{answer(self.frequency)}</td>
                <td>{answer(self.duration)}</td>
                <td>{answer(self.indication)}</td>
                <td>{answer(self.get_response_option(req))}</td>
            </tr>
        """


class Khandaker2MojoTherapyItem(Khandaker2MojoTableItem, Base):
    __tablename__ = "khandaker_2_mojotherapy_item"

    medicationtable_id = CamcopsColumn(
        "medicationtable_id", Integer, nullable=False,
        comment="FK to medicationtable"
    )

    seqnum = CamcopsColumn(
        "seqnum", Integer, nullable=False,
        comment="Sequence number of this therapy"
    )

    therapy = CamcopsColumn(
        "therapy", UnicodeText,
        comment="Therapy"
    )

    frequency_per_week = CamcopsColumn(
        "frequency_per_week", Integer,
        comment="Frequency (per week)"
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

    @classmethod
    def mandatory_fields(self) -> List[str]:
        return [
            "therapy",
            "frequency_per_week",
            "duration",
            "indication",
            "response",
        ]

    def get_html_table_row(self, req: "CamcopsRequest") -> str:
        return f"""
            <tr>
                <td>{answer(self.therapy)}</td>
                <td>{answer(self.frequency_per_week)}</td>
                <td>{answer(self.duration)}</td>
                <td>{answer(self.indication)}</td>
                <td>{answer(self.get_response_option(req))}</td>
            </tr>
        """


class Khandaker2MojoMedicationTable(TaskHasPatientMixin, Task):
    """
    Server implementation of the Khandaker_2_MOJOMedicationTable task
    """
    __tablename__ = "khandaker_2_mojomedicationtable"
    shortname = "Khandaker_2_MOJOMedicationTable"
    provides_trackers = False

    medication_items = ancillary_relationship(
        parent_class_name="Khandaker2MojoMedicationTable",
        ancillary_class_name="Khandaker2MojoMedicationItem",
        ancillary_fk_to_parent_attr_name="medicationtable_id",
        ancillary_order_by_attr_name="seqnum"
    )

    therapy_items = ancillary_relationship(
        parent_class_name="Khandaker2MojoMedicationTable",
        ancillary_class_name="Khandaker2MojoTherapyItem",
        ancillary_fk_to_parent_attr_name="medicationtable_id",
        ancillary_order_by_attr_name="seqnum"
    )

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Khandaker GM — 2 MOJO Study — Medications and Treatment")

    def is_complete(self) -> bool:
        # Whilst it's almost certain that anyone completing this task would be
        # on some kind of medication, we have no way of knowing when all
        # medication has been added to the table
        for item in self.medication_items:
            if item.any_fields_none():
                return False

        for item in self.therapy_items:
            if item.any_fields_none():
                return False

        return True

    def get_num_medication_items(self) -> int:
        return len(self.medication_items)

    def get_num_therapy_items(self) -> int:
        return len(self.therapy_items)

    def get_task_html(self, req: "CamcopsRequest") -> str:
        html = f"""
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {self.get_is_complete_tr(req)}
                    {tr_qa("Number of medications",
                            self.get_num_medication_items())}
                    {tr_qa("Number of therapies",
                            self.get_num_therapy_items())}
                </table>
            </div>

            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th>{self.xstring(req, "medication_name")}</th>
                    <th>{self.xstring(req, "chemical_name")}</th>
                    <th>{self.xstring(req, "dosage")}</th>
                    <th>{self.xstring(req, "frequency")}</th>
                    <th>{self.xstring(req, "duration")}</th>
                    <th>{self.xstring(req, "indication")}</th>
                    <th>{self.xstring(req, "response")}</th>
                </tr>
        """
        for item in self.medication_items:
            html += item.get_html_table_row(req)

        html += f"""
            </table>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th>{self.xstring(req, "therapy")}</th>
                    <th>{self.xstring(req, "frequency_per_week")}</th>
                    <th>{self.xstring(req, "duration")}</th>
                    <th>{self.xstring(req, "indication")}</th>
                    <th>{self.xstring(req, "response")}</th>
                </tr>
        """

        for item in self.therapy_items:
            html += item.get_html_table_row(req)

        html += f"""
            </table>
        """

        return html
