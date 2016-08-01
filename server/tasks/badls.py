#!/usr/bin/env python3
# badls.py

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

from ..cc_modules.cc_constants import (
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
)
from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    tr,
)
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task


# =============================================================================
# BADLS
# =============================================================================

class Badls(Task):
    SCORING = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 0}
    NQUESTIONS = 20
    QUESTION_SNIPPETS = [
        "food",  # 1
        "eating",
        "drink",
        "drinking",
        "dressing",  # 5
        "hygiene",
        "teeth",
        "bath/shower",
        "toilet/commode",
        "transfers",  # 10
        "mobility",
        "orientation: time",
        "orientation: space",
        "communication",
        "telephone",  # 15
        "hosuework/gardening",
        "shopping",
        "finances",
        "games/hobbies",
        "transport",  # 20
    ]

    tablename = "badls"
    shortname = "BADLS"
    longname = "Bristol Activities of Daily Living Scale"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, cctype="CHAR",
        comment_fmt="Q{n}, {s} ('a' best [0] to 'd' worst [3]; "
                    "'e'=N/A [scored 0])",
        pv=list(SCORING.keys()),
        comment_strings=QUESTION_SNIPPETS
    )
    has_respondent = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total_score", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (/ 48)"),
        ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="BADLS total score {}/60 (lower is better)".format(
                self.total_score())
        )]

    def score(self, q: str) -> int:
        text_value = getattr(self, q)
        return self.SCORING.get(text_value, 0)

    def total_score(self) -> int:
        return sum(self.score(q) for q in self.TASK_FIELDS)

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid() and
            self.is_respondent_complete() and
            self.are_all_fields_complete(self.TASK_FIELDS)
        )

    def get_task_html(self) -> str:
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score (0–60, higher worse)</td>
                        <td>{total}</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="30%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                    <th width="20%">Score</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(self.total_score()),
        )
        for q in range(1, self.NQUESTIONS + 1):
            fieldname = "q" + str(q)
            qtext = self.WXSTRING(fieldname)  # happens to be the same
            avalue = getattr(self, "q" + str(q))
            atext = (self.WXSTRING("q{}_{}".format(q, avalue))
                     if q is not None else None)
            score = self.score(fieldname)
            h += tr(qtext, answer(atext), score)
        h += """
            </table>
            <div class="footnotes">
                [1] Scored a = 0, b = 1, c = 2, d = 3, e = 0.
            </div>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
