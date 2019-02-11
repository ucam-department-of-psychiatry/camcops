#!/usr/bin/env python

"""
camcops_server/tasks/gbogres.py

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

from typing import List, Optional

from camcops_server.cc_modules.cc_constants import CssClass

from sqlalchemy import Column

from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
)
from sqlalchemy.sql.sqltypes import Integer, Date, UnicodeText


# =============================================================================
# GBO-GReS
# =============================================================================

class Gbogres(TaskHasPatientMixin, Task):
    """
    Server implementation of the GBO - Goal Record Sheet task.
    """
    __tablename__ = "gbogres"
    shortname = "GBO-GReS"
    longname = "Goal Based Outcomes – Goal Record Sheet"

    FN_DATE = "date"  # NB SQL keyword too; doesn't matter
    FN_GOAL_1_DESC = "goal_1_desc"
    FN_GOAL_2_DESC = "goal_2_desc"
    FN_GOAL_3_DESC = "goal_3_desc"
    FN_GOAL_OTHER = "goal_other"
    FN_COMPLETED_BY = "completed_by"
    FN_COMPLETED_BY_OTHER = "completed_by_other"

    REQUIRED_FIELDS = [FN_DATE, FN_GOAL_1_DESC, FN_COMPLETED_BY]

    GOAL_CHILD = 1
    GOAL_PARENT_CARER = 2
    GOAL_OTHER = 3

    COMPLETED_BY_STRINGS = {
        GOAL_CHILD: "Child/young person",
        GOAL_PARENT_CARER: "Parent/carer",
        GOAL_OTHER: "Other"
    }

    date = Column(FN_DATE, Date, comment="Session date")
    goal_1_desc = Column(FN_GOAL_1_DESC, UnicodeText,
                         comment="Goal 1 description")
    goal_2_desc = Column(FN_GOAL_2_DESC, UnicodeText,
                         comment="Goal 2 description")
    goal_3_desc = Column(FN_GOAL_3_DESC, UnicodeText,
                         comment="Goal 3 description")
    goal_other = Column(FN_GOAL_OTHER, UnicodeText,
                        comment="Other/additional goal description(s)")
    completed_by = Column(
        FN_COMPLETED_BY, Integer,
        comment="Who completed the form ({})".format(
            "; ".join("{} = {}".format(k, v)
                      for k, v in COMPLETED_BY_STRINGS.items())
        )
    )
    completed_by_other = Column(FN_COMPLETED_BY_OTHER, UnicodeText,
                                comment="If completed by 'other', who?")

    def get_goals(self) -> List[str]:
        goals = []  # type: List[str]
        for x in [self.goal_1_desc, self.goal_2_desc,
                  self.goal_3_desc, self.goal_other]:
            if x:
                goals.append(x)
        return goals

    def goals_set_tr(self) -> str:
        extra = " (additional goals specified)" if self.goal_other else ""
        return tr_qa("Goals", "{}{}".format(len(self.get_goals()), extra))

    def completed_by_tr(self) -> str:
        who = self.COMPLETED_BY_STRINGS.get(self.completed_by, "Unknown")
        if self.completed_by == self.GOAL_OTHER:
            who += ": " + self.completed_by_other
        return tr_qa("Completed by", who)

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def is_complete(self) -> bool:
        if self.are_all_fields_complete(self.REQUIRED_FIELDS):
            if self.completed_by == self.GOAL_OTHER:
                return bool(self.completed_by_other)
            return True
        return False

    def get_task_html(self, req: CamcopsRequest) -> str:
        q_a = ""
        for i, goaltext in enumerate(self.get_goals(), start=1):
            q_a += tr_qa("{}".format(i), goaltext)

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

