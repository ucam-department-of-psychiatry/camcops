#!/usr/bin/env python

"""
camcops_server/tasks/cet.py

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

"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Float

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo, CTV_INCOMPLETE
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_fhir import (
    FHIRAnsweredQuestion,
    FHIRAnswerType,
    FHIRQuestionType,
)
from camcops_server.cc_modules.cc_html import a_href, answer, pmid, tr, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_text import SS
from camcops_server.cc_modules.cc_trackerhelpers import (
    TrackerAxisTick,
    TrackerInfo,
)

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

TARANIS_PHD_URL = (
    "https://repository.lboro.ac.uk/articles/thesis/"
    "Compulsive_exercise_and_eating_disorder_related_pathology/9609239/1"
)
CET_COPYRIGHT = f"""
CET: © Lorin Taranis, 2010. See Taranis, L. (2010). Compulsive exercise and
eating disorder related pathology. PhD thesis, Loughborough University.
{a_href(TARANIS_PHD_URL)}; EThOS ID: uk.bl.ethos.544467. Licensed under a
Creative Commons CC BY-NC-ND 2.5 licence. Additional publications include
Taranis et al. (2011), PMID {pmid(21584918)}; Meyer et al. (2016), PMID
{pmid(27547403)}.
"""


# =============================================================================
# CET
# =============================================================================


class CetMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(
        cls: Type["Cet"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:
        add_multiple_columns(
            cls,
            "q",
            1,
            cls.N_QUESTIONS,
            minimum=cls.MIN_ANSWER,
            maximum=cls.MAX_ANSWER,
            comment_fmt="Q{n} ({s}) (0 never true - 5 always true)",
            comment_strings=[
                "exercise makes happier/positive",  # 1
                "exercise to improve appearance",
                "exercise part of organised/structured day",
                "exercise makes less anxious",
                "exercise a chore",  # 5
                "exercise if eat too much",
                "exercise pattern repetitive",
                "do not exercise to be slim",
                "low/depressed if cannot exercise",
                "guilty if miss exercise",  # 10
                "continue exercise despite injury/illness",
                "enjoy exercise",
                "exercise to burn calories/lose weight",
                "exercise makes less stressed",
                "compensate if miss exercise",  # 15
                "agitated/irritable if cannot exercise",
                "exercise improves mood",
                "worry will gain weight if cannot exercise",
                "set routine for exercise",
                "angry/frustrated if cannot exercise",  # 20
                "do not enjoy exercise",
                "feel have let self down if miss exercise",
                "anxious if cannot exercise",
                "less depressed/low after exercise",  # 24
            ],
        )
        super().__init__(name, bases, classdict)


class Cet(TaskHasPatientMixin, Task, metaclass=CetMetaclass):
    """
    Server implementation of the CET task.
    """

    __tablename__ = "cet"
    shortname = "CET"
    provides_trackers = True

    FIRST_Q = 1
    N_QUESTIONS = 24
    MIN_ANSWER = 0
    MAX_ANSWER = 5
    MAX_SUBSCALE_SCORE = MAX_ANSWER
    N_SUBSCALES = 5
    MAX_TOTAL_SCORE = MAX_SUBSCALE_SCORE * N_SUBSCALES
    Q_REVERSE_SCORED = [8, 12]
    Q_SUBSCALE_1_AVOID_RULE = [9, 10, 11, 15, 16, 20, 22, 23]
    Q_SUBSCALE_2_WT_CONTROL = [2, 6, 8, 13, 18]
    Q_SUBSCALE_3_MOOD = [1, 4, 14, 17, 24]
    Q_SUBSCALE_4_LACK_EX_ENJOY = [5, 12, 21]
    Q_SUBSCALE_5_EX_RIGIDITY = [3, 7, 19]
    QUESTIONS = strseq("q", FIRST_Q, N_QUESTIONS)  # fields and string names

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Compulsive Exercise Test")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.QUESTIONS):
            return False
        if not self.field_contents_valid():
            return False
        return True

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.total_score(),
                plot_label="CET total score",
                axis_label=f"Score (out of {self.MAX_SCORE})",
                axis_min=-0.5,
                axis_max=self.MAX_SCORE + 0.5,
                axis_ticks=[
                    TrackerAxisTick(120, "120"),
                    TrackerAxisTick(100, "100"),
                    TrackerAxisTick(80, "80"),
                    TrackerAxisTick(60, "60"),
                    TrackerAxisTick(40, "40"),
                    TrackerAxisTick(20, "20"),
                    TrackerAxisTick(0, "0"),
                ],
            )
            # Trackers for subscales may be over the top.
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        ms = f"{self.MAX_SUBSCALE_SCORE}"  # ms = max subscale (score)
        return [
            CtvInfo(
                content=(
                    f"CET total score "
                    f"{self.total_score()}/{self.MAX_TOTAL_SCORE}. "
                    f"Subscales: "
                    f"#1 avoidance and rule-driven behaviour "
                    f"{self.subscale_1_avoidance_rule_based()}/{ms}; "
                    f"#2 weight control exercise "
                    f"{self.subscale_2_weight_control()}/{ms}; "
                    f"#3 mood improvement "
                    f"{self.subscale_3_mood_improvement()}/{ms}; "
                    f"#4 lack of exercise enjoyment "
                    f"{self.subscale_4_lack_enjoyment()}/{ms}; "
                    f"#5 exercise rigidity "
                    f"{self.subscale_5_rigidity()}/{ms}."
                )
            )
        ]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        ss = f" (/{self.MAX_SUBSCALE_SCORE})"  # ss = subscale suffix
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total",
                coltype=Float(),
                value=self.total_score(),
                comment=f"Total score (/{self.MAX_SCORE})",
            ),
            SummaryElement(
                name="subscale_1_avoidance_rule_based",
                coltype=Float(),
                value=self.subscale_1_avoidance_rule_based(),
                comment=(
                    "Subscale 1 score: avoidance and rule-driven behaviour"
                    + ss
                ),
            ),
            SummaryElement(
                name="subscale_2_weight_control",
                coltype=Float(),
                value=self.subscale_2_weight_control(),
                comment="Subscale 2 score: weight control exercise" + ss,
            ),
            SummaryElement(
                name="subscale_3_mood_improvement",
                coltype=Float(),
                value=self.subscale_3_mood_improvement(),
                comment="Subscale 3 score: mood improvement" + ss,
            ),
            SummaryElement(
                name="subscale_4_lack_enjoyment",
                coltype=Float(),
                value=self.subscale_4_lack_enjoyment(),
                comment="Subscale 4 score: lack of exercise enjoyment" + ss,
            ),
            SummaryElement(
                name="subscale_5_rigidity",
                coltype=Float(),
                value=self.subscale_5_rigidity(),
                comment="Subscale 5 score: exercise rigidity" + ss,
            ),
        ]

    def score(self, q: int) -> Optional[int]:
        value = getattr(self, "q" + str(q))
        if value is None:
            return None
        if q in self.Q_REVERSE_SCORED:
            return self.MAX_ANSWER - value
        else:
            return value

    def mean_score(self, questions: List[int]) -> Union[int, float, None]:
        values = [self.score(q) for q in questions]
        return self.mean_values(values, ignorevalues=[])
        # ... not including None in ignorevalues means that no mean will be
        # produced unless the task is complete.

    def subscale_1_avoidance_rule_based(self) -> float:
        return self.mean_score(self.Q_SUBSCALE_1_AVOID_RULE)

    def subscale_2_weight_control(self) -> float:
        return self.mean_score(self.Q_SUBSCALE_2_WT_CONTROL)

    def subscale_3_mood_improvement(self) -> float:
        return self.mean_score(self.Q_SUBSCALE_3_MOOD)

    def subscale_4_lack_enjoyment(self) -> float:
        return self.mean_score(self.Q_SUBSCALE_4_LACK_EX_ENJOY)

    def subscale_5_rigidity(self) -> float:
        return self.mean_score(self.Q_SUBSCALE_5)

    def total_score(self) -> int:
        return self.sum_values(
            [
                self.subscale_1_avoidance_rule_based(),
                self.subscale_2_weight_control(),
                self.subscale_3_mood_improvement(),
                self.subscale_4_lack_enjoyment(),
                self.subscale_5_rigidity(),
            ]
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        answerdict = {None: None}
        for a in range(self.MIN_ANSWER, self.MAX_ANSWER + 1):
            answerdict[a] = f"{a}: " + self.wxstring(req, f"a{a}")
        q_a = ""
        for q_field in self.QUESTIONS:
            q_a += tr_qa(
                self.wxstring(req, q_field),
                get_from_dict(answerdict, getattr(self, q_field)),
            )
        ms = f" / {self.MAX_SUBSCALE_SCORE}"

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                    {subscale_1}
                    {subscale_2}
                    {subscale_3}
                    {subscale_4}
                    {subscale_5}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Sum for all questions, with reverse-scoring of questions
                    {REVERSE_SCORED_QUESTIONS}.
            </div>
            <div class="{CssClass.COPYRIGHT}">
                {CET_COPYRIGHT}
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.sstring(SS.TOTAL_SCORE) + " <sup>[1]</sup>",
                answer(self.total_score()) + f" / {self.MAX_TOTAL_SCORE}",
            ),
            subscale_1=tr(
                self.wxstring(req, "subscale1"),
                answer(self.subscale_1_avoidance_rule_based()) + ms,
            ),
            subscale_2=tr(
                self.wxstring(req, "subscale2"),
                answer(self.subscale_2_weight_control()) + ms,
            ),
            subscale_3=tr(
                self.wxstring(req, "subscale3"),
                answer(self.subscale_3_mood_improvement()) + ms,
            ),
            subscale_4=tr(
                self.wxstring(req, "subscale4"),
                answer(self.subscale_4_lack_enjoyment()) + ms,
            ),
            subscale_5=tr(
                self.wxstring(req, "subscale5"),
                answer(self.subscale_5_rigidity()) + ms,
            ),
            q_a=q_a,
            REVERSE_SCORED_QUESTIONS=self.Q_REVERSE_SCORED,
            CET_COPYRIGHT=CET_COPYRIGHT,
        )
        return h

    # There are no SNOMED codes for "compulsive exercise" as of 2023-12-20.

    def get_fhir_questionnaire(
        self, req: "CamcopsRequest"
    ) -> List[FHIRAnsweredQuestion]:
        items = []  # type: List[FHIRAnsweredQuestion]

        answer_options = {}  # type: Dict[int, str]
        for index in range(self.MIN_ANSWER, self.MAX_ANSWER + 1):
            answer_options[index] = self.wxstring(req, f"a{index}")
        for q_field in self.QUESTIONS:
            items.append(
                FHIRAnsweredQuestion(
                    qname=q_field,
                    qtext=self.xstring(req, q_field),
                    qtype=FHIRQuestionType.CHOICE,
                    answer_type=FHIRAnswerType.INTEGER,
                    answer=getattr(self, q_field),
                    answer_options=answer_options,
                )
            )

        return items
