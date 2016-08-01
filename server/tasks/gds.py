#!/usr/bin/env python3
# gds.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from typing import List

from ..cc_modules.cc_constants import NO_CHAR, YES_CHAR
from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, tr, tr_qa
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task, TrackerInfo


# =============================================================================
# GAD-7
# =============================================================================

class Gds15(Task):
    NQUESTIONS = 15

    tablename = "gds15"
    shortname = "GDS-15"
    longname = "Geriatric Depression Scale, 15-item version"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, cctype="TEXT", pv=[NO_CHAR, YES_CHAR],
        comment_fmt="Q{n}, {s} ('Y' or 'N')",
        comment_strings=[
            "satisfied",
            "dropped activities",
            "life empty",
            "bored",
            "good spirits",  # 5
            "afraid",
            "happy",
            "helpless",
            "stay at home",
            "memory problems",  # 10
            "wonderful to be alive",
            "worthless",
            "full of energy",
            "hopeless",
            "others better off",  # 15
        ])

    TASK_FIELDS = [x["name"] for x in fieldspecs]
    SCORE_IF_YES = [2, 3, 4, 6, 8, 9, 10, 12, 14, 15]
    SCORE_IF_NO = [1, 5, 7, 11, 13]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="GDS-15 total score",
            axis_label="Total score (out of 15)",
            axis_min=-0.5,
            axis_max=15.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="GDS-15 total score {}/15".format(
                self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/15)"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        score = 0
        for q in self.SCORE_IF_YES:
            if getattr(self, "q" + str(q)) == YES_CHAR:
                score += 1
        for q in self.SCORE_IF_NO:
            if getattr(self, "q" + str(q)) == NO_CHAR:
                score += 1
        return score

    def get_task_html(self) -> str:
        score = self.total_score()
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 15")
        h += """
                </table>
            </div>
            <div class="explanation">
                Ratings are over the last 1 week.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """
        for q in range(1, self.NQUESTIONS + 1):
            suffix = " †" if q in self.SCORE_IF_YES else " *"
            h += tr_qa(
                str(q) + ". " + WSTRING("gds15_q" + str(q)) + suffix,
                getattr(self, "q" + str(q))
            )
        h += """
            </table>
            <div class="footnotes">
                (†) ‘Y’ scores 1; ‘N’ scores 0.
                (*) ‘Y’ scores 0; ‘N’ scores 1.
            </div>
        """
        return h
