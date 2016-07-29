#!/usr/bin/env python3
# gad7.py

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

from ..cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
)
from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# GAD-7
# =============================================================================

class Gad7(Task):
    NQUESTIONS = 7

    tablename = "gad7"
    shortname = "GAD-7"
    longname = "Generalized Anxiety Disorder Assessment"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=3,
        comment_fmt="Q{n}, {s} (0 not at all - 3 nearly every day)",
        comment_strings=[
            "nervous/anxious/on edge",
            "can't stop/control worrying",
            "worrying too much about different things",
            "trouble relaxing",
            "restless",
            "irritable",
            "afraid"
        ])

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "GAD-7 total score",
                "axis_label": "Total score (out of 21)",
                "axis_min": -0.5,
                "axis_max": 21.5,
                "horizontal_lines": [
                    14.5,
                    9.5,
                    4.5
                ],
                "horizontal_labels": [
                    (17, WSTRING("severe")),
                    (12, WSTRING("moderate")),
                    (7, WSTRING("mild")),
                    (2.25, WSTRING("none"))
                ]
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{"content": "GAD-7 total score {}/21 ({})".format(
            self.total_score(), self.severity())}]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/21)"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="Severity"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self):
        return self.sum_fields(self.TASK_FIELDS)

    def severity(self):
        score = self.total_score()
        if score >= 15:
            severity = WSTRING("severe")
        elif score >= 10:
            severity = WSTRING("moderate")
        elif score >= 5:
            severity = WSTRING("mild")
        else:
            severity = WSTRING("none")
        return severity

    def get_task_html(self):
        score = self.total_score()
        severity = self.severity()
        answer_dict = {None: None}
        for option in range(0, 4):
            answer_dict[option] = (
                str(option) + " — " + WSTRING("gad7_a" + str(option))
            )
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 21")
        h += tr(WSTRING("gad7_anxiety_severity") + " <sup>[1]</sup>",
                severity)
        h += """
                </table>
            </div>
            <div class="explanation">
                Ratings are over the last 2 weeks.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        for q in range(1, self.NQUESTIONS + 1):
            h += tr_qa(
                WSTRING("gad7_q" + str(q)),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] ≥15 severe, ≥10 moderate, ≥5 mild.
                Score ≥10 identifies: generalized anxiety disorder with
                sensitivity 89%, specificity 82% (Spitzer et al. 2006, PubMed
                ID 16717171);
                panic disorder with sensitivity 74%, specificity 81% (Kroenke
                et al. 2010, PMID 20633738);
                social anxiety with sensitivity 72%, specificity 80% (Kroenke
                et al. 2010);
                post-traumatic stress disorder with sensitivity 66%,
                specificity 81% (Kroenke et al. 2010).
                The majority of evidence contributing to these figures comes
                from primary care screening studies.
            </div>
        """
        return h
