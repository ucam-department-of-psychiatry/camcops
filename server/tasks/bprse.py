#!/usr/bin/env python3
# bprse.py

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
    CLINICIAN_FIELDSPECS,
    CTV_DICTLIST_INCOMPLETE,
    STANDARD_TASK_FIELDSPECS,
)
from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# BPRS-E
# =============================================================================

class Bprse(Task):
    NQUESTIONS = 24
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=7,
        comment_fmt="Q{n}, {s} (1-7, higher worse, or 0 for not assessed)",
        comment_strings=[
            "somatic concern", "anxiety", "depression", "suicidality",
            "guilt", "hostility", "elevated mood", "grandiosity",
            "suspiciousness", "hallucinations", "unusual thought content",
            "bizarre behaviour", "self-neglect", "disorientation",
            "conceptual disorganisation", "blunted affect",
            "emotional withdrawal", "motor retardation", "tension",
            "uncooperativeness", "excitement", "distractibility",
            "motor hyperactivity", "mannerisms and posturing"])
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "bprse"

    @classmethod
    def get_taskshortname(cls):
        return "BPRS-E"

    @classmethod
    def get_tasklongname(cls):
        return "Brief Psychiatric Rating Scale, Expanded"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + \
            Bprse.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "BPRS-E total score",
                "axis_label": "Total score (out of 168)",
                "axis_min": -0.5,
                "axis_max": 168.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "BPRS-E total score {}/168".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/168)"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(Bprse.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def total_score(self):
        return self.sum_fields(Bprse.TASK_FIELDS)

    def get_task_html(self):
        MAIN_DICT = {
            None: None,
            0: "0 — " + WSTRING("bprsold_option0"),
            1: "1 — " + WSTRING("bprsold_option1"),
            2: "2 — " + WSTRING("bprsold_option2"),
            3: "3 — " + WSTRING("bprsold_option3"),
            4: "4 — " + WSTRING("bprsold_option4"),
            5: "5 — " + WSTRING("bprsold_option5"),
            6: "6 — " + WSTRING("bprsold_option6"),
            7: "7 — " + WSTRING("bprsold_option7")
        }
        h = self.get_standard_clinician_block() + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score") +
                " (0–168; 24–168 if all rated)",
                answer(self.total_score()))
        h += """
                </table>
            </div>
            <div class="explanation">
                Each question has specific answer definitions (see e.g. tablet
                app).
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer <sup>[1]</sup></th>
                </tr>
        """
        for i in range(1, Bprse.NQUESTIONS + 1):
            h += tr_qa(
                WSTRING("bprse_q" + str(i) + "_s"),
                get_from_dict(MAIN_DICT, getattr(self, "q" + str(i)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] All answers are in the range 1–7, or 0 (not assessed, for
                    some).
            </div>
        """
        return h
