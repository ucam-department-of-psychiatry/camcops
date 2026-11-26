"""
camcops_server/tasks/ocir.py

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

**Obsessive-Compulsive Inventory Revised (OCI-R) task.**

"""

from typing import Any, Iterable, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo, CTV_INCOMPLETE
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_fhir import (
    FHIRAnsweredQuestion,
    FHIRAnswerType,
    FHIRQuestionType,
)
from camcops_server.cc_modules.cc_html import answer, sup, th, tr
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.cc_modules.cc_text import SS


def to_csv(values: Iterable[Any]) -> str:
    """
    Create a comma-separated string from iterable.
    """
    return ", ".join(str(v) for v in values)


class Ocir(TaskHasPatientMixin, Task):  # type: ignore[misc]
    __tablename__ = "ocir"
    shortname = "OCI-R"

    PREFIX = "q"

    FIRST_Q = 1
    LAST_Q = 18

    MAX_Q_SCORE = 4

    MAX_TOTAL_SCORE = LAST_Q * MAX_Q_SCORE

    QUESTIONS_PER_SUBSCALE = 3
    MAX_SUBSCALE_SCORE = MAX_Q_SCORE * QUESTIONS_PER_SUBSCALE

    WASHING_QUESTIONS = [5, 11, 17]
    OBSESSING_QUESTIONS = [6, 12, 18]
    HOARDING_QUESTIONS = [1, 7, 13]
    ORDERING_QUESTIONS = [3, 9, 15]
    CHECKING_QUESTIONS = [2, 8, 14]
    NEUTRALISING_QUESTIONS = [4, 10, 16]

    @classmethod
    def extend_columns(cls: Type["Ocir"], **kwargs: Any) -> None:
        add_multiple_columns(
            cls,
            cls.PREFIX,
            cls.FIRST_Q,
            cls.LAST_Q,
            coltype=Integer,
            minimum=0,
            maximum=cls.MAX_Q_SCORE,
            comment_fmt=cls.PREFIX + "{n} - {s}",
            comment_strings=[
                # 1-5:
                "things get in way",
                "check things",
                "objects not arranged",
                "compelled to count",
                "object touched by strangers",
                # 6-10:
                "control thoughts",
                "collect things",
                "check doors etc",
                "others change arrangement",
                "repeat numbers",
                # 11-15:
                "feel contaminated",
                "unpleasant thoughts",
                "avoid throwing away",
                "check gas etc",
                "particular order",
                # 15-18:
                "good and bad numbers",
                "handwashing",
                "nasty thoughts",
            ],
        )

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _("Obsessive-Compulsive Inventory Revised")

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
                    f"{self.score()}/{self.MAX_TOTAL_SCORE}"
                )
            )
        ]

    def score(self) -> int | None:
        return self.questions_score(self.all_questions())

    def get_summaries(self, req: CamcopsRequest) -> list[SummaryElement]:
        mss = self.MAX_SUBSCALE_SCORE
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total",
                coltype=Integer(),
                value=self.score(),
                comment=f"Total score (/{self.MAX_TOTAL_SCORE})",
            ),
            SummaryElement(
                name="washing",
                coltype=Integer(),
                value=self.washing_score(),
                comment=f"Washing score (/{mss})",
            ),
            SummaryElement(
                name="obsessing",
                coltype=Integer(),
                value=self.obsessing_score(),
                comment=f"Obsessing score (/{mss})",
            ),
            SummaryElement(
                name="hoarding",
                coltype=Integer(),
                value=self.hoarding_score(),
                comment=f"Hoarding score (/{mss})",
            ),
            SummaryElement(
                name="ordering",
                coltype=Integer(),
                value=self.ordering_score(),
                comment=f"Ordering score (/{mss})",
            ),
            SummaryElement(
                name="checking",
                coltype=Integer(),
                value=self.checking_score(),
                comment=f"Checking score (/{mss})",
            ),
            SummaryElement(
                name="neutralising",
                coltype=Integer(),
                value=self.neutralising_score(),
                comment=f"Neutralising score (/{mss})",
            ),
        ]

    def washing_score(self) -> int | None:
        return self.questions_score(self.WASHING_QUESTIONS)

    def obsessing_score(self) -> int | None:
        return self.questions_score(self.OBSESSING_QUESTIONS)

    def hoarding_score(self) -> int | None:
        return self.questions_score(self.HOARDING_QUESTIONS)

    def ordering_score(self) -> int | None:
        return self.questions_score(self.ORDERING_QUESTIONS)

    def checking_score(self) -> int | None:
        return self.questions_score(self.CHECKING_QUESTIONS)

    def neutralising_score(self) -> int | None:
        return self.questions_score(self.NEUTRALISING_QUESTIONS)

    def questions_score(self, q_nums: Iterable[int]) -> int | None:
        total = 0

        for q_num in q_nums:
            score = self.question_score(q_num)
            if score is None:
                return None

            total += score

        return total

    def question_score(self, q_num: int) -> int | None:
        q_field = self.PREFIX + str(q_num)
        return getattr(self, q_field)

    def get_task_html_rows(self, req: CamcopsRequest) -> str:
        _ = req.gettext
        statement = _("Statement")
        answer = _("Answer")
        score_text = _("Score")

        header = f"""
            <tr>
                <th>{statement}</th>
                <th>{answer}</th>
                <th>{score_text}</th>
            </tr>
        """
        return header + self.get_task_html_rows_for_range(
            req, self.FIRST_Q, self.LAST_Q
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        detail_rows = self.get_task_html_rows(req)

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                </table>
                <table class="{CssClass.SUMMARY}">
                    <colgroup>
                        <col class="{css_col_prefix}-category-col" />
                        <col class="{css_col_prefix}-total-col" />
                        <col class="{css_col_prefix}-mean-col" />
                    </colgroup>
                    {summary_header}
                    {summary_rows}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <colgroup>
                    <col class="{css_col_prefix}-statement-col" />
                    <col class="{css_col_prefix}-answer-col" />
                    <col class="{css_col_prefix}-score-col" />
                </colgroup>
                {detail_rows}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Questions {washing_q_nums}.
                [2] Questions {obsessing_q_nums}.
                [3] Questions {hoarding_q_nums}.
                [4] Questions {ordering_q_nums}.
                [5] Questions {checking_q_nums}.
                [6] Questions {neutralising_q_nums}. {scoring_notes}
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            css_col_prefix=self.__tablename__,
            summary_header=tr(
                th(self.wxstring(req, "category")),
                th(self.wxstring(req, "total")),
                th(self.wxstring(req, "mean")),
                literal=True,
            ),
            summary_rows="".join(
                [
                    self.summary_row(
                        req,
                        "washing",
                        self.washing_score(),
                        self.QUESTIONS_PER_SUBSCALE,
                        1,
                    ),
                    self.summary_row(
                        req,
                        "obsessing",
                        self.obsessing_score(),
                        self.QUESTIONS_PER_SUBSCALE,
                        2,
                    ),
                    self.summary_row(
                        req,
                        "hoarding",
                        self.hoarding_score(),
                        self.QUESTIONS_PER_SUBSCALE,
                        3,
                    ),
                    self.summary_row(
                        req,
                        "ordering",
                        self.ordering_score(),
                        self.QUESTIONS_PER_SUBSCALE,
                        4,
                    ),
                    self.summary_row(
                        req,
                        "checking",
                        self.checking_score(),
                        self.QUESTIONS_PER_SUBSCALE,
                        5,
                    ),
                    self.summary_row(
                        req,
                        "neutralising",
                        self.neutralising_score(),
                        self.QUESTIONS_PER_SUBSCALE,
                        6,
                    ),
                    self.summary_row(
                        req,
                        "total",
                        self.score(),
                        self.LAST_Q,
                    ),
                ]
            ),
            washing_q_nums=to_csv(self.WASHING_QUESTIONS),
            obsessing_q_nums=to_csv(self.OBSESSING_QUESTIONS),
            hoarding_q_nums=to_csv(self.HOARDING_QUESTIONS),
            ordering_q_nums=to_csv(self.ORDERING_QUESTIONS),
            checking_q_nums=to_csv(self.CHECKING_QUESTIONS),
            neutralising_q_nums=to_csv(self.NEUTRALISING_QUESTIONS),
            detail_rows=detail_rows,
            scoring_notes=self.wxstring(req, "scoring_notes"),
        )
        return html

    def summary_row(
        self,
        req: CamcopsRequest,
        title: str,
        score: int | None,
        num_questions: int,
        footnote_number: int = 0,
    ) -> str:

        mean = None
        if score is not None:
            mean = round(score / num_questions, 2)

        max_score = num_questions * self.MAX_Q_SCORE

        footnote = f" {sup(str(footnote_number))}" if footnote_number else ""
        return tr(
            self.wxstring(req, title) + footnote,
            answer(score) + f" / {max_score}",
            answer(mean) + f" / {self.MAX_Q_SCORE}",
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
        for index in range(self.MAX_Q_SCORE + 1):
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
