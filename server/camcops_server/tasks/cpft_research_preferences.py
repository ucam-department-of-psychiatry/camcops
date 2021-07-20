#!/usr/bin/env python

"""
camcops_server/tasks/cpft_research_preferences.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

**CPFT Research Preferences task.**

"""

from typing import Any, Dict, Optional, Tuple, Type

from sqlalchemy.ext.declarative import DeclarativeMeta

from camcops_server.cc_modules.cc_constants import CssClass, PV
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    BoolColumn,
    CamcopsColumn,
    CharColType,
    PermittedValueChecker,
)
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
)


class CpftResearchPreferencesMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(
        cls: Type["CpftResearchPreferences"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:
        setattr(
            cls,
            cls.FN_CONTACT_PREFERENCE,
            CamcopsColumn(
                cls.FN_CONTACT_PREFERENCE,
                CharColType,
                permitted_value_checker=PermittedValueChecker(
                    permitted_values=PV.RYG
                ),
            ),
        )
        setattr(
            cls, cls.FN_CONTACT_BY_EMAIL, BoolColumn(cls.FN_CONTACT_BY_EMAIL)
        )
        setattr(
            cls, cls.FN_RESEARCH_OPT_OUT, BoolColumn(cls.FN_RESEARCH_OPT_OUT)
        )

        super().__init__(name, bases, classdict)


class CpftResearchPreferences(
    TaskHasPatientMixin, Task, metaclass=CpftResearchPreferencesMetaclass
):
    """
    Server implementation of the CPFT_Research_Preferences task
    """
    __tablename__ = "cpft_research_preferences"
    shortname = "CPFT_Research_Preferences"
    provides_trackers = False

    FN_CONTACT_PREFERENCE = "contact_preference"
    FN_CONTACT_BY_EMAIL = "contact_by_email"
    FN_RESEARCH_OPT_OUT = "research_opt_out"

    MANDATORY_FIELD_NAMES = [
        FN_CONTACT_PREFERENCE,
        FN_CONTACT_BY_EMAIL,
        FN_RESEARCH_OPT_OUT,
    ]

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("CPFT Research Preferences")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.MANDATORY_FIELD_NAMES):
            return False

        if not self.field_contents_valid():
            return False

        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = ""

        for field_name in self.MANDATORY_FIELD_NAMES:
            question_text = self.xstring(req, f"q_{field_name}")
            answer_text = self.get_answer_text(req, field_name)

            rows += tr_qa(question_text, answer_text)

        html = f"""
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {self.get_is_complete_tr(req)}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {rows}
            </table>
        """

        return html

    def get_answer_text(
        self, req: CamcopsRequest, field_name: str
    ) -> Optional[str]:
        answer = getattr(self, field_name)

        if answer is None:
            return answer

        answer_text = self.xstring(req, f"{field_name}_option{answer}")

        return f"{answer} — {answer_text}"
