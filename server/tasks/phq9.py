#!/usr/bin/env python3
# phq9.py

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
)
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    get_yes_no,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# PHQ-9
# =============================================================================

class Phq9(Task):
    tablename = "phq9"
    shortname = "PHQ-9"
    longname = "Patient Health Questionnaire-9"
    fieldspecs = repeat_fieldspec(
        "q", 1, 9, min=0, max=3,
        comment_fmt="Q{n} ({s}) (0 not at all - 3 nearly every day)",
        comment_strings=[
            "anhedonia",
            "mood",
            "sleep",
            "energy",
            "appetite",
            "self-esteem/guilt",
            "concentration",
            "psychomotor",
            "death/self-harm",
        ]
    ) + [
        dict(name="q10", cctype="INT", min=0, max=3,
             comment="Q10 (difficulty in activities) (0 not difficult at "
                     "all - 3 extremely difficult)"),

    ]

    N_MAIN_QUESTIONS = 9

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        if not self.are_all_fields_complete(repeat_fieldname("q", 1, 9)):
            return False
        if self.total_score() > 0 and self.q10 is None:
            return False
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "PHQ-9 total score (rating depressive symptoms)",
                "axis_label": "Score for Q1-9 (out of 27)",
                "axis_min": -0.5,
                "axis_max": 27.5,
                "axis_ticks": [
                    (27, "27"),
                    (25, "25"),
                    (20, "20"),
                    (15, "15"),
                    (10, "10"),
                    (5, "5"),
                    (0, "0"),
                ],
                "horizontal_lines": [
                    19.5,
                    14.5,
                    9.5,
                    4.5
                ],
                "horizontal_labels": [
                    (23, WSTRING("severe")),
                    (17, WSTRING("moderately_severe")),
                    (12, WSTRING("moderate")),
                    (7, WSTRING("mild")),
                    (2.25, WSTRING("none"))
                ]
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{"content": "PHQ-9 total score {}/27 ({})".format(
            self.total_score(), self.severity())}]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/27)"),
            dict(name="n_core", cctype="INT", value=self.n_core(),
                 comment="Number of core symptoms"),
            dict(name="n_other", cctype="INT", value=self.n_other(),
                 comment="Number of other symptoms"),
            dict(name="n_total", cctype="INT", value=self.n_total(),
                 comment="Total number of symptoms"),
            dict(name="is_mds", cctype="BOOL", value=self.is_mds(),
                 comment="PHQ9 major depressive syndrome?"),
            dict(name="is_ods", cctype="BOOL", value=self.is_ods(),
                 comment="PHQ9 other depressive syndrome?"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="PHQ9 depression severity"),
        ]

    def total_score(self):
        return self.sum_fields(repeat_fieldname("q", 1, 9))

    def one_if_q_ge(self, qnum, threshold):
        value = getattr(self, "q" + str(qnum))
        return 1 if value is not None and value >= threshold else 0

    def n_core(self):
        return (self.one_if_q_ge(1, 2) +
                self.one_if_q_ge(2, 2))

    def n_other(self):
        return (self.one_if_q_ge(3, 2) +
                self.one_if_q_ge(4, 2) +
                self.one_if_q_ge(5, 2) +
                self.one_if_q_ge(6, 2) +
                self.one_if_q_ge(7, 2) +
                self.one_if_q_ge(8, 2) +
                self.one_if_q_ge(9, 1))  # suicidality
        # suicidality counted whenever present

    def n_total(self):
        return self.n_core() + self.n_other()

    def is_mds(self):
        return True if self.n_core() >= 1 and self.n_total() >= 5 else False

    def is_ods(self):
        return True if self.n_core() >= 1 and self.n_total() >= 2 and \
            self.n_total() <= 4 else False

    def severity(self):
        total = self.total_score()
        if total >= 20:
            return WSTRING("severe")
        elif total >= 15:
            return WSTRING("moderately_severe")
        elif total >= 10:
            return WSTRING("moderate")
        elif total >= 5:
            return WSTRING("mild")
        else:
            return WSTRING("none")

    def get_task_html(self):
        MAIN_DICT = {
            None: None,
            0: "0 — " + WSTRING("phq9_a0"),
            1: "1 — " + WSTRING("phq9_a1"),
            2: "2 — " + WSTRING("phq9_a2"),
            3: "3 — " + WSTRING("phq9_a3")
        }
        Q10_DICT = {
            None: None,
            0: "0 — " + WSTRING("phq9_fa0"),
            1: "1 — " + WSTRING("phq9_fa1"),
            2: "2 — " + WSTRING("phq9_fa2"),
            3: "3 — " + WSTRING("phq9_fa3")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score") + " <sup>[1]</sup>",
                answer(self.total_score()) + " / 27")
        h += tr_qa(WSTRING("phq9_depression_severity") + " <sup>[2]</sup>",
                   self.severity())
        h += tr(
            "Number of symptoms: core <sup>[3]</sup>, other <sup>[4]</sup>, "
            "total",
            answer(self.n_core()) + "/2, "
            + answer(self.n_other()) + "/7, "
            + answer(self.n_total()) + "/9"
        )
        h += tr_qa(WSTRING("phq9_mds") + " <sup>[5]</sup>",
                   get_yes_no(self.is_mds()))
        h += tr_qa(WSTRING("phq9_ods") + " <sup>[6]</sup>",
                   get_yes_no(self.is_ods()))
        h += """
                </table>
            </div>
            <div class="explanation">
                Ratings are over the last 2 weeks.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """
        for i in range(1, self.N_MAIN_QUESTIONS + 1):
            nstr = str(i)
            h += tr_qa(WSTRING("phq9_q" + nstr),
                       get_from_dict(MAIN_DICT, getattr(self, "q" + nstr)))
        h += tr_qa("10. " + WSTRING("phq9_finalq"),
                   get_from_dict(Q10_DICT, self.q10))
        h += """
            </table>
            <div class="footnotes">
                [1] Sum for questions 1–9.
                [2] Total score ≥20 severe, ≥15 moderately severe,
                    ≥10 moderate, ≥5 mild, &lt;5 none.
                [3] Number of questions 1–2 rated ≥2.
                [4] Number of questions 3–8 rated ≥2, or question 9
                    rated ≥1.
                [5] ≥1 core symptom and ≥5 total symptoms (as per
                    DSM-IV-TR page 356).
                [6] ≥1 core symptom and 2–4 total symptoms (as per
                    DSM-IV-TR page 775).
            </div>
        """
        return h
