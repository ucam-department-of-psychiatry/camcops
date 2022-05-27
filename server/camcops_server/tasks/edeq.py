#!/usr/bin/env python

"""
camcops_server/tasks/basdai.py

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

** Eating Disorder Examination Questionnaire (EDE-Q 6.0) task.**

"""

import statistics
from typing import Any, Dict, List, Optional, Type, Tuple

from cardinal_pythonlib.stringfunc import strnumlist, strseq
from sqlalchemy import Column
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Boolean, Float, Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import tr_qa, tr, answer
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import TaskHasPatientMixin, Task
from camcops_server.cc_modules.cc_text import SS


class EdeqMetaclass(DeclarativeMeta):
    def __init__(
        cls: Type["Edeq"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:

        add_multiple_columns(
            cls,
            "q",
            1,
            12,
            coltype=Integer,
            minimum=0,
            maximum=6,
            comment_fmt="Q{n} - {s}",
            comment_strings=[
                "days limit the amount of food 0-6 (no days - every day)",
                "days long periods without eating 0-6 (no days - every day)",
                "days exclude from diet 0-6 (no days - every day)",
                "days follow rules 0-6 (no days - every day)",
                "days desire empty stomach 0-6 (no days - every day)",
                "days desire flat stomach 0-6 (no days - every day)",
                "days thinking about food 0-6 (no days - every day)",
                "days thinking about shape 0-6 (no days - every day)",
                "days fear losing control 0-6 (no days - every day)",
                "days fear weight gain 0-6 (no days - every day)",
                "days felt fat 0-6 (no days - every day)",
                "days desire lose weight 0-6 (no days - every day)",
            ],
        )

        add_multiple_columns(
            cls,
            "q",
            13,
            18,
            coltype=Integer,
            comment_fmt="Q{n} - {s}",
            comment_strings=[
                "times eaten unusually large amount of food",
                "times sense lost control",
                "days episodes of overeating",
                "times made self sick",
                "times taken laxatives",
                "times exercised in driven or compulsive way",
            ],
        )

        add_multiple_columns(
            cls,
            "q",
            19,
            21,
            coltype=Integer,
            minimum=0,
            maximum=6,
            comment_fmt="Q{n} - {s}",
            comment_strings=[
                "days eaten in secret (no days - every day)",
                "times felt guilty (none of the times - every time)",
                "concern about people seeing you eat (not at all - markedly)",
            ],
        )

        add_multiple_columns(
            cls,
            "q",
            22,
            28,
            coltype=Integer,
            minimum=0,
            maximum=6,
            comment_fmt="Q{n} - {s}",
            comment_strings=[
                "weight influenced how you judge self (not at all - markedly)",
                "shape influenced how you judge self (not at all - markedly)",
                "upset if asked to weigh self (not at all - markedly)",
                "dissatisfied with weight (not at all - markedly)",
                "dissatisfied with shape (not at all - markedly)",
                "uncomfortable seeing body (not at all - markedly)",
                "uncomfortable others seeing shape (not at all - markedly)",
            ],
        )

        setattr(
            cls,
            "q_weight",
            Column("q_weight", Float, comment="Weight (kg)"),
        )

        setattr(
            cls,
            "q_height",
            Column("q_height", Float, comment="Height (m)"),
        )

        setattr(
            cls,
            "q_num_periods_missed",
            Column(
                "q_num_periods_missed",
                Integer,
                comment="Number of periods missed",
            ),
        )

        setattr(
            cls,
            "q_pill",
            Column("q_pill", Boolean, comment="Taking the pill"),
        )

        super().__init__(name, bases, classdict)


class Edeq(TaskHasPatientMixin, Task, metaclass=EdeqMetaclass):
    __tablename__ = "edeq"
    shortname = "EDE-Q"

    N_QUESTIONS = 28
    FIELD_NAMES = strseq("q", 1, N_QUESTIONS) + [
        "q_weight",
        "q_height",
        "q_num_periods_missed",
        "q_pill",
    ]

    RESTRAINT_Q_NUMS = strnumlist("", [1, 2, 3, 4, 5])
    RESTRAINT_FIELD_NAMES = strnumlist("q", RESTRAINT_Q_NUMS)
    EATING_CONCERN_Q_NUMS = strnumlist("", [7, 9, 19, 20, 21])
    EATING_CONCERN_FIELD_NAMES = strnumlist("q", EATING_CONCERN_Q_NUMS)
    SHAPE_CONCERN_Q_NUMS = strnumlist("", [6, 8, 10, 11, 23, 26, 27, 28])
    SHAPE_CONCERN_FIELD_NAMES = strnumlist("q", SHAPE_CONCERN_Q_NUMS)
    WEIGHT_CONCERN_Q_NUMS = strnumlist("", [8, 12, 22, 24, 25])
    WEIGHT_CONCERN_FIELD_NAMES = strnumlist("q", WEIGHT_CONCERN_Q_NUMS)

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _("Eating Disorder Examination Questionnaire")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.FIELD_NAMES):
            return False

        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        score_range = "[0–7]"

        rows = ""
        for q_num in range(1, self.N_QUESTIONS + 1):
            q_field = "q" + str(q_num)
            question_cell = "{}. {}".format(q_num, self.xstring(req, q_field))

            score = getattr(self, q_field)
            if score is None or (q_num >= 13 and q_num <= 18):
                answer_cell = score
            else:
                if q_num <= 12 or q_num == 19:
                    meaning = self.wxstring(req, f"days_option_{score}")
                elif q_num == 20:
                    meaning = self.wxstring(req, f"freq_option_{score}")
                else:
                    if score % 2 == 1:
                        previous = self.wxstring(
                            req, f"how_much_option_{score-1}"
                        )
                        next = self.wxstring(req, f"how_much_option_{score+1}")
                        meaning = f"{previous}—{next}"
                    else:
                        meaning = self.wxstring(
                            req, f"how_much_option_{score}"
                        )

                answer_cell = f"{score} [{meaning}]"

            rows += tr_qa(question_cell, answer_cell)

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {global_score}
                    {restraint_score}
                    {eating_concern_score}
                    {shape_concern_score}
                    {weight_concern_score}
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
                [1] Mean of four subscales.
                [2] Mean of questions {restraint_q_nums}.
                [3] Mean of questions {eating_concern_q_nums}.
                [4] Mean of questions {shape_concern_q_nums}.
                [5] Mean of questions {weight_concern_q_nums}.
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            global_score=tr(
                req.sstring(SS.TOTAL_SCORE) + " <sup>[1]</sup>",
                f"{answer(self.global_score())} {score_range}",
            ),
            restraint_score=tr(
                self.wxstring(req, "restraint") + " <sup>[2]</sup>",
                f"{answer(self.restraint())} {score_range}",
            ),
            eating_concern_score=tr(
                self.wxstring(req, "eating_concern") + " <sup>[3]</sup>",
                f"{answer(self.eating_concern())} {score_range}",
            ),
            shape_concern_score=tr(
                self.wxstring(req, "shape_concern") + " <sup>[4]</sup>",
                f"{answer(self.shape_concern())} {score_range}",
            ),
            weight_concern_score=tr(
                self.wxstring(req, "weight_concern") + " <sup>[5]</sup>",
                f"{answer(self.weight_concern())} {score_range}",
            ),
            rows=rows,
            restraint_q_nums=",".join(self.RESTRAINT_Q_NUMS),
            eating_concern_q_nums=",".join(self.EATING_CONCERN_Q_NUMS),
            shape_concern_q_nums=",".join(self.SHAPE_CONCERN_Q_NUMS),
            weight_concern_q_nums=",".join(self.WEIGHT_CONCERN_Q_NUMS),
        )
        return html

    def restraint(self) -> Optional[float]:
        return self.subscale(self.RESTRAINT_FIELD_NAMES)

    def eating_concern(self) -> Optional[float]:
        return self.subscale(self.EATING_CONCERN_FIELD_NAMES)

    def shape_concern(self) -> Optional[float]:
        return self.subscale(self.SHAPE_CONCERN_FIELD_NAMES)

    def weight_concern(self) -> Optional[float]:
        return self.subscale(self.WEIGHT_CONCERN_FIELD_NAMES)

    def subscale(self, field_names: List[str]) -> Optional[float]:
        return statistics.mean([getattr(self, q) for q in field_names])

    def global_score(self) -> Optional[float]:
        return statistics.mean(
            [
                self.restraint(),
                self.eating_concern(),
                self.shape_concern(),
                self.weight_concern(),
            ]
        )
