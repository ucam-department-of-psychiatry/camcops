#!/usr/bin/env python

"""
camcops_server/tasks/isaaq10.py

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

** Internet Severity and Activities Addiction Questionnaire, 10-items
   (ISAAQ-10) task.**

"""

from typing import Any, Dict, Type, Tuple

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.tasks.isaaqcommon import IsaaqCommon


class Isaaq10Metaclass(DeclarativeMeta):
    def __init__(
        cls: Type["Isaaq10"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:

        add_multiple_columns(
            cls,
            cls.A_PREFIX,
            cls.FIRST_Q,
            cls.LAST_A_Q,
            coltype=Integer,
            minimum=0,
            maximum=5,
            comment_fmt=cls.A_PREFIX + "{n} - {s}",
            comment_strings=[
                "losing track of time 0-5 (not at all - all the time)",
                "block disturbing thoughts 0-5 (not at all - all the time)",
                "loneliness or boredom 0-5 (not at all - all the time)",
                "neglect normal activities 0-5 (not at all - all the time)",
                "school/study suffers 0-5 (not at all - all the time)",
                "try to stop 0-5 (not at all - all the time)",
                "preoccupied when offline 0-5 (not at all - all the time)",
                "lose sleep 0-5 (not at all - all the time)",
                "physical or psychological problems 0-5 "
                "(not at all - all the time)",
                "try to cut down 0-5 (not at all - all the time)",
            ],
        )

        add_multiple_columns(
            cls,
            cls.B_PREFIX,
            cls.FIRST_Q,
            cls.LAST_B_Q,
            coltype=Integer,
            minimum=0,
            maximum=5,
            comment_fmt=cls.B_PREFIX + "{n} - {s}",
            comment_strings=[
                "general surfing 0-5 (not at all - all the time)",
                "internet gaming 0-5 (not at all - all the time)",
                "skill games 0-5 (not at all - all the time)",
                "online shopping 0-5 (not at all - all the time)",
                "online gaming 0-5 (not at all - all the time)",
                "social networking 0-5 (not at all - all the time)",
                "health and medicine 0-5 (not at all - all the time)",
                "pornography 0-5 (not at all - all the time)",
                "streaming media 0-5 (not at all - all the time)",
                "cyberbullying 0-5 (not at all - all the time)",
            ],
        )

        super().__init__(name, bases, classdict)


class Isaaq10(IsaaqCommon, metaclass=Isaaq10Metaclass):
    __tablename__ = "isaaq10"
    shortname = "ISAAQ-10"

    prohibits_commercial = True

    A_PREFIX = "a"
    B_PREFIX = "b"
    FIRST_Q = 1
    LAST_A_Q = 10
    LAST_B_Q = 10

    ALL_FIELD_NAMES = strseq(A_PREFIX, FIRST_Q, LAST_A_Q) + strseq(
        B_PREFIX, FIRST_Q, LAST_B_Q
    )

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _(
            "Internet Severity and Activities Addiction Questionnaire,"
            " 10-items"
        )

    def get_task_html_rows(self, req: CamcopsRequest) -> str:
        _ = req.gettext
        header_format = """
            <tr>
                <th width="70%">{title}</th>
                <th width="30%">{score}</th>
            </tr>
        """

        # "Scale" is a visual thing for the original; use "score" here.
        score_text = _("Score")
        a_header = header_format.format(
            title=self.xstring(req, "a_title"),
            score=score_text,
        )
        b_header = header_format.format(
            title=self.xstring(req, "b_title"),
            score=score_text,
        )

        return (
            a_header
            + self.get_task_html_rows_for_range(
                req, self.A_PREFIX, self.FIRST_Q, self.LAST_A_Q
            )
            + b_header
            + self.get_task_html_rows_for_range(
                req, self.B_PREFIX, self.FIRST_Q, self.LAST_B_Q
            )
        )
