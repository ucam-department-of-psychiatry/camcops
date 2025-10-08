"""
camcops_server/tasks/pgic.py

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

Patient Global Impression of Change (PGIC) task.

"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import tr
from camcops_server.cc_modules.cc_sqla_coltypes import (
    mapped_camcops_column,
    ONE_TO_SEVEN_CHECKER,
)
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest

DP = 2


class Pgic(TaskHasPatientMixin, Task):  # type: ignore[misc]
    __tablename__ = "pgic"
    shortname = "PGIC"

    question: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ONE_TO_SEVEN_CHECKER,
        comment="1 Very Much Improved to 7 Very Much Worse",
    )

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Patient Global Impression of Change")

    def is_complete(self) -> bool:
        return self.question is not None

    def get_task_html(self, req: "CamcopsRequest") -> str:  # produces table
        rows = self.get_task_html_rows(req)

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
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

    def get_task_html_rows(self, req: "CamcopsRequest") -> str:
        question_text = self.xstring(
            req, "question"
        )  # refers to named string in XML file
        header = f"""
            <tr>
                <th width="100%">{question_text}</th>
            </tr>
        """
        response = self.xstring(req, f"a{self.question}")
        row = tr(f"{self.question} - {response}")

        return header + row
