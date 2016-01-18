#!/usr/bin/env python3
# iesr.py

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
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
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
# IES-R
# =============================================================================

class Iesr(Task):
    MIN_SCORE = 0
    MAX_SCORE = 4
    QUESTION_SNIPPETS = [
        "reminder feelings",  # 1
        "sleep maintenance",
        "reminder thinking",
        "irritable",
        "avoided getting upset",  # 5
        "thought unwanted",
        "unreal",
        "avoided reminder",
        "mental pictures",
        "jumpy",  # 10
        "avoided thinking",
        "feelings undealt",
        "numb",
        "as if then",
        "sleep initiation",  # 15
        "waves of emotion",
        "tried forgetting",
        "concentration",
        "reminder physical",
        "dreams",  # 20
        "vigilant",
        "avoided talking",
    ]
    NQUESTIONS = 22
    QUESTION_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        min=MIN_SCORE, max=MAX_SCORE,
        comment_strings=QUESTION_SNIPPETS
    )

    tablename = "iesr"
    shortname = "IES-R"
    longname = "Impact of Events Scale – Revised"
    fieldspecs = [
        dict(name="event", cctype="TEXT",
             comment="Relevant event"),
    ] + QUESTION_FIELDSPECS

    TASK_FIELDS = [x["name"] for x in fieldspecs]
    QUESTION_FIELDS = [x["name"] for x in QUESTION_FIELDSPECS]
    EXTRASTRING_TASKNAME = "iesr"
    AVOIDANCE_QUESTIONS = [5, 7, 8, 11, 12, 13, 17, 22]
    INTRUSION_QUESTIONS = [1, 2, 3, 6, 9, 16, 20]
    HYPERAROUSAL_QUESTIONS = [4, 10, 14, 15, 18, 19, 21]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "IES-R total score (lower is better)",
                "axis_label": "Total score (out of 88)",
                "axis_min": -0.5,
                "axis_max": 88.5,
            },
            {
                "value": self.avoidance_score(),
                "plot_label": "IES-R avoidance score",
                "axis_label": "Avoidance score (out of 32)",
                "axis_min": -0.5,
                "axis_max": 32.5,
            },
            {
                "value": self.intrusion_score(),
                "plot_label": "IES-R intrusion score",
                "axis_label": "Intrusion score (out of 28)",
                "axis_min": -0.5,
                "axis_max": 28.5,
            },
            {
                "value": self.hyperarousal_score(),
                "plot_label": "IES-R hyperarousal score",
                "axis_label": "Hyperarousal score (out of 28)",
                "axis_min": -0.5,
                "axis_max": 28.5,
            },
        ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total_score", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (/ 88)"),
            dict(name="avoidance_score", cctype="INT",
                 value=self.avoidance_score(),
                 comment="Avoidance score (/ 32)"),
            dict(name="intrusion_score", cctype="INT",
                 value=self.intrusion_score(),
                 comment="Intrusion score (/ 28)"),
            dict(name="hyperarousal_score", cctype="INT",
                 value=self.hyperarousal_score(),
                 comment="Hyperarousal score (/ 28)"),
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        t = self.total_score()
        a = self.avoidance_score()
        i = self.intrusion_score()
        h = self.hyperarousal_score()
        return [{"content": "IES-R total score {t}/48 (avoidance {a}/32 "
                            "intrusion {i}/28, hyperarousal {h}/28)".format(
                                t=t, a=a, i=i, h=h)}]

    def total_score(self):
        return self.sum_fields(self.QUESTION_FIELDS)

    def avoidance_score(self):
        return self.sum_fields(
            self.fieldnames_from_list("q", self.AVOIDANCE_QUESTIONS))

    def intrusion_score(self):
        return self.sum_fields(
            self.fieldnames_from_list("q", self.INTRUSION_QUESTIONS))

    def hyperarousal_score(self):
        return self.sum_fields(
            self.fieldnames_from_list("q", self.HYPERAROUSAL_QUESTIONS))

    def is_complete(self):
        return (
            self.field_contents_valid()
            and self.event
            and self.are_all_fields_complete(self.QUESTION_FIELDS)
        )

    def get_task_html(self):
        OPTION_DICT = {None: None}
        for a in range(self.MIN_SCORE, self.MAX_SCORE + 1):
            OPTION_DICT[a] = WSTRING("iesr_a" + str(a))
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score</td>
                        <td>{total} / 88</td>
                    </td>
                    <tr>
                        <td>Avoidance score</td>
                        <td>{avoidance} / 32</td>
                    </td>
                    <tr>
                        <td>Intrusion score</td>
                        <td>{intrusion} / 28</td>
                    </td>
                    <tr>
                        <td>Hyperarousal score</td>
                        <td>{hyperarousal} / 28</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                {tr_event}
            </table>
            <table class="taskdetail">
                <tr>
                    <th width="75%">Question</th>
                    <th width="25%">Answer (0–4)</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(self.total_score()),
            avoidance=answer(self.avoidance_score()),
            intrusion=answer(self.intrusion_score()),
            hyperarousal=answer(self.hyperarousal_score()),
            tr_event=tr_qa(WSTRING("iesr_event"), self.event),
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            fa = ("{}: {}".format(a, get_from_dict(OPTION_DICT, a))
                  if a is not None else None)
            h += tr(self.WXSTRING("q" + str(q)), answer(fa))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
