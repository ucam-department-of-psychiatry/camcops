#!/usr/bin/env python3
# aims.py

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

from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
    CLINICIAN_FIELDSPECS,
    PV,
    STANDARD_TASK_FIELDSPECS,
)
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# AIMS
# =============================================================================

class Aims(Task):
    NQUESTIONS = 12
    NSCOREDQUESTIONS = 10
    TASK_FIELDSPECS = (
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
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "aims"

    @classmethod
    def get_taskshortname(cls):
        return "AIMS"

    @classmethod
    def get_tasklongname(cls):
        return "Abnormal Involuntary Movement Scale"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + \
            Aims.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "AIMS total score",
                "axis_label": "Total score (out of 40)",
                "axis_min": -0.5,
                "axis_max": 40.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "AIMS total score {}/40".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/40)"),
        ]

    def is_complete(self):
        return (self.are_all_fields_complete(Aims.TASK_FIELDS) and
                self.field_contents_valid())

    def total_score(self):
        return self.sum_fields(repeat_fieldname("q", 1, Aims.NSCOREDQUESTIONS))

    def get_task_html(self):
        score = self.total_score()
        MAIN_DICT = {None: None}
        Q10_DICT = {None: None}
        for option in range(0, 5):
            MAIN_DICT[option] = str(option) + " — " + \
                WSTRING("aims_main_option" + str(option))
            Q10_DICT[option] = str(option) + " — " + \
                WSTRING("aims_q10_option" + str(option))
        h = self.get_standard_clinician_block() + """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score") + " <sup>[1]</sup>",
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
            h += tr_qa(WSTRING("aims_q" + str(q) + "_s"),
                       get_from_dict(MAIN_DICT, getattr(self, "q" + str(q))))
        h += (
            tr_qa(WSTRING("aims_q10_s"), get_from_dict(Q10_DICT, self.q10))
            + tr_qa(WSTRING("aims_q11_s"), get_yes_no_none(self.q11))
            + tr_qa(WSTRING("aims_q12_s"), get_yes_no_none(self.q12))
            + """
                </table>
                <div class="footnotes">
                    [1] Only Q1–10 are scored.
                </div>
            """
        )
        return h
