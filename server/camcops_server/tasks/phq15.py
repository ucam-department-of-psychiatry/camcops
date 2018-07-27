#!/usr/bin/env python
# camcops_server/tasks/phq15.py

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

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, get_yes_no, tr, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import SummaryCategoryColType
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import (
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# PHQ-15
# =============================================================================

class Phq15Metaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Phq15'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS,
            minimum=0, maximum=2,
            comment_fmt="Q{n} ({s}) (0 not bothered at all - "
                        "2 bothered a lot)",
            comment_strings=[
                "stomach pain",
                "back pain",
                "limb/joint pain",
                "F - menstrual",
                "headaches",
                "chest pain",
                "dizziness",
                "fainting",
                "palpitations",
                "breathless",
                "sex",
                "constipation/diarrhoea",
                "nausea/indigestion",
                "energy",
                "sleep",
            ]
        )
        super().__init__(name, bases, classdict)


class Phq15(TaskHasPatientMixin, Task,
            metaclass=Phq15Metaclass):
    __tablename__ = "phq15"
    shortname = "PHQ-15"
    longname = "Patient Health Questionnaire-15"
    provides_trackers = True

    NQUESTIONS = 15
    MAX_TOTAL = 30

    ONE_TO_THREE = strseq("q", 1, 3)
    FIVE_TO_END = strseq("q", 5, NQUESTIONS)
    TASK_FIELDS = strseq("q", 1, NQUESTIONS)

    def is_complete(self) -> bool:
        if not self.field_contents_valid():
            return False
        if not self.are_all_fields_complete(self.ONE_TO_THREE):
            return False
        if not self.are_all_fields_complete(self.FIVE_TO_END):
            return False
        if self.is_female():
            return self.q4 is not None
        else:
            return True

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="PHQ-15 total score (rating somatic symptoms)",
            axis_label="Score for Q1-15 (out of {})".format(self.MAX_TOTAL),
            axis_min=-0.5,
            axis_max=self.MAX_TOTAL + 0.5,
            horizontal_lines=[14.5, 9.5, 4.5],
            horizontal_labels=[
                TrackerLabel(22, req.wappstring("severe")),
                TrackerLabel(12, req.wappstring("moderate")),
                TrackerLabel(7, req.wappstring("mild")),
                TrackerLabel(2.25, req.wappstring("none")),
            ]
        )]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="PHQ-15 total score {}/{} ({})".format(
                self.total_score(), self.MAX_TOTAL, self.severity(req))
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(name="total",
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score (/{})".format(self.MAX_TOTAL)),
            SummaryElement(name="severity",
                           coltype=SummaryCategoryColType,
                           value=self.severity(req),
                           comment="Severity"),
        ]

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def num_severe(self) -> int:
        n = 0
        for i in range(1, self.NQUESTIONS + 1):
            value = getattr(self, "q" + str(i))
            if value is not None and value >= 2:
                n += 1
        return n

    def severity(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        if score >= 15:
            return req.wappstring("severe")
        elif score >= 10:
            return req.wappstring("moderate")
        elif score >= 5:
            return req.wappstring("mild")
        else:
            return req.wappstring("none")

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        nsevere = self.num_severe()
        somatoform_likely = nsevere >= 3
        severity = self.severity(req)
        answer_dict = {None: None}
        for option in range(0, 3):
            answer_dict[option] = str(option) + " – " + \
                self.wxstring(req, "a" + str(option))
        q_a = ""
        for q in range(1, self.NQUESTIONS + 1):
            q_a += tr_qa(
                self.wxstring(req, "q" + str(q)),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )
        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                    {n_severe_symptoms}
                    {exceeds_somatoform_cutoff}
                    {symptom_severity}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] In males, maximum score is actually 28.
                [2] Questions with scores ≥2 are considered severe.
                [3] ≥3 severe symptoms.
                [4] Total score ≥15 severe, ≥10 moderate, ≥5 mild,
                    otherwise none.
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.wappstring("total_score") + " <sup>[1]</sup>",
                answer(score) + " / {}".format(self.MAX_TOTAL)
            ),
            n_severe_symptoms=tr_qa(
                self.wxstring(req, "n_severe_symptoms") + " <sup>[2]</sup>",
                nsevere
            ),
            exceeds_somatoform_cutoff=tr_qa(
                self.wxstring(req, "exceeds_somatoform_cutoff") +
                " <sup>[3]</sup>",
                get_yes_no(req, somatoform_likely)
            ),
            symptom_severity=tr_qa(
                self.wxstring(req, "symptom_severity") + " <sup>[4]</sup>",
                severity
            ),
            q_a=q_a,
        )
        return h
