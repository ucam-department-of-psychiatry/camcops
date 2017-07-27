#!/usr/bin/env python
# camcops_server/tasks/fast.py

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
from ..cc_modules.cc_html import answer, get_yes_no, tr, tr_qa
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


# =============================================================================
# FAST
# =============================================================================

class Fast(Task):
    tablename = "fast"
    shortname = "FAST"
    longname = "Fast Alcohol Screening Test"

    NQUESTIONS = 4
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=4,
        comment_fmt="Q{n}. {s} (0-4, higher worse)",
        comment_strings=["M>8, F>6 drinks", "unable to remember",
                         "failed to do what was expected", "others concerned"])

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="FAST total score",
            axis_label="Total score (out of 16)",
            axis_min=-0.5,
            axis_max=16.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        classification = "positive" if self.is_positive() else "negative"
        return [CtvInfo(
            content="FAST total score {}/16 ({})".format(
                self.total_score(), classification)
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (/16)"),
            dict(name="positive", cctype="BOOL",
                 value=self.is_positive(),
                 comment="FAST positive?"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def is_positive(self) -> bool:
        if self.q1 is not None and self.q1 == 0:
            return False
        if self.q1 is not None and self.q1 >= 3:
            return True
        return self.total_score() >= 3

    def get_task_html(self) -> str:
        main_dict = {
            None: None,
            0: "0 — " + self.wxstring("q1to3_option0"),
            1: "1 — " + self.wxstring("q1to3_option1"),
            2: "2 — " + self.wxstring("q1to3_option2"),
            3: "3 — " + self.wxstring("q1to3_option3"),
            4: "4 — " + self.wxstring("q1to3_option4"),
        }
        q4_dict = {
            None: None,
            0: "0 — " + self.wxstring("q4_option0"),
            2: "2 — " + self.wxstring("q4_option2"),
            4: "4 — " + self.wxstring("q4_option4"),
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(wappstring("total_score"), answer(self.total_score()) + " / 16")
        h += tr_qa(self.wxstring("positive") + " <sup>[1]</sup>",
                   get_yes_no(self.is_positive()))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """
        h += tr_qa(self.wxstring("q1"), get_from_dict(main_dict, self.q1))
        h += tr_qa(self.wxstring("q2"), get_from_dict(main_dict, self.q2))
        h += tr_qa(self.wxstring("q3"), get_from_dict(main_dict, self.q3))
        h += tr_qa(self.wxstring("q4"), get_from_dict(q4_dict, self.q4))
        h += """
            </table>
            <div class="footnotes">
                [1] Negative if Q1 = 0. Positive if Q1 ≥ 3. Otherwise positive
                    if total score ≥ 3.
            </div>
        """
        return h
