#!/usr/bin/env python3
# fast.py

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

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, get_yes_no, tr, tr_qa
from ..cc_modules.cc_string import WSTRING
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
    NQUESTIONS = 4

    tablename = "fast"
    shortname = "FAST"
    longname = "Fast Alcohol Screening Test"
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
            0: "0 — " + WSTRING("fast_q1to3_option0"),
            1: "1 — " + WSTRING("fast_q1to3_option1"),
            2: "2 — " + WSTRING("fast_q1to3_option2"),
            3: "3 — " + WSTRING("fast_q1to3_option3"),
            4: "4 — " + WSTRING("fast_q1to3_option4"),
        }
        q4_dict = {
            None: None,
            0: "0 — " + WSTRING("fast_q4_option0"),
            2: "2 — " + WSTRING("fast_q4_option2"),
            4: "4 — " + WSTRING("fast_q4_option4"),
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(self.total_score()) + " / 16")
        h += tr_qa(WSTRING("fast_positive") + " <sup>[1]</sup>",
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
        h += tr_qa(WSTRING("fast_q1"), get_from_dict(main_dict, self.q1))
        h += tr_qa(WSTRING("fast_q2"), get_from_dict(main_dict, self.q2))
        h += tr_qa(WSTRING("fast_q3"), get_from_dict(main_dict, self.q3))
        h += tr_qa(WSTRING("fast_q4"), get_from_dict(q4_dict, self.q4))
        h += """
            </table>
            <div class="footnotes">
                [1] Negative if Q1 = 0. Positive if Q1 ≥ 3. Otherwise positive
                    if total score ≥ 3.
            </div>
        """
        return h
