#!/usr/bin/env python

"""
camcops_server/tasks/phq8.py

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
from typing import Any, Dict, List, Tuple, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Boolean, Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo, CTV_INCOMPLETE
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_fhir import (
    FHIRAnsweredQuestion,
    FHIRAnswerType,
    FHIRQuestionType,
)
from camcops_server.cc_modules.cc_html import answer, get_yes_no, tr, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    SummaryCategoryColType,
)
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
    TrackerLabel,
)

log = logging.getLogger(__name__)


# =============================================================================
# PHQ-8
# =============================================================================


class Phq8Metaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(
        cls: Type["Phq8"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:
        add_multiple_columns(
            cls,
            "q",
            1,
            cls.N_QUESTIONS,
            minimum=0,
            maximum=3,
            comment_fmt="Q{n} ({s}) (0 not at all - 3 nearly every day)",
            comment_strings=[
                "anhedonia",
                "mood",
                "sleep",
                "energy",
                "appetite",
                "self-esteem/guilt",
                "concentration",
                "psychomotor",
            ],
        )
        super().__init__(name, bases, classdict)


class Phq8(TaskHasPatientMixin, Task, metaclass=Phq8Metaclass):
    """
    Server implementation of the Phq8 task.
    """

    __tablename__ = "phq8"
    shortname = "PHQ-8"
    provides_trackers = True

    N_QUESTIONS = 8
    MAX_SCORE = 3 * N_QUESTIONS
    QUESTIONS = strseq("q", 1, N_QUESTIONS)

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Patient Health Questionnaire 8-item depression scale")

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
                plot_label="PHQ-8 total score (rating depressive symptoms)",
                axis_label=f"Score (out of {self.MAX_SCORE})",
                axis_min=-0.5,
                axis_max=self.MAX_SCORE + 0.5,
                axis_ticks=[
                    TrackerAxisTick(24, "24"),  # maximum
                    TrackerAxisTick(20, "20"),
                    TrackerAxisTick(15, "15"),
                    TrackerAxisTick(10, "10"),
                    TrackerAxisTick(5, "5"),
                    TrackerAxisTick(0, "0"),
                ],
                horizontal_lines=[19.5, 14.5, 9.5, 4.5],
                horizontal_labels=[
                    TrackerLabel(23, req.sstring(SS.SEVERE)),
                    TrackerLabel(17, req.sstring(SS.MODERATELY_SEVERE)),
                    TrackerLabel(12, req.sstring(SS.MODERATE)),
                    TrackerLabel(7, req.sstring(SS.MILD)),
                    TrackerLabel(2.25, req.sstring(SS.NONE)),
                ],
            )
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [
            CtvInfo(
                content=(
                    f"PHQ-8 total score "
                    f"{self.total_score()}/{self.MAX_SCORE} "
                    f"({self.severity(req)})"
                )
            )
        ]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total",
                coltype=Integer(),
                value=self.total_score(),
                comment=f"Total score (/{self.MAX_SCORE})",
            ),
            SummaryElement(
                name="n_core",
                coltype=Integer(),
                value=self.n_core(),
                comment="Number of core symptoms",
            ),
            SummaryElement(
                name="n_other",
                coltype=Integer(),
                value=self.n_other(),
                comment="Number of other symptoms",
            ),
            SummaryElement(
                name="n_total",
                coltype=Integer(),
                value=self.n_total(),
                comment="Total number of symptoms",
            ),
            SummaryElement(
                name="is_mds",
                coltype=Boolean(),
                value=self.is_mds(),
                comment="PHQ8 major depressive syndrome?",
            ),
            SummaryElement(
                name="is_ods",
                coltype=Boolean(),
                value=self.is_ods(),
                comment="PHQ8 other depressive syndrome?",
            ),
            SummaryElement(
                name="severity",
                coltype=SummaryCategoryColType,
                value=self.severity(req),
                comment="PHQ8 depression severity",
            ),
        ]

    def total_score(self) -> int:
        return self.sum_fields(self.QUESTIONS)

    def reaches_threshold(self, qnum: int) -> int:
        # Checks if a symptom scores >=2, meaning "more than half the days".
        # Kroenke et al. (2010); see Phq8::detail() in phq8.cpp
        threshold = 2
        value = getattr(self, "q" + str(qnum))
        return 1 if value is not None and value >= threshold else 0

    def n_core(self) -> int:
        # Questions 1 and 2
        return sum(self.reaches_threshold(qnum) for qnum in range(1, 2 + 1))

    def n_other(self) -> int:
        # Questions 3-8
        return sum(self.reaches_threshold(qnum) for qnum in range(3, 8 + 1))

    def n_total(self) -> int:
        return self.n_core() + self.n_other()

    def is_mds(self) -> bool:
        # Kroenke et al. (2010); see Phq8::detail() in phq8.cpp
        return self.n_core() >= 1 and self.n_total() >= 5

    def is_ods(self) -> bool:
        # Kroenke et al. (2010); see Phq8::detail() in phq8.cpp
        return self.n_core() >= 1 and 2 <= self.n_total() <= 4

    def severity(self, req: CamcopsRequest) -> str:
        # Kroenke et al. (2010); see Phq8::severity() in phq8.cpp
        total = self.total_score()
        if total >= 20:
            return req.sstring(SS.SEVERE)
        elif total >= 15:
            return req.sstring(SS.MODERATELY_SEVERE)
        elif total >= 10:
            return req.sstring(SS.MODERATE)
        elif total >= 5:
            return req.sstring(SS.MILD)
        else:
            return req.sstring(SS.NONE)

    def get_task_html(self, req: CamcopsRequest) -> str:
        answer_dict = {
            None: None,
            0: "0 — " + self.wxstring(req, "a0"),
            1: "1 — " + self.wxstring(req, "a1"),
            2: "2 — " + self.wxstring(req, "a2"),
            3: "3 — " + self.wxstring(req, "a3"),
        }
        q_a = ""
        for i in range(1, self.N_QUESTIONS + 1):
            nstr = str(i)
            q_a += tr_qa(
                self.wxstring(req, "q" + nstr),
                get_from_dict(answer_dict, getattr(self, "q" + nstr)),
            )

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                    {depression_severity}
                    {n_symptoms}
                    {mds}
                    {ods}
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                Ratings are over the last 2 weeks.
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Sum for questions 1–8.
                [2] Total score ≥20 severe, ≥15 moderately severe,
                    ≥10 moderate, ≥5 mild, &lt;5 none.<sup>[7]</sup>
                [3] Number of questions 1–2 rated ≥2.<sup>[7]</sup>
                [4] Number of questions 3–8 rated ≥2.<sup>[7]</sup>
                [5] ≥1 core symptom and ≥5 total symptoms.<sup>[7]</sup>
                [6] ≥1 core symptom and 2–4 total symptoms.<sup>[7]</sup>
                [7] Kroenke et al. (2010), PMID 18752852.
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.sstring(SS.TOTAL_SCORE) + " <sup>[1]</sup>",
                answer(self.total_score()) + f" / {self.MAX_SCORE}",
            ),
            depression_severity=tr_qa(
                self.wxstring(req, "depression_severity") + " <sup>[2]</sup>",
                self.severity(req),
            ),
            n_symptoms=tr(
                "Number of symptoms: core <sup>[3]</sup>, other "
                "<sup>[4]</sup>, total",
                answer(self.n_core())
                + "/2, "
                + answer(self.n_other())
                + "/6, "
                + answer(self.n_total())
                + "/8",
            ),
            mds=tr_qa(
                self.wxstring(req, "mds") + " <sup>[5]</sup>",
                get_yes_no(req, self.is_mds()),
            ),
            ods=tr_qa(
                self.wxstring(req, "ods") + " <sup>[6]</sup>",
                get_yes_no(req, self.is_ods()),
            ),
            q_a=q_a,
        )
        return h

    # No SNOMED CT codes for the PHQ-8 (just the PHQ-9), 2022-11-30.

    def get_fhir_questionnaire(
        self, req: "CamcopsRequest"
    ) -> List[FHIRAnsweredQuestion]:
        items = []  # type: List[FHIRAnsweredQuestion]

        answer_options = {}  # type: Dict[int, str]
        for index in range(4):
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
