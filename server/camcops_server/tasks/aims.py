#!/usr/bin/env python
# aims.py

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

from ..cc_modules.cc_constants import (
    PV,
)
from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


# =============================================================================
# AIMS
# =============================================================================

class Aims(Task):
    tablename = "aims"
    shortname = "AIMS"
    longname = "Abnormal Involuntary Movement Scale"
    provides_trackers = True
    has_clinician = True

    NQUESTIONS = 12
    NSCOREDQUESTIONS = 10

    fieldspecs = (
        repeat_fieldspec(
            "q", 1, NSCOREDQUESTIONS,
            min=0, max=4,
            comment_fmt="Q{n}, {s} (0 none - 4 severe)",
            comment_strings=["facial_expression", "lips", "jaw", "tongue",
                             "upper_limbs", "lower_limbs", "trunk", "global",
                             "incapacitation", "awareness"]) +
        repeat_fieldspec(
            "q", NSCOREDQUESTIONS + 1, NQUESTIONS, pv=PV.BIT,
            comment_fmt="Q{n}, {s} (not scored) (0 no, 1 yes)",
            comment_strings=["problems_teeth_dentures",
                             "usually_wears_dentures"])
    )
    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="AIMS total score",
            axis_label="Total score (out of 40)",
            axis_min=-0.5,
            axis_max=40.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="AIMS total score {}/40".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/40)"),
        ]

    def is_complete(self) -> bool:
        return (self.are_all_fields_complete(Aims.TASK_FIELDS) and
                self.field_contents_valid())

    def total_score(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 1, Aims.NSCOREDQUESTIONS))

    def get_task_html(self) -> str:
        score = self.total_score()
        main_dict = {None: None}
        q10_dict = {None: None}
        for option in range(0, 5):
            main_dict[option] = str(option) + " — " + \
                self.wxstring("main_option" + str(option))
            q10_dict[option] = str(option) + " — " + \
                self.wxstring("q10_option" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(wappstring("total_score") + " <sup>[1]</sup>",
                answer(score) + " / 40")
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        for q in range(1, 10):
            h += tr_qa(self.wxstring("q" + str(q) + "_s"),
                       get_from_dict(main_dict, getattr(self, "q" + str(q))))
        h += (
            tr_qa(self.wxstring("q10_s"), get_from_dict(q10_dict, self.q10)) +
            tr_qa(self.wxstring("q11_s"), get_yes_no_none(self.q11)) +
            tr_qa(self.wxstring("q12_s"), get_yes_no_none(self.q12)) +
            """
                </table>
                <div class="footnotes">
                    [1] Only Q1–10 are scored.
                </div>
            """
        )
        return h
