#!/usr/bin/env python

"""
camcops_server/tasks/srs.py

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
    PendulumDateTimeAsIsoTextColType,
    ZERO_TO_ONE_CHECKER,
    ZERO_TO_TWO_CHECKER,
    ZERO_TO_FOUR_CHECKER
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import (
    TrackerInfo,
)
from sqlalchemy.sql.sqltypes import Integer, DateTime, UnicodeText


# =============================================================================
# APEQPT
# =============================================================================

class Apeqpt(TaskHasPatientMixin, Task):
    """
    Server implementation of the SRS task.
    """
    __tablename__ = "apeqpt"
    shortname = "APEQPT"
    longname = "Assessment Patient Experience Questionnaire: For Psychological Therapies"
    provides_trackers = True

    q_datetime = CamcopsColumn("q_datetime", PendulumDateTimeAsIsoTextColType, comment="Session number")

    N_CHOICE_QUESTIONS = 3
    q1_choice = CamcopsColumn("q1_choice", Integer, comment="Enough information was provided", permitted_value_checker=ZERO_TO_ONE_CHECKER)
    q2_choice = CamcopsColumn("q2_choice", Integer, comment="Treatment preference", permitted_value_checker=ZERO_TO_ONE_CHECKER)
    q3_choice = CamcopsColumn("q3_choice", Integer, comment="Preference offered", permitted_value_checker=ZERO_TO_TWO_CHECKER)

    q1_satisfaction = CamcopsColumn("q1_satisfaction", Integer, comment="Patient satisfaction", permitted_value_checker=ZERO_TO_FOUR_CHECKER)
    q2_satisfaction = CamcopsColumn("q2_satisfaction", UnicodeText, comment="Service expererience")

    MAIN_QUESTIONS = [
        "q_datetime",
        "q1_choice",
 
    ]

    def is_complete(self) -> bool:
        if not self.are_all_fields_complete(self.MAIN_QUESTIONS):
            return False
        if not self.field_contents_valid():
            return False
        return True

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        pass

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        pass

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def get_task_html(self, req: CamcopsRequest) -> str:
        c_dict= {
            0: "0 — " + self.wxstring(req, "a0_choice"),
            1: "1 — " + self.wxstring(req, "a1_choice"),
            2: "2 — " + self.wxstring(req, "a2_choice"),
        }
        s_dict = {
            0: "0 — " + self.wxstring(req, "a0_satisfaction"),
            1: "1 — " + self.wxstring(req, "a1_satisfaction"),
            2: "2 — " + self.wxstring(req, "a2_satisfaction"),
            3: "3 — " + self.wxstring(req, "a3_satisfaction"),
            4: "4 — " + self.wxstring(req, "a4_satisfaction"),
        }
        q_a = ""
        for i in range(1, self.N_CHOICE_QUESTIONS + 1):
            nstr = str(i)
            q_a += tr_qa(self.wxstring(req, "q" + nstr + "_choice"),
                         get_from_dict(c_dict, getattr(self, "q" + nstr + "_choice")))

        q_a += tr_qa(self.wxstring(req, "q1_satisfaction"), get_from_dict(s_dict, self.q1_satisfaction))
        q_a += tr_qa(self.wxstring(req, "q2_satisfaction"), self.q2_satisfaction)

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                Patient satisfaction rating rating for service provided. The service is rated on
                choice offered and general satisfaction.
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
            q_a=q_a
        )
        return h
