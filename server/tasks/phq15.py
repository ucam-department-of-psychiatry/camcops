#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

from cc_db import repeat_fieldname, repeat_fieldspec
from cc_html import (
    answer,
    get_yes_no,
    tr,
    tr_qa,
)
from cc_string import WSTRING
from cc_task import (
    CTV_DICTLIST_INCOMPLETE,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# PHQ-15
# =============================================================================

class Phq15(Task):
    NQUESTIONS = 15
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=2,
        comment_fmt="Q{n} ({s}) (0 not bothered at all - 2 bothered a lot)",
        comment_strings=[
            "stomach pain",
            "back pain",
            "limb/joint pain",
            "F - menstrual",
            "headaches",
            "chest pain",
            "dizziness",
            "fainting",
            "palpitations",
            "breathless",
            "sex",
            "constipation/diarrhoea",
            "nausea/indigestion",
            "energy",
            "sleep",
        ]
    )
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "phq15"

    @classmethod
    def get_taskshortname(cls):
        return "PHQ-15"

    @classmethod
    def get_tasklongname(cls):
        return "Patient Health Questionnaire-15"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + Phq15.TASK_FIELDSPECS

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        if not self.are_all_fields_complete(repeat_fieldname("q", 1, 3)):
            return False
        if not self.are_all_fields_complete(repeat_fieldname(
                                            "q", 5, Phq15.NQUESTIONS)):
            return False
        if self.is_female():
            return (self.q4 is not None)
        else:
            return True

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "PHQ-15 total score (rating somatic symptoms)",
                "axis_label": "Score for Q1-15 (out of 30)",
                "axis_min": -0.5,
                "axis_max": 30.5,
                "horizontal_lines": [
                    14.5,
                    9.5,
                    4.5
                ],
                "horizontal_labels": [
                    (22, WSTRING("severe")),
                    (12, WSTRING("moderate")),
                    (7, WSTRING("mild")),
                    (2.25, WSTRING("none"))
                ],
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content":
            "PHQ-15 total score {}/30 ({})".format(self.total_score(),
                                                   self.severity())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/30)"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="Severity"),
        ]

    def total_score(self):
        return self.sum_fields(Phq15.TASK_FIELDS)

    def num_severe(self):
        n = 0
        for i in range(1, Phq15.NQUESTIONS + 1):
            if getattr(self, "q" + str(i)) >= 2:
                n += 1
        return n

    def severity(self):
        score = self.total_score()
        if score >= 15:
            return WSTRING("severe")
        elif score >= 10:
            return WSTRING("moderate")
        elif score >= 5:
            return WSTRING("mild")
        else:
            return WSTRING("none")

    def get_task_html(self):
        score = self.total_score()
        nsevere = self.num_severe()
        somatoform_likely = nsevere >= 3
        severity = self.severity()
        ANSWER_DICT = {None: None}
        for option in range(0, 3):
            ANSWER_DICT[option] = str(option) + u" – " + \
                WSTRING("phq15_a" + str(option))
        h = u"""
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score") + " <sup>[1]</sup>",
                answer(score) + " / 30")
        h += tr_qa(WSTRING("phq15_n_severe_symptoms") + " <sup>[2]</sup>",
                   nsevere)
        h += tr_qa(WSTRING("phq15_exceeds_somatoform_cutoff")
                   + " <sup>[3]</sup>",
                   get_yes_no(somatoform_likely))
        h += tr_qa(WSTRING("phq15_symptom_severity") + " <sup>[4]</sup>",
                   severity)
        h += u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """
        for q in range(1, Phq15.NQUESTIONS + 1):
            h += tr_qa(
                WSTRING("phq15_q" + str(q)),
                get_from_dict(ANSWER_DICT, getattr(self, "q" + str(q)))
            )
        h += u"""
            </table>
            <div class="footnotes">
                [1] In males, maximum score is actually 28.
                [2] Questions with scores ≥2 are considered severe.
                [3] ≥3 severe symptoms.
                [4] Total score ≥15 severe, ≥10 moderate, ≥5 mild,
                    otherwise none.
            </div>
        """
        return h
