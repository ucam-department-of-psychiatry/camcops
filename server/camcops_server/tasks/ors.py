#!/usr/bin/env python

"""
camcops_server/tasks/ors.py

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

from typing import List

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    ZERO_TO_10_CHECKER
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import (
    TrackerInfo,
)
from sqlalchemy.sql.sqltypes import Date, Float, Integer, UnicodeText


# =============================================================================
# ORS
# =============================================================================

class Ors(TaskHasPatientMixin, Task):
    """
    Server implementation of the PHQ9 task.
    """
    __tablename__ = "ors"
    shortname = "ORS"
    longname = "Outcome Rating Scale"
    provides_trackers = True

    COMPLETED_BY_SELF = 0
    COMPLETED_BY_OTHER = 1

    VAS_MIN_INT = 0
    VAS_MAX_INT = 10

    q_session = CamcopsColumn("q_session", Integer, comment="Session number")
    q_date = CamcopsColumn("q_date", Date, comment="Session date")
    q_who = CamcopsColumn("q_who", Integer, comment="Completed by")
    q_who_other = CamcopsColumn(
        "q_who_other", UnicodeText, comment="Completed by other: who?")
    q_individual = CamcopsColumn(
        "q_individual", Float,
        comment="Individual rating (0-10, 10 better)",
        permitted_value_checker=ZERO_TO_10_CHECKER)
    q_interpersonal = CamcopsColumn(
        "q_interpersonal", Float,
        comment="Interpersonal rating (0-10, 10 better)",
        permitted_value_checker=ZERO_TO_10_CHECKER)
    q_social = CamcopsColumn(
        "q_social", Float,
        comment="Social rating (0-10, 10 better)",
        permitted_value_checker=ZERO_TO_10_CHECKER)
    q_overall = CamcopsColumn(
        "q_overall", Float,
        comment="Overall rating (0-10, 10 better)",
        permitted_value_checker=ZERO_TO_10_CHECKER)

    def is_complete(self) -> bool:
        required_always = [
            "q_session",
            "q_date",
            "q_who",
            "q_individual",
            "q_interpersonal",
            "q_social",
            "q_overall",
        ]
        for field in required_always:
            if getattr(self, field) is None:
                return False
        if self.q_who == self.COMPLETED_BY_OTHER:
            if not self.q_who_other:
                return False
        return True

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def who(self) -> str:
        if self.q_who == self.COMPLETED_BY_OTHER:
            return "Other: " + (self.q_who_other or "Unknown")
        if self.q_who == self.COMPLETED_BY_SELF:
            return "Patient"
        return "Unknown"

    def get_task_html(self, req: CamcopsRequest) -> str:
        fields = ["q_individual", "q_interpersonal", "q_social", "q_overall"]
        q_a = ""
        for field in fields:
            question = field.split("_")[1].capitalize()
            q_a += tr_qa(question, getattr(self, field))

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {tr_session_number}
                    {tr_completed_by}
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                Scores represent a selection on a scale from {vas_min} to
                {vas_max} ({vas_max} better). Scores reflect the patient’s
                feelings about the indicated life areas over the past week.
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
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            tr_completed_by=tr_qa("Completed by", self.who()),
            tr_session_number=tr_qa("Session number", self.q_session),
            vas_min=self.VAS_MIN_INT,
            vas_max=self.VAS_MAX_INT,
            q_a=q_a
        )
        return h
