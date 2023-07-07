#!/usr/bin/env python

"""
camcops_server/tasks/isaaqcommon.py

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

** Common functionality for Internet Severity and Activities Addiction
   Questionnaire (ISAAQ) tasks.**

"""

from typing import Optional

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin


# noinspection PyAbstractClass
class IsaaqCommon(TaskHasPatientMixin, Task):
    __abstract__ = True

    def is_complete(self) -> bool:
        # noinspection PyUnresolvedReferences
        if self.any_fields_none(self.ALL_FIELD_NAMES):
            return False

        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
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

    def get_task_html_rows(self, req: CamcopsRequest) -> str:
        raise NotImplementedError

    def get_task_html_rows_for_range(
        self, req: CamcopsRequest, prefix: str, first_q: int, last_q: int
    ):
        rows = ""
        for q_num in range(first_q, last_q + 1):
            field = prefix + str(q_num)
            question_cell = f"{q_num}. {self.xstring(req, field)}"

            rows += tr_qa(
                question_cell, self.get_answer_cell(req, prefix, q_num)
            )

        return rows

    def get_answer_cell(
        self, req: CamcopsRequest, prefix: str, q_num: int
    ) -> Optional[str]:
        q_field = prefix + str(q_num)

        score = getattr(self, q_field)
        if score is None:
            return score

        meaning = self.get_score_meaning(req, score)

        answer_cell = f"{score} [{meaning}]"

        return answer_cell

    def get_score_meaning(self, req: CamcopsRequest, score: int) -> str:
        return self.wxstring(req, f"freq_option_{score}")
