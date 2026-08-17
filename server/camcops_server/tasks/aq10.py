"""
camcops_server/tasks/aq10.py

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

**Autism Spectrum Quotient – 10 items (AQ-10) (Adult) task.**
"""

from typing import Any, Type

from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, tr
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_text import SS
from camcops_server.tasks.aqcommon import AqCommon


class Aq10(AqCommon):
    __tablename__ = "aq10"
    shortname = "AQ-10"

    FIRST_Q = 1
    LAST_Q = 10
    MAX_SCORE = 10

    # Questions where agreement indicates autistic-like traits.

    @classmethod
    def extend_columns(cls: Type["Aq10"], **kwargs: Any) -> None:
        add_multiple_columns(
            cls,
            cls.PREFIX,
            cls.FIRST_Q,
            cls.LAST_Q,
            coltype=Integer,
            minimum=0,
            maximum=3,
            comment_fmt=cls.PREFIX + "{n} - {s}",
            comment_strings=[
                # 1-5:
                "notice small sounds",
                "concentrate more on whole picture",
                "easy to do more than one thing",
                "can switch back after interruption",
                "easy to read between the lines",
                # 6-10:
                "can tell if person listening is bored",
                "can't work out story characters’ intentions",
                "like to collect information about categories of things",
                "can work out thinking or feeling from face",
                "difficult to work out people’s intentions",
            ],
        )

    AGREE_SCORING_QUESTIONS = [1, 7, 8, 10]

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _("Autism Spectrum Quotient – 10 items")

    def get_summaries(self, req: CamcopsRequest) -> list[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total",
                coltype=Integer(),
                value=self.score(),
                comment=f"Total score (/{self.MAX_SCORE})",
            ),
        ]

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = self.get_task_html_rows(req)

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                {rows}
            </table>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.sstring(SS.TOTAL_SCORE),
                answer(self.score()) + f" / {self.MAX_SCORE}",
            ),
            rows=rows,
        )
        return html
