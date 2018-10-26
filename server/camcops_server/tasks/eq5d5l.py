#!/usr/bin/env python
# camcops_server/tasks/eq5d5l.py

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
from typing import List

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import answer, get_yes_no, tr, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    PermittedValueChecker,
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


# =============================================================================
# EQ-5D-5L
# =============================================================================

class Eq5d5l(TaskHasPatientMixin, Task):
    """
    Server implementation of the EQ-5D-5L task.
    """
    __tablename__ = "eq5d5l"
    shortname = "EQ-5D-5L"
    longname = "EQ 5-Dimension, 5-Level Health Scale"
    provides_trackers = True

    q1 = CamcopsColumn(
        "q1", Integer,
        comment="Q1 (Mobility)",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=4),
    )

    q2 = CamcopsColumn(
        "q2", Integer,
        comment="Q2 (Self-Care)",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=4),
    )

    q3 = CamcopsColumn(
        "q3", Integer,
        comment="Q3 (Usual Activities)",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=4),
    )

    q4 = CamcopsColumn(
        "q4", Integer,
        comment="Q4 (Pain/Discomfort)",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=4),
    )

    q5 = CamcopsColumn(
        "q5", Integer,
        comment="Q5 (Anxiety/Depression)",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=4),
    )

    thermometer = CamcopsColumn(
        "thermometer", Integer,
        comment="Q5 (Anxiety/Depression)",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=100),
    )

    N_QUESTIONS = 5
    MISSING_ANSWER_VALUE = 9
    QUESTIONS = strseq("q", 1, N_QUESTIONS)
    QUESTIONS += ["thermometer"]

    def is_complete(self) -> bool:
        if not self.are_all_fields_complete(self.QUESTIONS):
            return False
        return True

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        pass

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="descriptive task score", coltype=Integer(),
                value=self.get_mcq_score(),
                comment="Descriptive Task Score"),
            SummaryElement(
                name="visual task score", coltype=Integer(),
                value=self.get_vis_score(),
                comment="Visual Task Score")
        ]

    def get_mcq_score(self) -> str:
        mcq = ""
        for i in range(1, self.N_QUESTIONS + 1):
            ans = getattr(self, "q" + str(i))
            if ans is None:
                mcq += str(self.MISSING_ANSWER_VALUE)
            else:
                mcq += str(ans + 1)
        return mcq

    def get_vis_score(self) -> str:
        vis_score = getattr(self, "thermometer")
        if vis_score is None:
            return "999"
        return str(vis_score)

    def get_task_html(self, req: CamcopsRequest) -> str:

        q_a = ""
        mcq_score = ""

        for i in range(1, self.N_QUESTIONS + 1):
            nstr = str(i)
            answers = {
                None: None,
                0: "0 — " + self.wxstring(req, "q" + nstr + "_o1"),
                1: "1 — " + self.wxstring(req, "q" + nstr + "_o2"),
                2: "2 — " + self.wxstring(req, "q" + nstr + "_o3"),
                3: "3 — " + self.wxstring(req, "q" + nstr + "_o4"),
                4: "4 — " + self.wxstring(req, "q" + nstr + "_o5"),
            }

            q_a += tr_qa(self.wxstring(req, "q" + nstr + "_h"),
                         get_from_dict(answers, getattr(self, "q" + str(i))))

        q_a += tr_qa("Self-rated health (/100) <sup>[2]</sup>",
                     getattr(self, "thermometer"))

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {mcq_score}
                    {vis_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Each value corresponds to a questions.
                    A score of 1 indicates no problems in any given dimension.
                    5 indicates extreme problems. Missing values are
                    coded as 9.
                [2] The "Visual Analogue" score is the value entered on the
                    thermometer task. A missing value is coded as 999.
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            mcq_score=tr_qa("Descriptive System Score" + " <sup>[1]</sup>", self.get_mcq_score()),
            vis_score=tr_qa("Visual System Score" + " <sup>[2]</sup>", self.get_vis_score()),
            q_a=q_a
        )
        return h
