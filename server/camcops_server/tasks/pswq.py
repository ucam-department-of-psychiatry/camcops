#!/usr/bin/env python
# camcops_server/tasks/pswq.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

from typing import Any, Dict, List, Optional, Tuple, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, tr
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# PSWQ
# =============================================================================

class PswqMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Pswq'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS,
            minimum=cls.MIN_PER_Q, maximum=cls.MAX_PER_Q,
            comment_fmt="Q{n}, {s} (1-5)",
            comment_strings=[
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
        )
        super().__init__(name, bases, classdict)


class Pswq(TaskHasPatientMixin, Task,
           metaclass=PswqMetaclass):
    __tablename__ = "pswq"
    shortname = "PSWQ"
    longname = "Penn State Worry Questionnaire"
    provides_trackers = True

    MIN_PER_Q = 1
    MAX_PER_Q = 5
    NQUESTIONS = 16
    REVERSE_SCORE = [1, 3, 8, 10, 11]
    TASK_FIELDS = strseq("q", 1, NQUESTIONS)
    MIN_TOTAL = MIN_PER_Q * NQUESTIONS
    MAX_TOTAL = MAX_PER_Q * NQUESTIONS

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="PSWQ total score (lower is better)",
            axis_label="Total score ({}–{})".format(self.MIN_TOTAL,
                                                    self.MAX_TOTAL),
            axis_min=self.MIN_TOTAL - 0.5,
            axis_max=self.MAX_TOTAL + 0.5
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(name="total_score", coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score (16-80)"),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="PSWQ total score {} (range {}–{})".format(
                self.total_score(), self.MIN_TOTAL, self.MAX_TOTAL)
        )]

    def score(self, q: int) -> Optional[int]:
        value = getattr(self, "q" + str(q))
        if value is None:
            return None
        if q in self.REVERSE_SCORE:
            return self.MAX_PER_Q + 1 - value
        else:
            return value

    def total_score(self) -> int:
        values = [self.score(q) for q in range(1, self.NQUESTIONS + 1)]
        return sum(v for v in values if v is not None)

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {complete_tr}
                    <tr>
                        <td>Total score (16–80)</td>
                        <td>{total}</td>
                    </td>
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                Anchor points are 1 = {anchor1}, 5 = {anchor5}.
                Questions {reversed_questions} are reverse-scored.
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="70%">Question</th>
                    <th width="15%">Answer (1–5)</th>
                    <th width="15%">Score (1–5)</th>
                </tr>
        """.format(
            CssClass=CssClass,
            complete_tr=self.get_is_complete_tr(req),
            total=answer(self.total_score()),
            anchor1=self.wxstring(req, "anchor1"),
            anchor5=self.wxstring(req, "anchor5"),
            reversed_questions=", ".join(str(x) for x in self.REVERSE_SCORE)
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            score = self.score(q)
            h += tr(self.wxstring(req, "q" + str(q)), answer(a), score)
        h += """
            </table>
        """
        return h
