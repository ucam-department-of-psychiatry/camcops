#!/usr/bin/env python
# bars.py

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

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task, TrackerInfo


# =============================================================================
# BARS
# =============================================================================

class Bars(Task):
    NQUESTIONS = 4

    tablename = "bars"
    shortname = "BARS"
    longname = "Barnes Akathisia Rating Scale"
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="BARS total score",
            axis_label="Total score (out of 14)",
            axis_min=-0.5,
            axis_max=14.5
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score"),
        ]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self) -> str:
        score = self.total_score()
        answer_dicts_dict = {}
        for q in self.TASK_FIELDS:
            d = {None: "?"}
            for option in range(0, 6):
                if option > 3 and q == "q4":
                    continue
                d[option] = WSTRING("bars_" + q + "_option" + str(option))
            answer_dicts_dict[q] = d
        h = self.get_standard_clinician_block() + """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 14</td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="35%">Question</th>
                    <th width="65%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score
        )
        for q in self.TASK_FIELDS:
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("bars_" + q + "_s"),
                get_from_dict(answer_dicts_dict[q], getattr(self, q))
            )
        h += """
            </table>
        """
        return h
