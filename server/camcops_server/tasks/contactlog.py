"""
camcops_server/tasks/contactlog.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

"""

from typing import List, Optional

from cardinal_pythonlib.datetimefunc import format_datetime, get_duration_h_m
import cardinal_pythonlib.rnc_web as ws
from pendulum import DateTime as Pendulum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass, DateFormat
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_html import (
    italic,
    get_yes_no_none,
    tr,
    tr_qa,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    mapped_camcops_column,
    BIT_CHECKER,
    PendulumDateTimeAsIsoTextColType,
)
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)


# =============================================================================
# ContactLog
# =============================================================================


class ContactLog(TaskHasClinicianMixin, TaskHasPatientMixin, Task):  # type: ignore[misc]  # noqa: E501
    """
    Server implementation of the ContactLog task.
    """

    __tablename__ = "contactlog"
    shortname = "ContactLog"
    info_filename_stem = "clinical"

    location: Mapped[Optional[str]] = mapped_column(
        UnicodeText, comment="Location"
    )
    start: Mapped[Optional[Pendulum]] = mapped_column(
        PendulumDateTimeAsIsoTextColType,
        comment="Date/time that contact started",
    )
    end: Mapped[Optional[Pendulum]] = mapped_column(
        "end",
        PendulumDateTimeAsIsoTextColType,
        comment="Date/time that contact ended",
    )
    patient_contact: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=BIT_CHECKER,
        comment="Patient contact involved (0 no, 1 yes)?",
    )
    staff_liaison: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=BIT_CHECKER,
        comment="Liaison with staff involved (0 no, 1 yes)?",
    )
    other_liaison: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=BIT_CHECKER,
        comment="Liaison with others (e.g. family) involved (0 no, 1 yes)?",
    )
    comment: Mapped[Optional[str]] = mapped_column(
        "comment", UnicodeText, comment="Comment"
    )

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Clinical contact log")

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        contact_type = "Patient" if self.patient_contact else "Non-patient"
        return [
            CtvInfo(
                content=(
                    f"{contact_type} contact. Duration (hours:minutes) "
                    f"{get_duration_h_m(self.start, self.end)}."
                )
            )
        ]

    def is_complete(self) -> bool:
        return (
            self.start is not None
            and self.end is not None
            and self.field_contents_valid()
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        return f"""
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <td width="33%">Location:</td>
                    <td width="67%"><b>{ws.webify(self.location)}</b></td>
                </tr>
                {tr_qa("Start:", format_datetime(self.start,
                                                 DateFormat.SHORT_DATETIME,
                                                 None))}
                {tr_qa("End:", format_datetime(self.end,
                                               DateFormat.SHORT_DATETIME,
                                               None))}
                {tr(italic("Calculated duration (hours:minutes)"),
                    italic(get_duration_h_m(self.start, self.end)))}
                {tr_qa("Patient contact?",
                       get_yes_no_none(req, self.patient_contact))}
                {tr_qa("Staff liaison?",
                       get_yes_no_none(req, self.staff_liaison))}
                {tr_qa("Other liaison?",
                       get_yes_no_none(req, self.other_liaison))}
                {tr_qa("Comment:", self.comment)}
            </table>
        """
