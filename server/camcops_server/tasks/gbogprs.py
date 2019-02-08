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

    date = Column("q_date", Date)
    session = Column("q_session", Integer)
    goal = Column("q_goal", UnicodeText)
    progress = Column("q_progress", UnicodeText)
    who = Column("q_who", Integer)
    who_other = Column("q_who_other", UnicodeText)

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def is_complete(self) -> bool:
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

