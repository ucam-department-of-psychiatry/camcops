#!/usr/bin/env python
# madrs.py

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

from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task, TrackerInfo, TrackerLabel


# =============================================================================
# MADRS
# =============================================================================

class Madrs(Task):
    NQUESTIONS = 10

    tablename = "madrs"
    shortname = "MADRS"
    longname = "Montgomery–Åsberg Depression Rating Scale"
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS) + [
        dict(name="period_rated", cctype="TEXT"),
    ]
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="MADRS total score",
            axis_label="Total score (out of 60)",
            axis_min=-0.5,
            axis_max=60.5,
            horizontal_lines=[
                33.5,
                19.5,
                6.5,
            ],
            horizontal_labels=[
                TrackerLabel(35, WSTRING("severe")),
                TrackerLabel(25, WSTRING("moderate")),
                TrackerLabel(14, WSTRING("mild")),
                TrackerLabel(3, WSTRING("normal"))
            ]
        )]

    def get_summaries(self):
        return [
            dict(name="is_complete", cctype="BOOL", value=self.is_complete()),
            dict(name="total", cctype="INT", value=self.total_score()),
        ]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 1, self.NQUESTIONS))

    def get_task_html(self) -> str:
        score = self.total_score()
        if score > 34:
            category = WSTRING("severe")
        elif score >= 20:
            category = WSTRING("moderate")
        elif score >= 7:
            category = WSTRING("mild")
        else:
            category = WSTRING("normal")
        answer_dicts = []
        for q in range(1, self.NQUESTIONS + 1):
            d = {None: "?"}
            for option in range(0, 7):
                if option == 1 or option == 3 or option == 5:
                    d[option] = option
                else:
                    d[option] = WSTRING("madrs_q" + str(q) + "_option" +
                                        str(option))
            answer_dicts.append(d)
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 60</td></tr>
                    <tr><td>{} <sup>[1]</sup></td><td><b>{}</b></tr>
                </table>
            </div>
            <div class="explanation">
                Ratings are from 0–6 (0 none, 6 extreme problem).
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="30%">Question</th>
                    <th width="70%">Answer</th>
                </tr>
                <tr><td>{}</td><td><b>{}</b></td></tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score,
            WSTRING("category"), category,
            WSTRING("madrs_q_period_rated"), self.period_rated
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("madrs_q" + str(q) + "_s"),
                get_from_dict(answer_dicts[q - 1], getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Total score &gt;34 severe, &ge;20 moderate, &ge;7 mild,
                &lt;7 normal. (Hermann et al. 1998, PubMed ID 9506602.)
            </div>
        """
        return h
