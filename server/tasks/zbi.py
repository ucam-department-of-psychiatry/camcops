#!/usr/bin/env python3
# zbi.py

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
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
)
from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    tr,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# ZBI
# =============================================================================

class Zbi12(Task):
    MIN_SCORE = 0
    MAX_SCORE = 4
    QUESTION_SNIPPETS = [
        "insufficient time for self",  # 1
        "stressed with other responsibilities",
        "angry",
        "other relationships affected",
        "strained",  # 5
        "health suffered",
        "insufficient privacy",
        "social life suffered",
        "lost control",
        "uncertain",  # 10
        "should do more",
        "could care better"
    ]
    NQUESTIONS = 12

    tablename = "zbi12"
    shortname = "ZBI-12"
    longname = "Zarit Burden Interview-12"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        min=MIN_SCORE, max=MAX_SCORE,
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

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{"content": "ZBI-12 total score {}/48".format(
            self.total_score())}]

    def total_score(self):
        return self.sum_fields(self.TASK_FIELDS)

    def is_complete(self):
        return (
            self.field_contents_valid() and
            self.is_respondent_complete() and
            self.are_all_fields_complete(self.TASK_FIELDS)
        )

    def get_task_html(self):
        option_dict = {None: None}
        for a in range(self.MIN_SCORE, self.MAX_SCORE + 1):
            option_dict[a] = WSTRING("zbi_a" + str(a))
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score (/ 48)</td>
                        <td>{total}</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="75%">Question</th>
                    <th width="25%">Answer (0–4)</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(self.total_score()),
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            fa = ("{}: {}".format(a, get_from_dict(option_dict, a))
                  if a is not None else None)
            h += tr(self.WXSTRING("q" + str(q)), answer(fa))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
