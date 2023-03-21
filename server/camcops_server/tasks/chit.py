#!/usr/bin/env python

"""
camcops_server/tasks/chit.py

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

**Cambridge-Chicago Compulsivity Trait Scale task.**

"""

from typing import List, Type, Tuple, Dict, Any

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.stringfunc import strseq
from semantic_version import Version
from sqlalchemy import Integer
from sqlalchemy.ext.declarative import DeclarativeMeta

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import (
    tr_qa,
    tr,
    answer,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    TaskHasPatientMixin,
    Task,
    get_from_dict,
)
from camcops_server.cc_modules.cc_text import SS


class ChitMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(
        cls: Type["Chit"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:
        add_multiple_columns(
            cls,
            "q",
            1,
            cls.N_SCORED_QUESTIONS,
            minimum=cls.MIN_ANSWER,
            maximum=cls.MAX_ANSWER,
            comment_fmt="Q{n} ({s}) (0 strongly disagree - 4 strongly agree)",
            comment_strings=[
                "hate unfinished task",
                "just right",
                "keep doing task",
                "get stuck",
                "habit",
                "addictive",
                "stubborn rigid",
                "urges",
                "rewarding things",
                "hard moving",
                "higher standards",
                "improvement",
                "complete",
                "avoid situations",
                "hobby",
            ],
        )

        super().__init__(name, bases, classdict)


class Chit(TaskHasPatientMixin, Task, metaclass=ChitMetaclass):
    __tablename__ = "chit"
    shortname = "CHI-T"

    N_SCORED_QUESTIONS = 15
    MIN_ANSWER = 0
    MAX_ANSWER = 4
    MAX_SCORE_MAIN = MAX_ANSWER * N_SCORED_QUESTIONS
    SCORED_QUESTIONS = strseq("q", 1, N_SCORED_QUESTIONS)

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Cambridge–Chicago Compulsivity Trait Scale")

    # noinspection PyMethodParameters
    @classproperty
    def minimum_client_version(cls) -> Version:
        return Version("2.4.15")

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total",
                coltype=Integer(),
                value=self.total_score(),
                comment=f"Total score (/{self.MAX_SCORE_MAIN})",
            )
        ]

    def is_complete(self) -> bool:
        if self.any_fields_none(self.SCORED_QUESTIONS):
            return False
        if not self.field_contents_valid():
            return False
        return True

    def total_score(self) -> int:
        return self.sum_fields(self.SCORED_QUESTIONS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        score_dict = {
            None: None,
        }

        for i in range(self.MIN_ANSWER, self.MAX_ANSWER + 1):
            score_dict[i] = f"{i} — " + self.wxstring(req, f"a{i}")

        rows = ""
        for i in range(1, self.N_SCORED_QUESTIONS + 1):
            q_field = "q" + str(i)
            question_cell = "{}. {}".format(i, self.wxstring(req, q_field))
            answer_cell = get_from_dict(score_dict, getattr(self, q_field))

            rows += tr_qa(question_cell, answer_cell)

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer <sup>[2]</sup></th>
                </tr>
                {rows}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Sum for questions 1–15. Prior to CamCOPS version 2.4.15
                each question scored 0–3 with a maximum possible score of 45.
                [2] Prior to CamCOPS version 2.4.15 the responses were:
                0 — Strongly disagree, 1 — Disagree, 2 — Agree, 3 — Strongly
                agree.
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.sstring(SS.TOTAL_SCORE) + " <sup>[1]</sup>",
                answer(self.total_score()) + f" / {self.MAX_SCORE_MAIN}",
            ),
            rows=rows,
        )
        return html
