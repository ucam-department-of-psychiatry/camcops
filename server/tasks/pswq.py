#!/usr/bin/env python3
# pswq.py

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
from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    tr,
)
from cc_modules.cc_task import Task


# =============================================================================
# IES-R
# =============================================================================

class Pswq(Task):
    MIN_SCORE = 1
    MAX_SCORE = 5
    QUESTION_SNIPPETS = [
        "OK if not enough time [REVERSE SCORE]",  # 1
        "worries overwhelm",
        "do not tend to worry [REVERSE SCORE]",
        "many situations make me worry",
        "cannot help worrying",  # 5
        "worry under pressure",
        "always worrying",
        "easily dismiss worries [REVERSE SCORE]",
        "finish then worry about next thing",
        "never worry [REVERSE SCORE]",  # 10
        "if nothing more to do, I do not worry [REVERSE SCORE]",
        "lifelong worrier",
        "have been worrying",
        "when start worrying cannot stop",
        "worry all the time",  # 15
        "worry about projects until done",
    ]
    NQUESTIONS = 16
    REVERSE_SCORE = [1, 3, 8, 10, 11]

    tablename = "pswq"
    shortname = "PSWQ"
    longname = "Penn State Worry Questionnaire"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (1-5)",
        min=MIN_SCORE, max=MAX_SCORE,
        comment_strings=QUESTION_SNIPPETS
    )

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "PSWQ total score (lower is better)",
                "axis_label": "Total score (16–80)",
                "axis_min": 15.5,
                "axis_max": 80.5,
            },
        ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total_score", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (16-80)"),
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{"content": "PSWQ total score {t} (range 16–80)".format(
            t=self.total_score())}]

    def score(self, q):
        value = getattr(self, "q" + str(q))
        if value is None:
            return None
        if q in self.REVERSE_SCORE:
            return self.MAX_SCORE + 1 - value
        else:
            return value

    def total_score(self):
        values = [self.score(q) for q in range(1, self.NQUESTIONS + 1)]
        return sum(v for v in values if v is not None)

    def is_complete(self):
        return (
            self.field_contents_valid() and
            self.are_all_fields_complete(self.TASK_FIELDS)
        )

    def get_task_html(self):
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score (16–80)</td>
                        <td>{total}</td>
                    </td>
                </table>
            </div>
            <div class="explanation">
                Anchor points are 1 = {anchor1}, 5 = {anchor5}.
                Questions {reversed_questions} are reverse-scored.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="15%">Answer (1–5)</th>
                    <th width="15%">Score (1–5)</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(self.total_score()),
            anchor1=self.WXSTRING("anchor1"),
            anchor5=self.WXSTRING("anchor5"),
            reversed_questions=", ".join(str(x) for x in self.REVERSE_SCORE)
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            score = self.score(q)
            h += tr(self.WXSTRING("q" + str(q)), answer(a), score)
        h += """
            </table>
        """
        return h
