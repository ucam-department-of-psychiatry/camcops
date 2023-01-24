#!/usr/bin/env python

"""
camcops_server/tasks/cia.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

**The Clinical Impairment Assessment questionnaire (CIA) task.**

"""

from typing import Any, Dict, Optional, Type, Tuple

from cardinal_pythonlib.stringfunc import strnumlist, strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import tr_qa, tr, answer
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import TaskHasPatientMixin, Task
from camcops_server.cc_modules.cc_text import SS


class CiaMetaclass(DeclarativeMeta):
    def __init__(
        cls: Type["Cia"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:

        add_multiple_columns(
            cls,
            cls.Q_PREFIX,
            cls.FIRST_Q,
            cls.LAST_Q,
            coltype=Integer,
            minimum=0,
            maximum=3,
            comment_fmt=cls.Q_PREFIX + "{n} - {s}",
            comment_strings=[
                "difficult to concentrate",
                "critical of self",
                "going out",
                "affected work performance",
                "forgetful",
                "everyday decisions",
                "meals with family",
                "upset",
                "ashamed",
                "difficult to eat out",
                "guilty",
                "things used to enjoy",
                "absent-minded",
                "failure",
                "relationships",
                "worry",
            ],
        )

        super().__init__(name, bases, classdict)


class Cia(TaskHasPatientMixin, Task, metaclass=CiaMetaclass):
    __tablename__ = "cia"
    shortname = "CIA"

    Q_PREFIX = "q"
    FIRST_Q = 1
    LAST_Q = 16
    MAX_SCORE = 48

    ALL_FIELD_NAMES = strseq(Q_PREFIX, FIRST_Q, LAST_Q)
    MANDATORY_QUESTIONS = [1, 2, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16]
    MANDATORY_FIELD_NAMES = strnumlist(Q_PREFIX, MANDATORY_QUESTIONS)

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _("The Clinical Impairment Assessment questionnaire")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.MANDATORY_FIELD_NAMES):
            return False

        return True

    def global_score(self) -> Optional[float]:
        """
        The original paper states:

        "To obtain the global CIA impairment score the ratings on all items are
        added together with prorating of missing ratings, so long as at least
        12 of the 16 items have been rated."

        In our implementation all questions are mandatory except for 3, 4, 7
        and 10. So there won't be fewer than 12 items rated for a complete
        questionnaire.
        """
        if not self.is_complete():
            return None

        num_answered = self.n_fields_not_none(self.ALL_FIELD_NAMES)
        scale_factor = self.LAST_Q / num_answered

        return scale_factor * self.sum_fields(self.ALL_FIELD_NAMES)

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = ""
        for q_num in range(self.FIRST_Q, self.LAST_Q + 1):
            field = self.Q_PREFIX + str(q_num)
            question_cell = "{}. {}".format(q_num, self.wxstring(req, field))

            rows += tr_qa(question_cell, self.get_answer_cell(req, q_num))

        global_score = self.global_score()
        if global_score is None:
            global_score_display = "?"
        else:
            global_score_display = "{:.2f} / {}".format(
                global_score, self.MAX_SCORE
            )

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {global_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Score</th>
                </tr>
                {rows}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Sum for all questions with prorating of missing ratings,
                so long as at least 12 of the 16 items have been rated.
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            global_score=tr(
                req.sstring(SS.TOTAL_SCORE) + "<sup>[1]</sup>",
                answer(global_score_display),
            ),
            rows=rows,
        )
        return html

    def get_answer_cell(self, req: CamcopsRequest, q_num: int) -> str:
        q_field = self.Q_PREFIX + str(q_num)

        score = getattr(self, q_field)
        if score is None:
            if q_num in self.MANDATORY_QUESTIONS:
                return "?"

            return req.sstring(SS.NA)

        meaning = self.get_score_meaning(req, score)
        return f"{score} [{meaning}]"

    def get_score_meaning(self, req: CamcopsRequest, score: int) -> str:
        return self.wxstring(req, f"option_{score}")
