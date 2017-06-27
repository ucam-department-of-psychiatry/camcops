#!/usr/bin/env python
# cage.py

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
from ..cc_modules.cc_html import (
    answer,
    get_yes_no,
    get_yes_no_none,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task, TrackerInfo


# =============================================================================
# CAGE
# =============================================================================

class Cage(Task):
    NQUESTIONS = 4

    tablename = "cage"
    shortname = "CAGE"
    longname = "CAGE Questionnaire"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, "CHAR", pv=['Y', 'N'],
        comment_fmt="Q{n}, {s} (Y, N)",
        comment_strings=["C", "A", "G", "E"])

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="CAGE total score",
            axis_label="Total score (out of 4)",
            axis_min=-0.5,
            axis_max=4.5,
            horizontal_lines=[1.5]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(content="CAGE score {}/4".format(self.total_score()))]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/4)"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(Cage.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def get_value(self, q: int) -> int:
        return 1 if getattr(self, "q" + str(q)) == "Y" else 0

    def total_score(self) -> int:
        total = 0
        for i in range(1, Cage.NQUESTIONS + 1):
            total += self.get_value(i)
        return total

    def get_task_html(self) -> str:
        score = self.total_score()
        exceeds_cutoff = score >= 2
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 4")
        h += tr_qa(self.WXSTRING("over_threshold"), get_yes_no(exceeds_cutoff))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """
        for q in range(1, Cage.NQUESTIONS + 1):
            h += tr_qa(str(q) + " — " + self.WXSTRING("q" + str(q)),
                       getattr(self, "q" + str(q)))  # answer is itself Y/N/NULL  # noqa
        h += """
            </table>
        """
        return h
