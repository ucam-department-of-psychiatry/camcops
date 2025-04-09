"""
camcops_server/tasks/srs.py

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

- By Joe Kearney, Rudolf Cardinal.

"""

import datetime
from typing import List, Optional

from sqlalchemy.orm import Mapped

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    mapped_camcops_column,
    ZERO_TO_10_CHECKER,
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin


# =============================================================================
# SRS
# =============================================================================


class Srs(TaskHasPatientMixin, Task):  # type: ignore[misc]
    """
    Server implementation of the SRS task.
    """

    __tablename__ = "srs"
    shortname = "SRS"
    provides_trackers = True

    COMPLETED_BY_SELF = 0
    COMPLETED_BY_OTHER = 1

    VAS_MIN_INT = 0
    VAS_MAX_INT = 10

    q_session: Mapped[Optional[int]] = mapped_camcops_column(
        comment="Session number"
    )
    q_date: Mapped[Optional[datetime.date]] = mapped_camcops_column(
        comment="Session date"
    )
    q_relationship: Mapped[Optional[float]] = mapped_camcops_column(
        comment="Rating of patient-therapist relationship (0-10, 10 better)",
        permitted_value_checker=ZERO_TO_10_CHECKER,
    )
    q_goals: Mapped[Optional[float]] = mapped_camcops_column(
        comment="Rating for topics discussed (0-10, 10 better)",
        permitted_value_checker=ZERO_TO_10_CHECKER,
    )
    q_approach: Mapped[Optional[float]] = mapped_camcops_column(
        comment="Rating for therapist's approach (0-10, 10 better)",
        permitted_value_checker=ZERO_TO_10_CHECKER,
    )
    q_overall: Mapped[Optional[float]] = mapped_camcops_column(
        comment="Overall rating (0-10, 10 better)",
        permitted_value_checker=ZERO_TO_10_CHECKER,
    )

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Session Rating Scale")

    def is_complete(self) -> bool:
        required_always = [
            "q_session",
            "q_date",
            "q_relationship",
            "q_goals",
            "q_approach",
            "q_overall",
        ]
        for field in required_always:
            if getattr(self, field) is None:
                return False
        return True

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def get_task_html(self, req: CamcopsRequest) -> str:
        fields = ["q_relationship", "q_goals", "q_approach", "q_overall"]
        q_a = ""
        for field in fields:
            question = field.split("_")[1].capitalize()
            q_a += tr_qa(question, getattr(self, field))

        return f"""
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {self.get_is_complete_tr(req)}
                    {tr_qa("Session number", self.q_session)}
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                Scores represent a selection on a scale from
                {self.VAS_MIN_INT} to {self.VAS_MAX_INT}
                ({self.VAS_MAX_INT} better). Scores indicate the patient’s
                feelings about different aspects of the day’s therapy session.
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
            </div>
        """
