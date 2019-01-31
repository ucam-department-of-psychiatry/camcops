#!/usr/bin/env python

"""
camcops_server/tasks/gbogrs.py

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
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
)

from sqlalchemy import Column

from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_html import (
    tr,
    tr_qa,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
    TaskHasRespondentMixin,
)
from sqlalchemy.sql.sqltypes import Integer, Date, UnicodeText


# =============================================================================
# GBO-GRS
# =============================================================================

class Gbogrs(TaskHasPatientMixin, Task):
    """
    Server implementation of the GBO-GRS task.
    """
    __tablename__ = "gbogrs"
    shortname = "GBO-GRS"
    longname = "Goal Based Outcomes - Goal Record Sheet"

    REQUIRED_FIELDS = [
        "date", "goal_1_desc", "completed_by"
    ]

    GOAL_CHILD = 1
    GOAL_PARENT_CARER = 2
    GOAL_OTHER = 3

    completed_by_strings = {
        GOAL_CHILD: "Child/young person",
        GOAL_PARENT_CARER: "Parent/carer",
        GOAL_OTHER: "Other"
    }

    date = Column("date", Date)
    goal_1_desc = Column("goal_1_desc", UnicodeText)
    goal_2_desc = Column("goal_2_desc", UnicodeText)
    goal_3_desc = Column("goal_3_desc", UnicodeText)
    goal_other = Column("goal_other", UnicodeText)
    completed_by = Column("completed_by", Integer)
    completed_by_other = Column("completed_by_other", UnicodeText)

    goals = []

    def goal_set(self, goal_prop):
        return goal_prop is not None and len(goal_prop) > 0

    def get_goals(self) -> str:
        if len(self.goals) > 0:
            return self.goals

        if self.goal_set(self.goal_1_desc):
            self.goals.append(self.goal_1_desc)
        if self.goal_set(self.goal_2_desc):
            self.goals.append(self.goal_2_desc)
        if self.goal_set(self.goal_3_desc):
            self.goals.append(self.goal_2_desc)
        if self.goal_set(self.goal_other):
            self.goals.append(self.goal_other)
        return self.goals

    def goals_set_tr(self) -> str:
        extra = ""
        if self.goal_set(self.goal_other):
            extra = ' (additional goals specified)'
        return tr_qa("Goals", "{}{}".format(len(self.get_goals()), extra))

    def completed_by_tr(self) -> str:
        who = self.completed_by_strings[self.completed_by]
        if self.completed_by == self.GOAL_OTHER:
            who = self.completed_by_other
        if len(who) <= 0:
            who = "Unknown"

        return tr_qa("Completed by", who)

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def is_complete(self) -> bool:
        if self.are_all_fields_complete(self.REQUIRED_FIELDS):
            if self.completed_by == self.GOAL_OTHER:
                return len(self.completed_by_other) > 0
            return True
        return False

    def get_task_html(self, req: CamcopsRequest) -> str:
        q_a = ""
        for i, goaltext in enumerate(self.get_goals()):
            q_a += tr_qa("{}".format(i+1), goaltext)

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {complete_tr}
                    {completed_by_tr}
                    {goals_set_count_tr}
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
            complete_tr=self.get_is_complete_tr(req),
            completed_by_tr=self.completed_by_tr(),
            goals_set_count_tr=self.goals_set_tr(),
            q_a=q_a
        )
        return h

