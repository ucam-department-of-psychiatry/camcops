#!/usr/bin/env python

"""
camcops_server/tasks/isaaq.py

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

** Internet Severity and Activities Addiction Questionnaire (ISAAQ) task.**

"""

from typing import Any, Dict, Type, Tuple

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import TaskHasPatientMixin, Task


class IsaaqMetaclass(DeclarativeMeta):
    def __init__(
        cls: Type["Isaaq"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:

        add_multiple_columns(
            cls,
            "a",
            1,
            15,
            coltype=Integer,
            minimum=0,
            maximum=5,
            comment_fmt="a{n} - {s}",
            comment_strings=[
                "losing track of time 0-5 (not at all - all the time)",
                "block disturbing thoughts 0-5 (not at all - all the time)",
                "loneliness or boredom 0-5 (not at all - all the time)",
                "neglect normal activities 0-5 (not at all - all the time)",
                "choose over intimacy 0-5 (not at all - all the time)",
                "financial consequences 0-5 (not at all - all the time)",
                "school/study suffers 0-5 (not at all - all the time)",
                "check email or social media 0-5 (not at all - all the time)",
                "others complain 0-5 (not at all - all the time)",
                "defensive or secretive 0-5 (not at all - all the time)",
                "try to arrest 0-5 (not at all - all the time)",
                "preoccupied when offline 0-5 (not at all - all the time)",
                "lose sleep 0-5 (not at all - all the time)",
                (
                    "physical or psychological problems 0-5 "
                    "(not at all - all the time)"
                ),
                "try to cut down 0-5 (not at all - all the time)",
            ],
        )

        add_multiple_columns(
            cls,
            "b",
            1,
            10,
            coltype=Integer,
            minimum=0,
            maximum=5,
            comment_fmt="b{n} - {s}",
            comment_strings=[
                "general surfing 0-5 (not at all - all the time)",
                "internet gaming 0-5 (not at all - all the time)",
                "skill games 0-5 (not at all - all the time)",
                "online shopping 0-5 (not at all - all the time)",
                "online gaming 0-5 (not at all - all the time)",
                "social networking 0-5 (not at all - all the time)",
                "health and medicine 0-5 (not at all - all the time)",
                "pornography 0-5 (not at all - all the time)",
                "streaming media 0-5 (not at all - all the time)",
                "cyberbullying 0-5 (not at all - all the time)",
            ],
        )

        super().__init__(name, bases, classdict)


class Isaaq(TaskHasPatientMixin, Task, metaclass=IsaaqMetaclass):
    __tablename__ = "isaaq"
    shortname = "ISAAQ"

    N_A_QUESTIONS = 15
    N_B_QUESTIONS = 10

    ALL_FIELD_NAMES = strseq("a", 1, N_A_QUESTIONS) + strseq(
        "b", 1, N_B_QUESTIONS
    )

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _("Internet Severity and Activities Addiction Questionnaire")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.ALL_FIELD_NAMES):
            return False

        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = ""
        for q_num in range(1, self.N_A_QUESTIONS + 1):
            field = "a" + str(q_num)
            question_cell = self.xstring(req, field)

            rows += tr_qa(question_cell, self.get_answer_cell(req, q_num))

        for q_num in range(1, self.N_B_QUESTIONS + 1):
            field = "b" + str(q_num)
            question_cell = self.xstring(req, field)

            rows += tr_qa(question_cell, self.get_answer_cell(req, q_num))

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
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
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            rows=rows,
        )
        return html

    def get_answer_cell(self, req: CamcopsRequest, q_num: int) -> str:
        q_field = "q" + str(q_num)

        score = getattr(self, q_field)
        if score is None:
            return score

        meaning = self.get_score_meaning(req, q_num, score)

        answer_cell = f"{score} [{meaning}]"

        return answer_cell

    def get_score_meaning(
        self, req: CamcopsRequest, q_num: int, score: int
    ) -> str:
        return self.wxstring(req, f"freq_option_{score}")
