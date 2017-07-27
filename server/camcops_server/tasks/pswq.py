#!/usr/bin/env python
# camcops_server/tasks/pswq.py

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

from typing import List, Optional

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, tr
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task, TrackerInfo


# =============================================================================
# IES-R
# =============================================================================

class Pswq(Task):
    tablename = "pswq"
    shortname = "PSWQ"
    longname = "Penn State Worry Questionnaire"
    provides_trackers = True

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

    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (1-5)",
        min=MIN_SCORE, max=MAX_SCORE,
        comment_strings=QUESTION_SNIPPETS
    )

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="PSWQ total score (lower is better)",
            axis_label="Total score (16–80)",
            axis_min=15.5,
            axis_max=80.5
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total_score", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (16-80)"),
        ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="PSWQ total score {t} (range 16–80)".format(
                t=self.total_score())
        )]

    def score(self, q: int) -> Optional[int]:
        value = getattr(self, "q" + str(q))
        if value is None:
            return None
        if q in self.REVERSE_SCORE:
            return self.MAX_SCORE + 1 - value
        else:
            return value

    def total_score(self) -> int:
        values = [self.score(q) for q in range(1, self.NQUESTIONS + 1)]
        return sum(v for v in values if v is not None)

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid() and
            self.are_all_fields_complete(self.TASK_FIELDS)
        )

    def get_task_html(self) -> str:
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
            anchor1=self.wxstring("anchor1"),
            anchor5=self.wxstring("anchor5"),
            reversed_questions=", ".join(str(x) for x in self.REVERSE_SCORE)
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            score = self.score(q)
            h += tr(self.wxstring("q" + str(q)), answer(a), score)
        h += """
            </table>
        """
        return h
