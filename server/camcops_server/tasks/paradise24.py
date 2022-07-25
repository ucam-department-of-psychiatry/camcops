#!/usr/bin/env python

"""
camcops_server/tasks/paradise24.py

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

** PARADISE-24 task.**

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


class Paradise24Metaclass(DeclarativeMeta):
    def __init__(
        cls: Type["Paradise24"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:

        add_multiple_columns(
            cls,
            cls.Q_PREFIX,
            cls.FIRST_Q,
            cls.LAST_Q,
            coltype=Integer,
            minimum=0,
            maximum=2,
            comment_fmt="Q{n} - {s}",
            comment_strings=[
                "rested 0-2 (none - a lot)",
                "loss interest 0-2 (none - a lot)",
                "appetite 0-2 (none - a lot)",
                "sleeping 0-2 (none - a lot)",
                "irritable 0-2 (none - a lot)",
                "slowed down 0-2 (none - a lot)",
                "sad 0-2 (none - a lot)",
                "worry 0-2 (none - a lot)",
                "cope 0-2 (none - a lot)",
                "pain 0-2 (none - a lot)",
                "concentrating 0-2 (none - a lot)",
                "remembering 0-2 (none - a lot)",
                "decisions 0-2 (none - a lot)",
                "conversation 0-2 (none - a lot)",
                "walking 0-2 (none - a lot)",
                "grooming 0-2 (none - a lot)",
                "sexual 0-2 (none - a lot)",
                "staying by yourself 0-2 (none - a lot)",
                "health 0-2 (none - a lot)",
                "friendship 0-2 (none - a lot)",
                "getting along 0-2 (none - a lot)",
                "work or school 0-2 (none - a lot)",
                "money 0-2 (none - a lot)",
                "community 0-2 (none - a lot)",
            ],
        )

        super().__init__(name, bases, classdict)


class Paradise24(TaskHasPatientMixin, Task, metaclass=Paradise24Metaclass):
    __tablename__ = "paradise24"
    shortname = "PARADISE-24"

    Q_PREFIX = "q"
    FIRST_Q = 1
    LAST_Q = 24

    ALL_FIELD_NAMES = strseq(Q_PREFIX, FIRST_Q, LAST_Q)

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _("PARADISE-24")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.ALL_FIELD_NAMES):
            return False

        return True

    def total_score(self) -> int:
        return self.sum_fields(self.ALL_FIELD_NAMES)

    def metric_score(self) -> int:
        score_lookup = {
            0: 0,
            1: 10,
            2: 19,
            3: 25,
            4: 29,
            5: 33,
            6: 36,
            7: 38,
            8: 41,
            9: 43,
            10: 45,
            11: 46,
            12: 48,
            13: 50,
            14: 51,
            15: 53,
            16: 54,
            17: 55,
            18: 57,
            19: 58,
            20: 59,
            21: 60,
            22: 61,
            23: 63,
            24: 64,
            25: 65,
            26: 66,
            27: 67,
            28: 68,
            29: 69,
            30: 71,
            31: 72,
            32: 73,
            33: 74,
            34: 76,
            35: 77,
            36: 78,
            37: 80,
            38: 81,
            39: 83,
            40: 85,
            41: 87,
            42: 89,
            43: 91,
            44: 92,
            45: 94,
            46: 96,
            47: 98,
            48: 100,
        }

        return score_lookup[self.total_score()]

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = ""
        for q_num in range(self.FIRST_Q, self.LAST_Q + 1):
            field = self.Q_PREFIX + str(q_num)
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
        q_field = self.Q_PREFIX + str(q_num)

        score = getattr(self, q_field)
        meaning = self.get_score_meaning(req, q_num, score)
        answer_cell = f"{score} [{meaning}]"

        return answer_cell

    def get_score_meaning(
        self, req: CamcopsRequest, q_num: int, score: int
    ) -> str:
        return self.wxstring(req, f"option_{score}")
