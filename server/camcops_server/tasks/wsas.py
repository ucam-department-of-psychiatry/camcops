#!/usr/bin/env python
# wsas.py

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

from ..cc_modules.cc_constants import DATA_COLLECTION_UNLESS_UPGRADED_DIV
from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, get_true_false, tr, tr_qa
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


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

    TASK_FIELDS = [x["name"] for x in fieldspecs]
    QUESTION_FIELDS = [x["name"] for x in QUESTION_FIELDSPECS]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="WSAS total score (lower is better)",
            axis_label="Total score (out of 40)",
            axis_min=-0.5,
            axis_max=40.5
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total_score", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (/ 40)"),
        ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(content="WSAS total score {t}/40".format(
            t=self.total_score())
        )]

    def total_score(self) -> int:
        return self.sum_fields(self.QUESTION_FIELDS)

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid() and
            self.are_all_fields_complete(self.QUESTION_FIELDS)
        )

    def get_task_html(self) -> str:
        option_dict = {None: None}
        for a in range(self.MIN_SCORE, self.MAX_SCORE + 1):
            option_dict[a] = WSTRING("wsas_a" + str(a))
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
            retired_row=tr_qa(self.wxstring("q_retired_etc"),
                              get_true_false(self.retired_etc)),
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            fa = get_from_dict(option_dict, a) if a is not None else None
            h += tr(self.wxstring("q" + str(q)), answer(fa))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
