#!/usr/bin/env python

"""
camcops_server/tasks/asdas.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

**Ankylosing Spondylitis Disease Activity Score (ASDAS) task.**

"""
from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import tr_qa, tr, answer
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    ZERO_TO_10_CHECKER,
)

from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import TaskHasPatientMixin, \
    TaskHasClinicianMixin, Task
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy import Column, Float, Integer
from sqlalchemy.ext.declarative import DeclarativeMeta
from typing import List, Type, Tuple, Dict, Any


class AsdasMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Asdas'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:

        add_multiple_columns(
            cls, "q", 1, cls.N_SCALE_QUESTIONS,
            minimum=0, maximum=10,
            comment_fmt="Q{n} - {s}",
            comment_strings=[
                "back pain 0-10 (None - very severe)",
                "morning stiffness 0-10 (None - 2+ hours)",
                "patient global 0-10 (Not active - very active)",
                "peripheral pain 0-10 (None - very severe)",
            ]
        )

        setattr(
            cls, "q5",
            Column("q5", Float, comment="CRP (mg/L)")
        )

        setattr(
            cls, "q6",
            Column("q6", Float, comment="ESR (mm/h)")
        )

        super().__init__(name, bases, classdict)


class Asdas(TaskHasPatientMixin,
            TaskHasClinicianMixin,
            Task,
            metaclass=AsdasMetaclass):
    __tablename__ = "asdas"
    shortname = "ASDAS"

    N_SCALE_QUESTIONS = 4
    N_QUESTIONS = 6
    ALL_QUESTIONS = strseq("q", 1, N_QUESTIONS)

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Ankylosing Spondylitis Disease Activity Score")

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            # TODO: Log disease activity?
            SummaryElement(
                name="asdas_crp", coltype=Float(),
                value=self.asdas_crp(),
                comment=f"ASDAS-CRP"),
            SummaryElement(
                name="asdas_esr", coltype=Float(),
                value=self.asdas_esr(),
                comment=f"ASDAS-ESR"),
        ]

    def is_complete(self) -> bool:
        if self.any_fields_none(self.ALL_QUESTIONS):
            return False
        if not self.field_contents_valid():
            return False
        return True

    def overall_score(self) -> int:
        return self.mean_fields(self.ALL_QUESTIONS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = ""
        for q_num in range(1, self.N_QUESTIONS + 1):
            q_field = "q" + str(q_num)
            question_cell = "{}. {}".format(q_num, self.wxstring(req, q_field))

            score = getattr(self, q_field)

            rows += tr_qa(question_cell, score)

        formatted_score = ws.number_to_dp(self.overall_score(), 3, default="?")

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {overall_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {rows}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Mean of three numerical rating scales, each rated 0-10.
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            overall_score=tr(
                self.wxstring(req, "overall_score") + " <sup>[1]</sup>",
                "{} / {}".format(
                    answer(formatted_score),
                    self.MAX_SCORE
                )
            ),
            rows=rows,
        )
        return html
