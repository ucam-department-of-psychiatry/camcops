#!/usr/bin/env python
# camcops_server/tasks/badls.py

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

from typing import Any, Dict, List, Tuple, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import (
    CssClass,
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
)
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import (
    answer,
    tr,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import CharColType
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
    TaskHasRespondentMixin,
)


# =============================================================================
# BADLS
# =============================================================================

class BadlsMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Badls'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS, CharColType,
            comment_fmt="Q{n}, {s} ('a' best [0] to 'd' worst [3]; "
                        "'e'=N/A [scored 0])",
            pv=list(cls.SCORING.keys()),
            comment_strings=cls.QUESTION_SNIPPETS
        )
        super().__init__(name, bases, classdict)


class Badls(TaskHasPatientMixin, TaskHasRespondentMixin, Task,
            metaclass=BadlsMetaclass):
    __tablename__ = "badls"
    shortname = "BADLS"
    longname = "Bristol Activities of Daily Living Scale"
    provides_trackers = True

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
    TASK_FIELDS = strseq("q", 1, NQUESTIONS)

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(name="total_score",
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score (/ 48)"),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
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

    def get_task_html(self, req: CamcopsRequest) -> str:
        q_a = ""
        for q in range(1, self.NQUESTIONS + 1):
            fieldname = "q" + str(q)
            qtext = self.wxstring(req, fieldname)  # happens to be the same
            avalue = getattr(self, "q" + str(q))
            atext = (self.wxstring(req, "q{}_{}".format(q, avalue))
                     if q is not None else None)
            score = self.score(fieldname)
            q_a += tr(qtext, answer(atext), score)
        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {complete_tr}
                    <tr>
                        <td>Total score (0–60, higher worse)</td>
                        <td>{total}</td>
                    </td>
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="30%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                    <th width="20%">Score</th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Scored a = 0, b = 1, c = 2, d = 3, e = 0.
            </div>
            {DATA_COLLECTION_UNLESS_UPGRADED_DIV}
        """.format(
            CssClass=CssClass,
            complete_tr=self.get_is_complete_tr(req),
            total=answer(self.total_score()),
            q_a=q_a,
            DATA_COLLECTION_UNLESS_UPGRADED_DIV=DATA_COLLECTION_UNLESS_UPGRADED_DIV,  # noqa
        )
        return h
