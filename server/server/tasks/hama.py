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

from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    CLINICIAN_FIELDSPECS,
    CTV_DICTLIST_INCOMPLETE,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# HAM-A
# =============================================================================

class Hama(Task):
    NQUESTIONS = 14
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (0-4, higher worse)", min=0, max=4,
        comment_strings=[
            "anxious mood", "tension", "fears", "insomnia",
            "concentration/memory", "depressed mood", "somatic, muscular",
            "somatic, sensory", "cardiovascular", "respiratory",
            "gastrointestinal", "genitourinary", "other autonomic",
            "behaviour in interview"
        ])
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "hama"

    @classmethod
    def get_taskshortname(cls):
        return "HAM-A"

    @classmethod
    def get_tasklongname(cls):
        return "Hamilton Rating Scale for Anxiety"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + \
            Hama.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "HAM-A total score",
                "axis_label": "Total score (out of 56)",
                "axis_min": -0.5,
                "axis_max": 56.5,
                "horizontal_lines": [
                    30.5,
                    24.5,
                    17.5,
                ],
                "horizontal_labels": [
                    (33, WSTRING("very_severe")),
                    (27.5, WSTRING("moderate_to_severe")),
                    (21, WSTRING("mild_to_moderate")),
                    (8.75, WSTRING("mild")),
                ]
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{"content": "HAM-A total score {}/56 ({})".format(
            self.total_score(), self.severity())}]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/56)"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="Severity"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(Hama.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def total_score(self):
        return self.sum_fields(Hama.TASK_FIELDS)

    def severity(self):
        score = self.total_score()
        if score >= 31:
            return WSTRING("very_severe")
        elif score >= 25:
            return WSTRING("moderate_to_severe")
        elif score >= 18:
            return WSTRING("mild_to_moderate")
        else:
            return WSTRING("mild")

    def get_task_html(self):
        score = self.total_score()
        severity = self.severity()
        ANSWER_DICTS = []
        for q in range(1, Hama.NQUESTIONS + 1):
            d = {None: None}
            for option in range(0, 4):
                d[option] = WSTRING("hama_q" + str(q) + "_option" +
                                    str(option))
            ANSWER_DICTS.append(d)
        h = self.get_standard_clinician_block() + u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 56")
        h += tr_qa(WSTRING("hama_symptom_severity") + " <sup>[1]</sup>",
                   severity)
        h += u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        for q in range(1, Hama.NQUESTIONS + 1):
            h += tr_qa(
                WSTRING("hama_q" + str(q) + "_s") + " " + WSTRING(
                    "hama_q" + str(q) + "_question"),
                get_from_dict(ANSWER_DICTS[q - 1], getattr(self, "q" + str(q)))
            )
        h += u"""
            </table>
            <div class="footnotes">
                [1] ≥31 very severe, ≥25 moderate to severe,
                    ≥18 mild to moderate, otherwise mild.
            </div>
        """
        return h
