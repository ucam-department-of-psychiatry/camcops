#!/usr/bin/env python3
# hamd7.py

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
# HAMD-7
# =============================================================================

class Hamd7(Task):
    NQUESTIONS = 7
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=4,  # see below
        comment_fmt="Q{n}, {s} (0-4, except Q6 0-2; higher worse)",
        comment_strings=["depressed mood", "guilt",
                         "interest/pleasure/level of activities",
                         "psychological anxiety", "somatic anxiety",
                         "energy/somatic symptoms", "suicide"]
    )
    # Now fix the wrong bits. Hardly elegant!
    for item in TASK_FIELDSPECS:
        if item["name"] == "q6":
            item["max"] = 2
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "hamd7"

    @classmethod
    def get_taskshortname(cls):
        return "HAMD-7"

    @classmethod
    def get_tasklongname(cls):
        return "Hamilton Rating Scale for Depression (7-item scale)"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + \
            Hamd7.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "HAM-D-7 total score",
                "axis_label": "Total score (out of 26)",
                "axis_min": -0.5,
                "axis_max": 26.5,
                "horizontal_lines": [
                    19.5,
                    11.5,
                    3.5,
                ],
                "horizontal_labels": [
                    (23, WSTRING("hamd7_severity_severe")),
                    (15.5, WSTRING("hamd7_severity_moderate")),
                    (7.5, WSTRING("hamd7_severity_mild")),
                    (1.75, WSTRING("hamd7_severity_none")),
                ]
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "HAM-D-7 total score {}/26 ({})".format(
                self.total_score(), self.severity())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/26)"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="Severity"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(Hamd7.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def total_score(self):
        return self.sum_fields(Hamd7.TASK_FIELDS)

    def severity(self):
        score = self.total_score()
        if score >= 20:
            return WSTRING("hamd7_severity_severe")
        elif score >= 12:
            return WSTRING("hamd7_severity_moderate")
        elif score >= 4:
            return WSTRING("hamd7_severity_mild")
        else:
            return WSTRING("hamd7_severity_none")

    def get_task_html(self):
        score = self.total_score()
        severity = self.severity()
        ANSWER_DICTS = []
        for q in range(1, Hamd7.NQUESTIONS + 1):
            d = {None: None}
            for option in range(0, 5):
                if q == 6 and option > 2:
                    continue
                d[option] = WSTRING("hamd7_q" + str(q) + "_option" +
                                    str(option))
            ANSWER_DICTS.append(d)
        h = self.get_standard_clinician_block() + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 26")
        h += tr_qa(WSTRING("hamd7_severity") + " <sup>[1]</sup>", severity)
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="30%">Question</th>
                    <th width="70%">Answer</th>
                </tr>
        """
        for q in range(1, Hamd7.NQUESTIONS + 1):
            h += tr_qa(
                WSTRING("hamd7_q" + str(q) + "_s"),
                get_from_dict(ANSWER_DICTS[q - 1], getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] ≥20 severe, ≥12 moderate, ≥4 mild, &lt;4 none.
            </div>
        """
        return h
