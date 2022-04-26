#!/usr/bin/env python

"""
camcops_server/tasks/cpft_research_preferences.py

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

**CPFT Research Preferences task.**

"""

from typing import Any, Dict, Optional, Tuple, Type

from sqlalchemy.ext.declarative import DeclarativeMeta

from camcops_server.cc_modules.cc_constants import CssClass, PV
from camcops_server.cc_modules.cc_html import tr_qa, get_yes_no_unknown
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    BoolColumn,
    CamcopsColumn,
    CharColType,
    PermittedValueChecker,
)
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin


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
        if not self.field_contents_valid():
            return False

        contact_preference = getattr(self, self.FN_CONTACT_PREFERENCE)
        if contact_preference is None:
            return False

        if contact_preference != "R":
            return getattr(self, self.FN_CONTACT_BY_EMAIL) is not None

        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = [
            tr_qa(
                self.wxstring(req, f"q_{self.FN_CONTACT_PREFERENCE}_short"),
                self.get_contact_preference_answer(req),
            ),
            tr_qa(
                self.wxstring(req, f"q_{self.FN_CONTACT_BY_EMAIL}_short"),
                self.get_contact_by_email_answer(req),
            ),
            tr_qa(
                self.wxstring(req, f"q_{self.FN_RESEARCH_OPT_OUT}_short"),
                self.get_research_opt_out_answer(req),
            ),
        ]

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
                {''.join(rows)}
            </table>
        """

        return html

    def get_contact_preference_answer(
        self, req: CamcopsRequest
    ) -> Optional[str]:

        answer = getattr(self, self.FN_CONTACT_PREFERENCE)
        if answer is None:
            return None

        return self.xstring(req, answer)

    def get_contact_by_email_answer(
        self, req: CamcopsRequest
    ) -> Optional[str]:
        return get_yes_no_unknown(req, getattr(self, self.FN_CONTACT_BY_EMAIL))

    def get_research_opt_out_answer(
        self, req: CamcopsRequest
    ) -> Optional[str]:
        return get_yes_no_unknown(req, getattr(self, self.FN_RESEARCH_OPT_OUT))
