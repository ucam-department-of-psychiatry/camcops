#!/usr/bin/env python
# epds.py

"""
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
"""

from typing import List

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import get_yes_no
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task, TrackerInfo, TrackerLabel


# =============================================================================
# EPDS
# =============================================================================

class Epds(Task):
    NQUESTIONS = 10

    tablename = "epds"
    shortname = "EPDS"
    longname = "Edinburgh Postnatal Depression Scale"
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="EPDS total score (rating depressive symptoms)",
            axis_label="Total score (out of 30)",
            axis_min=-0.5,
            axis_max=30.5,
            horizontal_lines=[
                12.5,
                9.5,
            ],
            horizontal_labels=[
                TrackerLabel(13, "likely depression"),
                TrackerLabel(10, "possible depression"),
            ]
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
        above_cutoff_1 = score >= 10
        above_cutoff_2 = score >= 13
        answer_dicts = []
        for q in range(1, self.NQUESTIONS + 1):
            d = {None: "?"}
            for option in range(0, 4):
                d[option] = (
                    str(option) + " — " +
                    WSTRING("epds_q" + str(q) + "_option" + str(option)))
            answer_dicts.append(d)
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 30</td></tr>
                    <tr><td>{} <sup>[1]</sup></td><td><b>{}</b></td></tr>
                    <tr><td>{} <sup>[2]</sup></td><td><b>{}</b></td></tr>
                </table>
            </div>
            <div class="explanation">
                Ratings are over the last week.
                <b>{}</b>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score,
            WSTRING("epds_above_cutoff_1"), get_yes_no(above_cutoff_1),
            WSTRING("epds_above_cutoff_2"), get_yes_no(above_cutoff_2),
            WSTRING("epds_always_look_at_suicide")
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("epds_q" + str(q) + "_question"),
                get_from_dict(answer_dicts[q - 1], getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] &ge;10.
                [2] &ge;13.
                (Cox et al. 1987, PubMed ID 3651732.)
            </div>
        """
        return h
