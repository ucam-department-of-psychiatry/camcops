#!/usr/bin/env python

"""
camcops_server/tasks/bmi.py

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
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    PermittedValueChecker,
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from sqlalchemy.sql.sqltypes import Integer, UnicodeText, Date


# =============================================================================
# GBO
# =============================================================================

class Gbo(TaskHasPatientMixin, Task):
    """
    Server implementation of the GBO task.
    """
    __tablename__ = "gbo"
    shortname = "GBO"
    longname = "Goal-based Outcomes"
    provides_trackers = True

    MIN_SESSIONS = 1
    MAX_SESSIONS = 1000

    MIN_GOALS = 1
    MAX_GOALS = 1000

    MIN_PROGRESS = 1
    MAX_PROGRESS = 10

    CHOSEN_BY_CHILD = 0
    CHOSEN_BY_PARENT = 1
    CHOSEN_BY_OTHER = 2

    session_n = CamcopsColumn(
        "session_n", Integer,
        permitted_value_checker=PermittedValueChecker(minimum=MIN_SESSIONS, maximum=MAX_SESSIONS),
        comment="Session number"
    )
    session_d = CamcopsColumn(
        "session_d", Date,
        comment="Session date"
    )
    goal_n = CamcopsColumn(
        "goal_n", Integer,
        permitted_value_checker=PermittedValueChecker(minimum=MIN_GOALS, maximum=MAX_GOALS),
        comment="Goal number"
    )
    goal_desc = CamcopsColumn(
        "goal_desc", UnicodeText,
        comment="Goal description"
    )
    goal_p = CamcopsColumn(
        "goal_p", Integer,
        permitted_value_checker=PermittedValueChecker(minimum=MIN_PROGRESS, maximum=MAX_PROGRESS),
        comment="Goal progress"
    )
    chosen_by = CamcopsColumn(
        "chosen_by", Integer,
        permitted_value_checker=PermittedValueChecker(minimum=CHOSEN_BY_CHILD, maximum=CHOSEN_BY_OTHER),
        comment="Goal chosen by"
    )
    chosen_by_other = CamcopsColumn(
        "chosen_by_other", UnicodeText,
        comment="Chosen by Other (more details)"
    )

    REQUIRED = [
        "session_n",
        "session_d",
        "goal_n",
        "goal_desc",
        "goal_p",
        "chosen_by",
    ]

    def is_complete(self) -> bool:
        if not self.are_all_fields_complete(self.REQUIRED):
            return False
        if self.chosen_by == self.CHOSEN_BY_OTHER:
            return len(self.chosen_by_other) > 0

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def get_task_html(self, req: CamcopsRequest) -> str:
        q_a = ""

        q_a += tr_qa(self.wxstring(req, "session_n"), self.session_n)
        q_a += tr_qa(self.wxstring(req, "session_d"), self.session_d)
        q_a += tr_qa(self.wxstring(req, "goal_n"), self.goal_n)
        q_a += tr_qa(self.wxstring(req, "goal_desc"), self.goal_desc)
        q_a += tr_qa(self.wxstring(req, "goal_p"),
                     "{}/{}".format(self.goal_p, self.MAX_PROGRESS))

        chosen_by_dict = {
            self.CHOSEN_BY_CHILD: self.wxstring(req, "choice_o1"),
            self.CHOSEN_BY_PARENT: self.wxstring(req, "choice_o2"),
            self.CHOSEN_BY_OTHER: self.wxstring(req, "choice_o3"),
        }

        chosen_by = chosen_by_dict[self.chosen_by]
        if self.chosen_by == self.CHOSEN_BY_OTHER:
            chosen_by += " (" + self.chosen_by_other + ")"

        q_a += tr_qa(self.wxstring(req, "chosen_by"), chosen_by)

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            q_a=q_a,
        )
        return h
