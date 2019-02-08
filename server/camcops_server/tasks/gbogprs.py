#!/usr/bin/env python

"""
camcops_server/tasks/gbogprs.py

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

from camcops_server.cc_modules.cc_constants import (
    CssClass,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
)
from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, Date, UnicodeText


# =============================================================================
# GBO-GReS
# =============================================================================

class Gbogprs(TaskHasPatientMixin, Task):
    """
    Server implementation of the GBO-GRS task.
    """
    __tablename__ = "gbogprs"
    shortname = "GBO-GPrS"
    longname = "Goal Based Outcomes - Goal Record Sheet"

    FN_DATE = "q_date"
    FN_SESSION = "q_session"
    FN_GOAL = "q_goal"
    FN_PROGRESS = "q_progress"
    FN_WHO = "q_who"
    FN_WHO_OTHER = "q_who_other"

    date = Column(FN_DATE, Date)
    session = Column(FN_SESSION, Integer)
    goal = Column(FN_GOAL, UnicodeText)
    progress = Column(FN_PROGRESS, UnicodeText)
    who = Column(FN_WHO, Integer)
    who_other = Column(FN_WHO_OTHER, UnicodeText)

    GOAL_CHILD = 1
    GOAL_PARENT_CARER = 2
    GOAL_OTHER = 3

    REQUIRED_FIELDS = [ FN_DATE, FN_SESSION, FN_GOAL, FN_PROGRESS, FN_WHO, FN_WHO_OTHER ]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def is_complete(self) -> bool:
        if self.are_all_fields_complete(self.REQUIRED_FIELDS):
            if self.who == self.GOAL_OTHER and len(self.who_other) <= 0:
                return False
            return True
        return False

    def get_task_html(self, req: CamcopsRequest) -> str:
        q_a = ""

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Goal number</th>
                    <th width="40%">Goal description</th>
                </tr>
                {q_a}
            </table>
        """.format(
            CssClass=CssClass,
            q_a=q_a
        )
        return h

