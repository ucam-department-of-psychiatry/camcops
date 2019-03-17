#!/usr/bin/env python

"""
camcops_server/tasks/gbo.py

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

Goal-Based Outcomes tasks.

- By Joe Kearney, Rudolf Cardinal.

"""

from typing import List

from cardinal_pythonlib.datetimefunc import format_datetime
from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Boolean, Integer, Date, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass, DateFormat
from camcops_server.cc_modules.cc_html import tr_qa, answer
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
)


# =============================================================================
# Common GBO constants
# =============================================================================

AGENT_PATIENT = 1
AGENT_PARENT_CARER = 2
AGENT_CLINICIAN = 3
AGENT_OTHER = 4

AGENT_STRING_MAP = {
    AGENT_PATIENT: "Patient/service user",  # in original: "Child/young person"
    AGENT_PARENT_CARER: "Parent/carer",
    AGENT_CLINICIAN: "Practitioner/clinician",
    AGENT_OTHER: "Other: "
}
UNKNOWN_AGENT = "Unknown"

PROGRESS_COMMENT_SUFFIX = " (0 no progress - 10 reached fully)"


def agent_description(agent: int, other_detail: str) -> str:
    who = AGENT_STRING_MAP.get(agent, UNKNOWN_AGENT)
    if agent == AGENT_OTHER:
        who += other_detail or "?"
    return who


# =============================================================================
# GBO-GReS
# =============================================================================

class Gbogres(TaskHasPatientMixin, Task):
    """
    Server implementation of the GBO - Goal Record Sheet task.
    """
    __tablename__ = "gbogres"
    shortname = "GBO-GReS"
    longname = "Goal-Based Outcomes – 1 – Goal Record Sheet"
    extrastring_taskname = "gbo"

    FN_DATE = "date"  # NB SQL keyword too; doesn't matter
    FN_GOAL_1_DESC = "goal_1_description"
    FN_GOAL_2_DESC = "goal_2_description"
    FN_GOAL_3_DESC = "goal_3_description"
    FN_GOAL_OTHER = "other_goals"
    FN_COMPLETED_BY = "completed_by"
    FN_COMPLETED_BY_OTHER = "completed_by_other"

    REQUIRED_FIELDS = [FN_DATE, FN_GOAL_1_DESC, FN_COMPLETED_BY]

    date = Column(FN_DATE, Date, comment="Date of goal-setting")
    goal_1_description = Column(
        FN_GOAL_1_DESC, UnicodeText,
        comment="Goal 1 description")
    goal_2_description = Column(
        FN_GOAL_2_DESC, UnicodeText,
        comment="Goal 2 description")
    goal_3_description = Column(
        FN_GOAL_3_DESC, UnicodeText,
        comment="Goal 3 description")
    other_goals = Column(
        FN_GOAL_OTHER, UnicodeText,
        comment="Other/additional goal description(s)")
    completed_by = Column(
        FN_COMPLETED_BY, Integer,
        comment="Who completed the form ({})".format(
            "; ".join("{} = {}".format(k, v)
                      for k, v in AGENT_STRING_MAP.items())
        )
    )
    completed_by_other = Column(
        FN_COMPLETED_BY_OTHER, UnicodeText,
        comment="If completed by 'other', who?")

    def get_n_core_goals(self) -> int:
        """
        Returns the number of non-blank core (1-3) goals.
        """
        return len(list(filter(
            None,
            [self.goal_1_description, self.goal_2_description,
             self.goal_3_description])))

    def goals_set_tr(self) -> str:
        extra = " (additional goals specified)" if self.other_goals else ""
        return tr_qa("Number of goals set",
                     "{}{}".format(self.get_n_core_goals(), extra))

    def completed_by_tr(self) -> str:
        who = agent_description(self.completed_by, self.completed_by_other)
        return tr_qa("Completed by", who)

    def get_date_tr(self) -> str:
        return tr_qa("Date", format_datetime(self.date,
                                             DateFormat.SHORT_DATE,
                                             default=None))

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def is_complete(self) -> bool:
        if not self.are_all_fields_complete(self.REQUIRED_FIELDS):
            return False
        if self.completed_by == AGENT_OTHER and not self.completed_by_other:
            return False
        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        return """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {complete_tr}
                    {date_tr}
                    {completed_by_tr}
                    {goals_set_count_tr}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="15%">Goal number</th>
                    <th width="85%">Goal description</th>
                </tr>
                <tr><td>1</td><td>{g1}</td></tr>
                <tr><td>2</td><td>{g2}</td></tr>
                <tr><td>3</td><td>{g3}</td></tr>
                <tr><td>Other</td><td>{go}</td></tr>
            </table>
        """.format(
            CssClass=CssClass,
            date_tr=self.get_date_tr(),
            complete_tr=self.get_is_complete_tr(req),
            completed_by_tr=self.completed_by_tr(),
            goals_set_count_tr=self.goals_set_tr(),
            g1=answer(self.goal_1_description, default=""),
            g2=answer(self.goal_2_description, default=""),
            g3=answer(self.goal_3_description, default=""),
            go=answer(self.other_goals, default=""),
        )


# =============================================================================
# GBO-GPC
# =============================================================================

class Gbogpc(TaskHasPatientMixin, Task):
    """
    Server implementation of the GBO-GPC task.
    """
    __tablename__ = "gbogpc"
    shortname = "GBO-GPC"
    longname = "Goal-Based Outcomes – 2 – Goal Progress Chart"
    extrastring_taskname = "gbo"

    FN_DATE = "date"  # NB SQL keyword too; doesn't matter
    FN_SESSION = "session"
    FN_GOAL_NUMBER = "goal_number"
    FN_GOAL_DESCRIPTION = "goal_description"
    FN_PROGRESS = "progress"
    FN_WHOSE_GOAL = "whose_goal"
    FN_WHOSE_GOAL_OTHER = "whose_goal_other"

    date = Column(FN_DATE, Date, comment="Session date")
    session = Column(FN_SESSION, Integer, comment="Session number")
    goal_number = Column(FN_GOAL_NUMBER, Integer, comment="Goal number (1-3)")
    goal_text = Column(
        FN_GOAL_DESCRIPTION, UnicodeText,
        comment="Brief description of the goal")
    progress = Column(
        FN_PROGRESS, Integer,
        comment="Progress towards goal" + PROGRESS_COMMENT_SUFFIX
    )
    whose_goal = Column(
        FN_WHOSE_GOAL, Integer,
        comment="Whose goal is this ({})".format(
            "; ".join("{} = {}".format(k, v)
                      for k, v in AGENT_STRING_MAP.items())
        )
    )
    whose_goal_other = Column(
        FN_WHOSE_GOAL_OTHER, UnicodeText,
        comment="If 'whose goal' is 'other', who?")

    REQUIRED_FIELDS = [
        FN_DATE, FN_SESSION, FN_GOAL_NUMBER, FN_PROGRESS, FN_WHOSE_GOAL
    ]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def is_complete(self) -> bool:
        if not self.are_all_fields_complete(self.REQUIRED_FIELDS):
            return False
        if self.whose_goal == AGENT_OTHER and not self.whose_goal_other:
            return False
        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        return """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="30%">Date</th>
                    <td width="70%">{date}</td>
                </tr>
                <tr>
                    <th>Session number</th>
                    <td>{session}</td>
                </tr>
                <tr>
                    <th>Goal number</th>
                    <td>{goal_num}</td>
                </tr>
                <tr>
                    <th>Goal description</th>
                    <td>{goal_desc}</td>
                </tr>
                <tr>
                    <th>Progress <sup>[1]</sup></th>
                    <td>{progress}</td>
                </tr>
                <tr>
                    <th>Whose goal is this?</th>
                    <td>{who}</td>
                </tr>
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] {progress_explanation}
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            date=answer(format_datetime(self.date, DateFormat.SHORT_DATE,
                                        default=None)),
            session=answer(self.session),
            goal_num=answer(self.goal_number),
            goal_desc=answer(self.goal_text),
            progress=answer(self.progress),
            who=answer(
                agent_description(self.whose_goal, self.whose_goal_other)
            ),
            progress_explanation=self.wxstring(req, "progress_explanation")
        )


# =============================================================================
# GBO-GRaS
# =============================================================================

class Gbogras(TaskHasPatientMixin, Task):
    """
    Server implementation of the GBO-GRaS task.
    """
    __tablename__ = "gbogras"
    shortname = "GBO-GRaS"
    longname = "Goal-Based Outcomes – 3 – Goal Rating Sheet"
    extrastring_taskname = "gbo"

    FN_DATE = "date"  # NB SQL keyword too; doesn't matter
    FN_RATE_GOAL_1 = "rate_goal_1"
    FN_RATE_GOAL_2 = "rate_goal_2"
    FN_RATE_GOAL_3 = "rate_goal_3"
    FN_GOAL_1_DESC = "goal_1_description"
    FN_GOAL_2_DESC = "goal_2_description"
    FN_GOAL_3_DESC = "goal_3_description"
    FN_GOAL_1_PROGRESS = "goal_1_progress"
    FN_GOAL_2_PROGRESS = "goal_2_progress"
    FN_GOAL_3_PROGRESS = "goal_3_progress"
    FN_COMPLETED_BY = "completed_by"
    FN_COMPLETED_BY_OTHER = "completed_by_other"

    date = Column(FN_DATE, Date, comment="Date of ratings")
    # ... NB SQL keyword too; doesn't matter
    rate_goal_1 = Column(FN_RATE_GOAL_1, Boolean, comment="Rate goal 1?")
    rate_goal_2 = Column(FN_RATE_GOAL_2, Boolean, comment="Rate goal 2?")
    rate_goal_3 = Column(FN_RATE_GOAL_3, Boolean, comment="Rate goal 3?")
    goal_1_description = Column(
        FN_GOAL_1_DESC, UnicodeText,
        comment="Goal 1 description")
    goal_2_description = Column(
        FN_GOAL_2_DESC, UnicodeText,
        comment="Goal 2 description")
    goal_3_description = Column(
        FN_GOAL_3_DESC, UnicodeText,
        comment="Goal 3 description")
    goal_1_progress = Column(
        FN_GOAL_1_PROGRESS, Integer,
        comment="Goal 1 progress" + PROGRESS_COMMENT_SUFFIX)
    goal_2_progress = Column(
        FN_GOAL_2_PROGRESS, Integer,
        comment="Goal 2 progress" + PROGRESS_COMMENT_SUFFIX)
    goal_3_progress = Column(
        FN_GOAL_3_PROGRESS, Integer,
        comment="Goal 3 progress" + PROGRESS_COMMENT_SUFFIX)
    completed_by = Column(
        FN_COMPLETED_BY, Integer,
        comment="Who completed the form ({})".format(
            "; ".join("{} = {}".format(k, v)
                      for k, v in AGENT_STRING_MAP.items()
                      if k != AGENT_CLINICIAN)
        )
    )
    completed_by_other = Column(
        FN_COMPLETED_BY_OTHER, UnicodeText,
        comment="If completed by 'other', who?")

    REQUIRED_FIELDS = [FN_DATE, FN_COMPLETED_BY]
    GOAL_TUPLES = (
        # goalnum, rate it?, goal description, progress
        (1, FN_RATE_GOAL_1, FN_GOAL_1_DESC, FN_GOAL_1_PROGRESS),
        (2, FN_RATE_GOAL_2, FN_GOAL_2_DESC, FN_GOAL_2_PROGRESS),
        (3, FN_RATE_GOAL_3, FN_GOAL_3_DESC, FN_GOAL_3_PROGRESS),
    )

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def is_complete(self) -> bool:
        if not self.are_all_fields_complete(self.REQUIRED_FIELDS):
            return False
        if self.completed_by == AGENT_OTHER and not self.completed_by_other:
            return False
        n_goals_completed = 0
        for _, rate_attr, desc_attr, prog_attr in self.GOAL_TUPLES:
            if getattr(self, rate_attr):
                n_goals_completed += 1
                if not getattr(self, desc_attr) or not getattr(self, prog_attr):  # noqa
                    return False
        return n_goals_completed > 0

    def completed_by_tr(self) -> str:
        who = agent_description(self.completed_by, self.completed_by_other)
        return tr_qa("Completed by", who)

    def get_date_tr(self) -> str:
        return tr_qa("Date", format_datetime(self.date,
                                             DateFormat.SHORT_DATE,
                                             default=None))

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = []  # type: List[str]
        for goalnum, rate_attr, desc_attr, prog_attr in self.GOAL_TUPLES:
            if getattr(self, rate_attr):
                rows.append("""
                    <tr><td>{gn}</td><td>{gd}</td><td>{p}</td></tr>
                """.format(
                    gn=answer(goalnum),
                    gd=answer(getattr(self, desc_attr)),
                    p=answer(getattr(self, prog_attr))
                ))
        return """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {complete_tr}
                    {date_tr}
                    {completed_by_tr}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="15%">Goal number</th>
                    <th width="70%">Description</th>
                    <th width="15%">Progress <sup>[1]</sup></th>
                </tr>
                {rows}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] {progress_explanation}
            </div>
        """.format(
            CssClass=CssClass,
            complete_tr=self.get_is_complete_tr(req),
            date_tr=self.get_date_tr(),
            completed_by_tr=self.completed_by_tr(),
            rows="\n".join(rows),
            progress_explanation=self.wxstring(req, "progress_explanation")
        )
