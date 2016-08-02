#!/usr/bin/env python3
# hama.py

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
from ..cc_modules.cc_html import answer, tr, tr_qa
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# HAM-A
# =============================================================================

class Hama(Task):
    NQUESTIONS = 14

    tablename = "hama"
    shortname = "HAM-A"
    longname = "Hamilton Rating Scale for Anxiety"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (0-4, higher worse)", min=0, max=4,
        comment_strings=[
            "anxious mood", "tension", "fears", "insomnia",
            "concentration/memory", "depressed mood", "somatic, muscular",
            "somatic, sensory", "cardiovascular", "respiratory",
            "gastrointestinal", "genitourinary", "other autonomic",
            "behaviour in interview"
        ])
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="HAM-A total score",
            axis_label="Total score (out of 56)",
            axis_min=-0.5,
            axis_max=56.5,
            horizontal_lines=[30.5, 24.5, 17.5],
            horizontal_labels=[
                TrackerLabel(33, WSTRING("very_severe")),
                TrackerLabel(27.5, WSTRING("moderate_to_severe")),
                TrackerLabel(21, WSTRING("mild_to_moderate")),
                TrackerLabel(8.75, WSTRING("mild")),
            ]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="HAM-A total score {}/56 ({})".format(
                self.total_score(), self.severity())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/56)"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="Severity"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def severity(self) -> str:
        score = self.total_score()
        if score >= 31:
            return WSTRING("very_severe")
        elif score >= 25:
            return WSTRING("moderate_to_severe")
        elif score >= 18:
            return WSTRING("mild_to_moderate")
        else:
            return WSTRING("mild")

    def get_task_html(self) -> str:
        score = self.total_score()
        severity = self.severity()
        answer_dicts = []
        for q in range(1, self.NQUESTIONS + 1):
            d = {None: None}
            for option in range(0, 4):
                d[option] = WSTRING("hama_q" + str(q) + "_option" +
                                    str(option))
            answer_dicts.append(d)
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 56")
        h += tr_qa(WSTRING("hama_symptom_severity") + " <sup>[1]</sup>",
                   severity)
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        for q in range(1, self.NQUESTIONS + 1):
            h += tr_qa(
                WSTRING("hama_q" + str(q) + "_s") + " " + WSTRING(
                    "hama_q" + str(q) + "_question"),
                get_from_dict(answer_dicts[q - 1], getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] ≥31 very severe, ≥25 moderate to severe,
                    ≥18 mild to moderate, otherwise mild.
            </div>
        """
        return h
