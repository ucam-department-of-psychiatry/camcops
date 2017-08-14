#!/usr/bin/env python
# camcops_server/tasks/zbi.py

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

from sqlalchemy.sql.sqltypes import Integer

from ..cc_modules.cc_constants import DATA_COLLECTION_UNLESS_UPGRADED_DIV
from ..cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, tr
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# ZBI
# =============================================================================

class Zbi12(Task):
    tablename = "zbi12"
    shortname = "ZBI-12"
    longname = "Zarit Burden Interview-12"
    has_respondent = True

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

    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        min=MIN_SCORE, max=MAX_SCORE,
        comment_strings=QUESTION_SNIPPETS
    )

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(name="total_score", coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score (/ 48)"),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(content="ZBI-12 total score {}/48".format(
            self.total_score()))]

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid() and
            self.is_respondent_complete() and
            self.are_all_fields_complete(self.TASK_FIELDS)
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        option_dict = {None: None}
        for a in range(self.MIN_SCORE, self.MAX_SCORE + 1):
            option_dict[a] = req.wappstring("zbi_a" + str(a))
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
            h += tr(self.wxstring(req, "q" + str(q)), answer(fa))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
