"""
camcops_server/tasks/empsa.py

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

Eating and Meal Preparation Skills Assessment (EMPSA)

"""

from typing import Optional, TYPE_CHECKING

import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy import UnicodeText
from sqlalchemy.orm import Mapped

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import answer, tr
from camcops_server.cc_modules.cc_sqla_coltypes import (
    mapped_camcops_column,
    ZERO_TO_10_CHECKER,
)
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest

DP = 2
RANGE_SUFFIX = " (0 none - 10 total)"


class Empsa(TaskHasPatientMixin, Task):  # type: ignore[misc]
    __tablename__ = "empsa"
    shortname = "EMPSA"

    q1_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q1 ability (planning)" + RANGE_SUFFIX,
    )
    q1_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q1 motivation (planning)" + RANGE_SUFFIX,
    )
    q1_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q1 comments (planning)"
    )

    q2_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q2 ability (budget)" + RANGE_SUFFIX,
    )
    q2_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q2 motivation (budget)" + RANGE_SUFFIX,
    )
    q2_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q2 comments (budget)"
    )

    q3_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q3 ability (shopping)" + RANGE_SUFFIX,
    )
    q3_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q3 motivation (shopping)" + RANGE_SUFFIX,
    )
    q3_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q3 comments (shopping)"
    )

    q4_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q4 ability (cooking)" + RANGE_SUFFIX,
    )
    q4_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q4 motivation (cooking)" + RANGE_SUFFIX,
    )
    q4_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q4 comments (cooking)"
    )

    q5_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q5 ability (preparing)" + RANGE_SUFFIX,
    )
    q5_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q5 motivation (preparing)" + RANGE_SUFFIX,
    )
    q5_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q5 comments (preparing)"
    )

    q6_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q6 ability (portions)" + RANGE_SUFFIX,
    )
    q6_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q6 motivation (portions)" + RANGE_SUFFIX,
    )
    q6_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q6 comments (portions)"
    )

    q7_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q7 ability (throwing away)" + RANGE_SUFFIX,
    )
    q7_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q7 motivation (throwing away)" + RANGE_SUFFIX,
    )
    q7_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q7 comments (throwing away)"
    )

    q8_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q8 ability (difficult food)" + RANGE_SUFFIX,
    )
    q8_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q8 motivation (difficult food)" + RANGE_SUFFIX,
    )
    q8_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q8 comments (difficult food)"
    )

    q9_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q9 ability (normal pace)" + RANGE_SUFFIX,
    )
    q9_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q9 motivation (normal pace)" + RANGE_SUFFIX,
    )
    q9_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q9 comments (normal pace)"
    )

    q10_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q10 ability (others)" + RANGE_SUFFIX,
    )
    q10_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q10 motivation (others)" + RANGE_SUFFIX,
    )
    q10_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q10 comments (others)"
    )

    q11_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q11 ability (public)" + RANGE_SUFFIX,
    )
    q11_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q11 motivation (public)" + RANGE_SUFFIX,
    )
    q11_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q11 comments (public)"
    )

    q12_ability: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q12 ability (distress)" + RANGE_SUFFIX,
    )
    q12_motivation: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ZERO_TO_10_CHECKER,
        comment="Q12 motivation (distress)" + RANGE_SUFFIX,
    )
    q12_comments: Mapped[Optional[str]] = mapped_camcops_column(
        UnicodeText, comment="Q12 comments (distress)"
    )

    PREFIX = "q"
    ABILITY_SUFFIX = "_ability"
    MOTIVATION_SUFFIX = "_motivation"
    COMMENTS_SUFFIX = "_comments"
    ALL_ABILITY_FIELD_NAMES = strseq(PREFIX, 1, 12, ABILITY_SUFFIX)
    ALL_MOTIVATION_FIELD_NAMES = strseq(PREFIX, 1, 12, MOTIVATION_SUFFIX)
    ALL_MANDATORY_FIELD_NAMES = (
        ALL_ABILITY_FIELD_NAMES + ALL_MOTIVATION_FIELD_NAMES
    )
    FIRST_Q = 1
    LAST_Q = 12
    MAX_SCORE = 10  # per question, or for subscales that are means

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Eating and Meal Preparation Skills Assessment")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.ALL_MANDATORY_FIELD_NAMES):
            return False

        return True

    def ability_subscale(self) -> Optional[float]:
        return self.mean_fields(self.ALL_ABILITY_FIELD_NAMES, ignorevalues=[])

    def motivation_subscale(self) -> Optional[float]:
        return self.mean_fields(
            self.ALL_MOTIVATION_FIELD_NAMES, ignorevalues=[]
        )

    def get_task_html(self, req: "CamcopsRequest") -> str:
        rows = self.get_task_html_rows(req)

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {ability_subscale}
                    {motivation_subscale}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                {rows}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] {ability_footnote}
                [2] {motivation_footnote}
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            ability_subscale=tr(
                self.wxstring(req, "ability") + "<sup>[1]</sup>",
                answer(
                    ws.number_to_dp(self.ability_subscale(), DP, default=None)
                )
                + f" / {self.MAX_SCORE}",
            ),
            motivation_subscale=tr(
                self.wxstring(req, "motivation") + "<sup>[2]</sup>",
                answer(
                    ws.number_to_dp(
                        self.motivation_subscale(), DP, default=None
                    ),
                )
                + f" / {self.MAX_SCORE}",
            ),
            rows=rows,
            ability_footnote=self.wxstring(req, "ability_footnote"),
            motivation_footnote=self.wxstring(req, "motivation_footnote"),
        )
        return html

    def get_task_html_rows(self, req: "CamcopsRequest") -> str:
        task_text = self.xstring(req, "task")
        ability_text = self.xstring(req, "ability")
        motivation_text = self.xstring(req, "motivation")
        comments_text = self.xstring(req, "comments")
        header = f"""
            <tr>
                <th width="2%"></th>
                <th width="41%">{task_text}</th>
                <th width="8%">{ability_text}</th>
                <th width="8%">{motivation_text}</th>
                <th width="41%">{comments_text}</th>
            </tr>
        """
        return header + self.get_task_html_rows_for_range(
            req, self.FIRST_Q, self.LAST_Q
        )

    def get_task_html_rows_for_range(
        self, req: "CamcopsRequest", first_q: int, last_q: int
    ) -> str:
        rows = ""
        for q_num in range(first_q, last_q + 1):
            q_str = f"{self.PREFIX}{q_num}"
            ability_field = f"{q_str}{self.ABILITY_SUFFIX}"
            motivation_field = f"{q_str}{self.MOTIVATION_SUFFIX}"
            comments_field = f"{q_str}{self.COMMENTS_SUFFIX}"
            question_cell = self.xstring(req, q_str)

            rows += tr(
                str(q_num),
                question_cell,
                answer(getattr(self, ability_field)),
                answer(getattr(self, motivation_field)),
                answer(getattr(self, comments_field), default=""),
            )

        return rows
