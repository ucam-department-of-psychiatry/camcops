#!/usr/bin/env python

"""
camcops_server/tasks/cpft_covid_medical.py

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

**CPFT Post-Covid Clinic Medical Questionnaire task.**

"""

from typing import Any, Dict, Optional, Tuple, Type

from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    ZERO_TO_THREE_CHECKER,
)
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin


class CpftCovidMedicalMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(
        cls: Type["CpftCovidMedical"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:
        setattr(
            cls,
            cls.FN_HOW_AND_WHEN_SYMPTOMS,
            CamcopsColumn(
                cls.FN_HOW_AND_WHEN_SYMPTOMS,
                Integer,
                permitted_value_checker=ZERO_TO_THREE_CHECKER,
                comment=(
                    "0 Present before C-19, "
                    "1 Within 6 weeks of catching C-19, "
                    "2 Between 6 weeks and 6 months of catching C-19, "
                    "3 Following immunisation for C-19"
                ),
            ),
        )

        super().__init__(name, bases, classdict)


class CpftCovidMedical(
    TaskHasPatientMixin, Task, metaclass=CpftCovidMedicalMetaclass
):
    """
    Server implementation of the CPFT_Covid_Medical task
    """

    __tablename__ = "cpft_covid_medical"
    shortname = "CPFT_Covid_Medical"
    provides_trackers = False

    FN_HOW_AND_WHEN_SYMPTOMS = "how_and_when_symptoms"

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("CPFT Post-COVID-19 Clinic Medical Questionnaire")

    def is_complete(self) -> bool:
        if not self.field_contents_valid():
            return False

        if getattr(self, self.FN_HOW_AND_WHEN_SYMPTOMS) is None:
            return False

        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = [
            tr_qa(
                self.wxstring(req, f"q_{self.FN_HOW_AND_WHEN_SYMPTOMS}"),
                self.get_how_and_when_symptoms_answer(req),
            )
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

    def get_how_and_when_symptoms_answer(
        self, req: CamcopsRequest
    ) -> Optional[str]:

        answer = getattr(self, self.FN_HOW_AND_WHEN_SYMPTOMS)
        if answer is None:
            return None

        return self.xstring(
            req, f"{self.FN_HOW_AND_WHEN_SYMPTOMS}_option{answer}"
        )
