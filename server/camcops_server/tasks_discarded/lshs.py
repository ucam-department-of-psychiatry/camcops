#!/usr/bin/env python
# camcops_server/tasks_discarded/lshs.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

from sqlalchemy.sql.sqltypes import Integer

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import get_from_dict, Task
from ..cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# LSHS-A
# =============================================================================

class LshsA(Task):
    tablename = "lshs_a"
    shortname = "LSHS-A"
    longname = "Launay–Slade Hallucination Scale, revision A"
    provides_trackers = True

    NQUESTIONS = 12
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="LSHS-A total score",
            axis_label="Total score (out of 48)",
            axis_min=-0.5,
            axis_max=48.5
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(name="total",
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score"),
        ]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        answer_dict = {None: "?"}
        for option in range(0, 5):
            answer_dict[option] = (str(option) + " — " +
                                   self.wxstring(req, "a_option" + str(option)))
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 48</td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            req.wappstring("total_score"), score
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                self.wxstring(req, "a_q" + str(q) + "_question"),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )
        h += """
            </table>
        """
        return h


# =============================================================================
# LSHS-Laroi2005
# =============================================================================

class LshsLaroi2005(Task):
    NQUESTIONS = 16

    tablename = "lshs_laroi2005"
    shortname = "LSHS-Larøi"
    longname = (
        "Launay–Slade Hallucination Scale, revision of "
        "Larøi et al. (2005)"
    )
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        answer_dict = {None: "?"}
        for option in range(0, 5):
            answer_dict[option] = (
                str(option) + " — " +
                self.wxstring(req, "option" + str(option)))
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 64</td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            req.wappstring("total_score"), score
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                "Q" + str(q) + " – " +
                self.wxstring(req, "q" + str(q) + "_question"),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )
        h += """
            </table>
        """
        return h
