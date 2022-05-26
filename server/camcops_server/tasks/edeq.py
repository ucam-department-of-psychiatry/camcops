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

from typing import Any, Dict, Optional, Type, Tuple

from cardinal_pythonlib.stringfunc import strnumlist, strseq
from sqlalchemy import Column
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Boolean, Float, Integer

from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import TaskHasPatientMixin, Task


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

    RESTRAINT_FIELD_NAMES = strseq("q", 1, 5)
    EATING_CONCERN_FIELD_NAMES = strnumlist("q", [7, 9, 19, 20, 21])
    SHAPE_CONCERN_FIELD_NAMES = strnumlist("q", [6, 8, 10, 11, 23, 26, 27, 28])
    WEIGHT_CONCERN_FIELD_NAMES = strnumlist("q", [8, 12, 22, 24, 25])

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _("Eating Disorder Examination Questionnaire")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.FIELD_NAMES):
            return False

        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        # TODO
        return ""

    def restraint(self) -> Optional[float]:
        return sum([getattr(self, q) for q in self.RESTRAINT_FIELD_NAMES]) / 5

    def eating_concern(self) -> Optional[float]:
        return (
            sum([getattr(self, q) for q in self.EATING_CONCERN_FIELD_NAMES])
            / 5
        )

    def shape_concern(self) -> Optional[float]:
        return (
            sum([getattr(self, q) for q in self.SHAPE_CONCERN_FIELD_NAMES]) / 8
        )

    def weight_concern(self) -> Optional[float]:
        return (
            sum([getattr(self, q) for q in self.WEIGHT_CONCERN_FIELD_NAMES])
            / 5
        )
