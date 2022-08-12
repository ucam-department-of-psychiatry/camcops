#!/usr/bin/env python

"""
camcops_server/tasks/isaaqed.py

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

** Internet Severity and Activities Addiction Questionnaire, Eating Disorders
   Appendix (ISAAQ-ED) task. **

"""

from typing import Any, Dict, Type, Tuple

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.tasks.isaaqcommon import IsaaqCommon


class IsaaqEdMetaclass(DeclarativeMeta):
    def __init__(
        cls: Type["IsaaqEd"],
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
            maximum=5,
            comment_fmt=cls.Q_PREFIX + "{n} - {s}",
            comment_strings=[
                "pro-ED websites 0-5 (not at all - all the time)",
                "fitspiration 0-5 (not at all - all the time)",
                "thinspiration 0-5 (not at all - all the time)",
                "bonespiration 0-5 (not at all - all the time)",
                "online dating 0-5 (not at all - all the time)",
                "calorie tracking 0-5 (not at all - all the time)",
                "fitness tracking 0-5 (not at all - all the time)",
                "cyberbullying victimization 0-5 (not at all - all the time)",
                "mukbang 0-5 (not at all - all the time)",
                "appearance-focused gaming 0-5 (not at all - all the time)",
            ],
        )

        super().__init__(name, bases, classdict)


class IsaaqEd(IsaaqCommon, metaclass=IsaaqEdMetaclass):
    __tablename__ = "isaaqed"
    shortname = "ISAAQ-ED"

    Q_PREFIX = "e"
    FIRST_Q = 11
    LAST_Q = 20

    ALL_FIELD_NAMES = strseq(Q_PREFIX, FIRST_Q, LAST_Q)

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _(
            "Internet Severity and Activities Addiction Questionnaire, "
            "Eating Disorders Appendix"
        )

    def is_complete(self) -> bool:
        if self.any_fields_none(self.ALL_FIELD_NAMES):
            return False

        return True

    def get_task_html_rows(self, req: CamcopsRequest) -> str:
        # "Scale" is a visual thing for the original; use "score" here.
        _ = req.gettext
        header = """
            <tr>
                <th width="70%">{title}</th>
                <th width="30%">{score}</th>
            </tr>
        """.format(
            title=self.xstring(req, "grid_title"),
            score=_("Score"),
        )

        return header + self.get_task_html_rows_for_range(
            req, self.Q_PREFIX, self.FIRST_Q, self.LAST_Q
        )
