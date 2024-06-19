"""
camcops_server/tasks/aq.py

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

** The Adult Autism Spectrum Quotient (AQ) Ages 16+ task.**

"""

from typing import Any, Dict, List, Optional, Type, Tuple

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, tr_qa, tr
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.cc_modules.cc_text import SS


class AqMetaclass(DeclarativeMeta):
    def __init__(
        cls: Type["Aq"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:

        add_multiple_columns(
            cls,
            cls.PREFIX,
            cls.FIRST_Q,
            cls.LAST_Q,
            coltype=Integer,
            minimum=0,
            maximum=3,
            comment_fmt=cls.PREFIX + "{n} - {s}",
            comment_strings=[
                "prefer doing things with others",
                "prefer doing things the same way",
                "can create picture in mind",
                "get strongly absorbed in one thing",
                "notice small sounds",
                "notice car number plates",
                "what I’ve said is impolite",
                "can imagine what story characters look like",
                "fascinated by dates",
                "can keep track of conversations",
                "find social situations easy",
                "notice details",
                "prefer library to party",
                "find making up stories easy",
                "drawn more strongly to people",
                "upset if can't pursue strong interests",
                "enjoy chit-chat",
                "not easy for others to get a word in edgeways",
                "fascinated by numbers",
                "can't work out story characters’ intentions",
                "don’t enjoy fiction",
                "hard to make new friends",
                "notice patterns",
                "prefer theatre to museum",
                "not upset if daily routine disturbed",
                "don't know how to keep conversation going",
                "easy to read between the lines",
                "concentrate more on whole picture",
                "can't remember phone numbers",
                "don’t notice small changes",
                "can tell if person listening is bored",
                "easy to do more than one thing",
                "not sure when to speak on phone",
                "enjoy doing things spontaneously",
                "last to understand joke",
                "can work out thinking or feeling from face",
                "can switch back after interruption",
                "good at chit-chat",
                "keep going on and on about the same thing",
                "used to enjoy pretending games with other children",
                "like to collect information about categories of things",
                "difficult to imagine being someone else",
                "like to plan activities carefully",
                "enjoy social occasions",
                "difficult to work out people’s intentions",
                "new situations make me anxious",
                "enjoy meeting new people",
                "am a good diplomat",
                "not very good at remembering people’s date of birth",
                "easy to play pretending games with children",
            ],
        )

        super().__init__(name, bases, classdict)


class Aq(TaskHasPatientMixin, Task, metaclass=AqMetaclass):
    __tablename__ = "aq"
    shortname = "AQ"

    prohibits_commercial = True

    FIRST_Q = 1
    LAST_Q = 50
    PREFIX = "q"
    MAX_SCORE = 50

    AGREE_SCORING_QUESTIONS = [
        2,
        4,
        5,
        6,
        7,
        9,
        12,
        13,
        16,
        18,
        19,
        20,
        21,
        22,
        23,
        26,
        33,
        35,
        39,
        41,
        42,
        43,
        45,
        46,
    ]

    AGREE_OPTIONS = [0, 1]

    ALL_FIELD_NAMES = strseq(PREFIX, FIRST_Q, LAST_Q)
    ALL_QUESTIONS = range(FIRST_Q, LAST_Q + 1)
    SOCIAL_SKILL_QUESTIONS = [1, 11, 13, 15, 22, 36, 44, 45, 47, 48]
    ATTENTION_SWITCHING_QUESTIONS = [2, 4, 10, 16, 25, 32, 34, 37, 43, 46]
    ATTENTION_TO_DETAIL_QUESTIONS = [5, 6, 9, 12, 19, 23, 28, 29, 30, 49]
    COMMUNICATION_QUESTIONS = [7, 17, 18, 26, 27, 31, 33, 35, 38, 39]

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _("The Adult Autism Spectrum Quotient (AQ)")

    def is_complete(self) -> bool:
        # noinspection PyUnresolvedReferences
        if self.any_fields_none(self.ALL_FIELD_NAMES):
            return False

        return True

    def score(self) -> Optional[int]:
        return self.questions_score(self.ALL_QUESTIONS)

    def social_skill_score(self) -> Optional[int]:
        return self.questions_score(self.SOCIAL_SKILL_QUESTIONS)

    def attention_switching_score(self) -> Optional[int]:
        return self.questions_score(self.ATTENTION_SWITCHING_QUESTIONS)

    def attention_to_detail_score(self) -> Optional[int]:
        return self.questions_score(self.ATTENTION_TO_DETAIL_QUESTIONS)

    def communication_score(self) -> Optional[int]:
        return self.questions_score(self.COMMUNICATION_QUESTIONS)

    def questions_score(self, q_nums: List[int]) -> Optional[int]:
        total = 0

        for q_num in q_nums:
            score = self.question_score(q_num)
            if score is None:
                return None

            total += score

        return total

    def question_score(self, q_num: int) -> Optional[int]:
        q_field = self.PREFIX + str(q_num)
        answer = getattr(self, q_field)
        if answer is None:
            return None

        agree_scored = (
            q_num in self.AGREE_SCORING_QUESTIONS
            and answer in self.AGREE_OPTIONS
        )
        disagree_scored = (
            q_num not in self.AGREE_SCORING_QUESTIONS
            and answer not in self.AGREE_OPTIONS
        )

        if agree_scored or disagree_scored:
            return 1

        return 0

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = self.get_task_html_rows(req)

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                {rows}
            </table>
            <div class="{CssClass.FOOTNOTES}">
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.sstring(SS.TOTAL_SCORE),
                answer(self.score()) + f" / {self.MAX_SCORE}",
            ),
            rows=rows,
        )
        return html

    def get_task_html_rows(self, req: CamcopsRequest) -> str:
        _ = req.gettext
        header_format = """
            <tr>
                <th width="70%">Statement</th>
                <th width="30%">Answer</th>
            </tr>
        """

        score_text = _("Score")
        header = header_format.format(
            title=self.xstring(req, "title"),
            score=score_text,
        )

        return header + self.get_task_html_rows_for_range(
            req, self.PREFIX, self.FIRST_Q, self.LAST_Q
        )

    def get_task_html_rows_for_range(
        self, req: CamcopsRequest, prefix: str, first_q: int, last_q: int
    ):
        rows = ""
        for q_num in range(first_q, last_q + 1):
            field = prefix + str(q_num)
            question_cell = f"{q_num}. {self.xstring(req, field)}"

            rows += tr_qa(
                question_cell, self.get_answer_cell(req, prefix, q_num)
            )

        return rows

    def get_answer_cell(
        self, req: CamcopsRequest, prefix: str, q_num: int
    ) -> Optional[str]:
        q_field = prefix + str(q_num)

        score = getattr(self, q_field)
        if score is None:
            return score

        meaning = self.get_score_meaning(req, score)

        answer_cell = f"{score} [{meaning}]"

        return answer_cell

    def get_score_meaning(self, req: CamcopsRequest, score: int) -> str:
        return self.wxstring(req, f"option_{score}")
