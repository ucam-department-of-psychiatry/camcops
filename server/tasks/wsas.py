#!/usr/bin/env python3
# wsas.py

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
    get_true_false,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# WSAS
# =============================================================================

class Wsas(Task):
    MIN_SCORE = 0
    MAX_SCORE = 8
    QUESTION_SNIPPETS = [
        "work",
        "home management",
        "social leisure",
        "private leisure",
        "relationships",
    ]
    NQUESTIONS = 5
    QUESTION_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        min=MIN_SCORE, max=MAX_SCORE,
        comment_strings=QUESTION_SNIPPETS
    )

    tablename = "wsas"
    shortname = "WSAS"
    longname = "Work and Social Adjustment Scale"
    fieldspecs = [
        dict(name="retired_etc", cctype="BOOL",
             comment="Retired or choose not to have job for reason unrelated "
             "to problem"),
    ] + QUESTION_FIELDSPECS
    extrastring_taskname = "wsas"

    TASK_FIELDS = [x["name"] for x in fieldspecs]
    QUESTION_FIELDS = [x["name"] for x in QUESTION_FIELDSPECS]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "WSAS total score (lower is better)",
                "axis_label": "Total score (out of 40)",
                "axis_min": -0.5,
                "axis_max": 40.5,
            },
        ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total_score", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (/ 40)"),
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{"content": "WSAS total score {t}/40".format(
            t=self.total_score())}]

    def total_score(self):
        return self.sum_fields(self.QUESTION_FIELDS)

    def is_complete(self):
        return (
            self.field_contents_valid() and
            self.are_all_fields_complete(self.QUESTION_FIELDS)
        )

    def get_task_html(self):
        OPTION_DICT = {None: None}
        for a in range(self.MIN_SCORE, self.MAX_SCORE + 1):
            OPTION_DICT[a] = WSTRING("wsas_a" + str(a))
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score</td>
                        <td>{total} / 40</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="75%">Question</th>
                    <th width="25%">Answer</th>
                </tr>
                {retired_row}
            </table>
            <table class="taskdetail">
                <tr>
                    <th width="75%">Question</th>
                    <th width="25%">Answer (0–8)</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(self.total_score()),
            retired_row=tr_qa(self.WXSTRING("q_retired_etc"),
                              get_true_false(self.retired_etc)),
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            fa = get_from_dict(OPTION_DICT, a) if a is not None else None
            h += tr(self.WXSTRING("q" + str(q)), answer(fa))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
