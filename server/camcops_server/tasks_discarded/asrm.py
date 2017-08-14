#!/usr/bin/env python
# camcops_server/tasks_discarded/asrm.py

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
from ..cc_modules.cc_html import get_yes_no
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import get_from_dict, Task
from ..cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# ASRM
# =============================================================================

class Asrm(Task):
    tablename = "asrm"
    shortname = "ASRM"
    longname = "Altman Self-Rating Mania Scale"
    provides_trackers = True

    NQUESTIONS = 5
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)
    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="ASRM total score",
            axis_label="Total score (out of 20)",
            axis_min=-0.5,
            axis_max=20.5,
            horizontal_lines=[5.5]
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
        above_cutoff = score >= 6
        answer_dicts = []
        for q in range(1, self.NQUESTIONS + 1):
            d = {None: "?"}
            for option in range(0, 5):
                d[option] = (
                    str(option) + " — " +
                    self.wxstring(req, "q" + str(q) + "_option" + str(option)))
            answer_dicts.append(d)
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 20</td></tr>
                    <tr><td>{} <sup>[1]</sup></td><td><b>{}</b></td></tr>
                </table>
            </div>
            <div class="explanation">
                Ratings are over the last week.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="30%">Question</th>
                    <th width="70%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            req.wappstring("total_score"), score,
            self.wxstring(req, "above_cutoff"), get_yes_no(above_cutoff),
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                self.wxstring(req, "q" + str(q) + "_s"),
                get_from_dict(answer_dicts[q - 1], getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Cutoff is &ge;6. Scores of &ge;6 identify mania/hypomania
                with sensitivity 85.5%, specificity 87.3% (Altman et al. 1997,
                PubMed ID 9359982).
            </div>
        """
        return h
