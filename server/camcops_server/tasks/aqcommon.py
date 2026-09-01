"""
camcops_server/tasks/aqcommon.py

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

** Common functionality for Autism Spectrum Quotient (AQ) tasks.**

"""

from typing import Iterable

from cardinal_pythonlib.stringfunc import strseq

from camcops_server.cc_modules.cc_ctvinfo import CtvInfo, CTV_INCOMPLETE
from camcops_server.cc_modules.cc_fhir import (
    FHIRAnsweredQuestion,
    FHIRAnswerType,
    FHIRQuestionType,
)
from camcops_server.cc_modules.cc_html import answer, tr
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.cc_modules.cc_text import SS


# noinspection PyAbstractClass
class AqCommon(TaskHasPatientMixin, Task):  # type: ignore[misc]
    __abstract__ = True

    prohibits_commercial = True

    PREFIX = "q"

    # Internal coding (not scoring) -- in the order on the questionnaire:
    DEFINITELY_AGREE = 0
    SLIGHTLY_AGREE = 1
    SLIGHTLY_DISAGREE = 2
    DEFINITELY_DISAGREE = 3

    AGREE_OPTIONS = [DEFINITELY_AGREE, SLIGHTLY_AGREE]
    DISAGREE_OPTIONS = [SLIGHTLY_DISAGREE, DEFINITELY_DISAGREE]

    # Define in derived class
    FIRST_Q: int
    LAST_Q: int
    MAX_SCORE: int
    AGREE_SCORING_QUESTIONS: list[int]

    @classmethod
    def all_field_names(cls) -> list[str]:
        return strseq(cls.PREFIX, cls.FIRST_Q, cls.LAST_Q)

    @classmethod
    def all_questions(cls) -> Iterable[int]:
        return range(cls.FIRST_Q, cls.LAST_Q + 1)

    def is_complete(self) -> bool:
        # noinspection PyUnresolvedReferences
        if self.any_fields_none(self.all_field_names()):
            return False

        return True

    def get_clinical_text(self, req: CamcopsRequest) -> list[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [
            CtvInfo(
                content=(
                    f"{req.sstring(SS.TOTAL_SCORE)} "
                    f"{self.score()}/{self.MAX_SCORE}"
                )
            )
        ]

    def score(self) -> int | None:
        return self.questions_score(self.all_questions())

    def questions_score(self, q_nums: Iterable[int]) -> int | None:
        total = 0

        for q_num in q_nums:
            score = self.question_score(q_num)
            if score is None:
                return None

            total += score

        return total

    def question_score(self, q_num: int) -> int | None:
        """
        Returns 1 if the answer reflects autistic-like behaviour, mildly or
        strongly (per Baron-Cohen et al. 2001, p6). Returns 0 for the opposite.
        Returns None for no answer or an invalid answer.
        """
        q_field = self.PREFIX + str(q_num)
        a = getattr(self, q_field)
        if a is None:
            return None

        if q_num in self.AGREE_SCORING_QUESTIONS:
            # Questions where agreement indicates autistic-like traits
            if a in self.AGREE_OPTIONS:
                return 1
            elif a in self.DISAGREE_OPTIONS:
                return 0
            else:
                # Shouldn't happen, but safety check
                return None
        else:
            # Questions where disagreement indicates autistic-like traits
            if a in self.AGREE_OPTIONS:
                return 0
            elif a in self.DISAGREE_OPTIONS:
                return 1
            else:
                # Shouldn't happen, but safety check
                return None

    def get_task_html_rows(self, req: CamcopsRequest) -> str:
        _ = req.gettext
        css_col_prefix = self.__tablename__
        score_text = _("Score")
        header = f"""
            <tr>
                <colgroup>
                    <col class="{css_col_prefix}-statement-col" />
                    <col class="{css_col_prefix}-answer-col" />
                    <col class="{css_col_prefix}-score-col" />
                </colgroup>
                <th>Statement</th>
                <th>Answer</th>
                <th>{score_text}</th>
            </tr>
        """
        return header + self.get_task_html_rows_for_range(
            req, self.FIRST_Q, self.LAST_Q
        )

    def get_task_html_rows_for_range(
        self, req: CamcopsRequest, first_q: int, last_q: int
    ) -> str:
        rows = ""
        for q_num in range(first_q, last_q + 1):
            field = self.PREFIX + str(q_num)
            question_cell = f"{q_num}. {self.xstring(req, field)}"
            score = self.question_score(q_num)

            rows += tr(
                question_cell,
                answer(self.get_answer_cell(req, q_num)),
                score,
            )

        return rows

    def get_answer_cell(self, req: CamcopsRequest, q_num: int) -> str | None:
        q_field = self.PREFIX + str(q_num)

        response = getattr(self, q_field)
        if response is None:
            return response

        return self.wxstring(req, f"option_{response}")

    def get_fhir_questionnaire(
        self, req: CamcopsRequest
    ) -> list[FHIRAnsweredQuestion]:
        items: list[FHIRAnsweredQuestion] = []
        options: dict[int, str] = {}
        for index in range(4):
            options[index] = self.wxstring(req, f"option_{index}")
        for q_field in self.all_field_names():
            items.append(
                FHIRAnsweredQuestion(
                    qname=q_field,
                    qtext=self.xstring(req, q_field),
                    qtype=FHIRQuestionType.CHOICE,
                    answer_type=FHIRAnswerType.INTEGER,
                    answer=getattr(self, q_field),
                    answer_options=options,
                )
            )
        return items

    # No SNOMED codes for the AQ as of 2024-06-26.
