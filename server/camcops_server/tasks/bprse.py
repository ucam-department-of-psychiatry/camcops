#!/usr/bin/env python
# bprse.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================
"""

from typing import List

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, tr, tr_qa
from ..cc_modules.cc_string import wappstring, WXSTRING
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


# =============================================================================
# BPRS-E
# =============================================================================

class Bprse(Task):
    NQUESTIONS = 24

    tablename = "bprse"
    shortname = "BPRS-E"
    longname = "Brief Psychiatric Rating Scale, Expanded"
    fieldspecs = repeat_fieldspec(
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
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="BPRS-E total score",
            axis_label="Total score (out of 168)",
            axis_min=-0.5,
            axis_max=168.5,
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="BPRS-E total score {}/168".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/168)"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self) -> str:
        def bprs_string(x: str) -> str:
            return WXSTRING("bprs", x)

        main_dict = {
            None: None,
            0: "0 — " + bprs_string("old_option0"),
            1: "1 — " + bprs_string("old_option1"),
            2: "2 — " + bprs_string("old_option2"),
            3: "3 — " + bprs_string("old_option3"),
            4: "4 — " + bprs_string("old_option4"),
            5: "5 — " + bprs_string("old_option5"),
            6: "6 — " + bprs_string("old_option6"),
            7: "7 — " + bprs_string("old_option7")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(wappstring("total_score") +
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
        for i in range(1, self.NQUESTIONS + 1):
            h += tr_qa(
                self.wxstring("q" + str(i) + "_s"),
                get_from_dict(main_dict, getattr(self, "q" + str(i)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] All answers are in the range 1–7, or 0 (not assessed, for
                    some).
            </div>
        """
        return h
