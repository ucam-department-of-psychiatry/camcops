#!/usr/bin/env python

"""
camcops_server/tasks/apeq_cpft_perinatal.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

"""

from typing import Dict, List, Optional

from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import Task


# =============================================================================
# APEQCPFTPerinatal
# =============================================================================

class APEQCPFTPerinatal(Task):
    """
    Server implementation of the APEQ-CPFT-Perinatal task.
    """
    __tablename__ = "apeq_cpft_perinatal"
    shortname = "APEQ-CPFT-Perinatal"

    FIRST_MAIN_Q = 1
    LAST_MAIN_Q = 6
    FN_QPREFIX = "q"
    MAIN_EXPLANATION = " (0 no, 1 yes to some extent, 2 yes)"

    q1 = Column(
        "q1", Integer,
        comment="Q1. Treated with respect/dignity" + MAIN_EXPLANATION
    )
    q2 = Column(
        "q2", Integer,
        comment="Q2. Felt listened to" + MAIN_EXPLANATION
    )
    q3 = Column(
        "q3", Integer,
        comment="Q3. Needs were understood" + MAIN_EXPLANATION
    )
    q4 = Column(
        "q4", Integer,
        comment="Q4. Given info about team" + MAIN_EXPLANATION
    )
    q5 = Column(
        "q5", Integer,
        comment="Q5. Family considered/included" + MAIN_EXPLANATION
    )
    q6 = Column(
        "q6", Integer,
        comment="Q6. Views on treatment taken into account" + MAIN_EXPLANATION
    )
    ff_rating = Column(
        "ff_rating", Integer,
        comment="How likely to recommend service to friends and family "
                "(0 don't know, 1 extremely unlikely, 2 unlikely, "
                "3 neither likely nor unlikely, 4 likely, 5 extremely likely)"
    )
    ff_why = Column(
        "ff_why", UnicodeText,
        comment="Why was friends/family rating given as it was?"
    )
    comments = Column(
        "comments", UnicodeText,
        comment="General comments"
    )

    REQUIRED_FIELDS = ["q1", "q2", "q3", "q4", "q5", "q6", "ff_rating"]

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Assessment Patient Experience Questionnaire for "
                 "CPFT Perinatal Services")

    def is_complete(self) -> bool:
        return self.all_fields_not_none(self.REQUIRED_FIELDS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        options_main = {None: "?"}  # type: Dict[Optional[int], str]
        for o in range(0, 2 + 1):
            options_main[o] = self.wxstring(req, f"main_a{o}")
        options_ff = {None: "?"}  # type: Dict[Optional[int], str]
        for o in range(0, 5 + 1):
            options_ff[o] = self.wxstring(req, f"ff_a{o}")

        qlines = []  # type: List[str]
        for qnum in range(self.FIRST_MAIN_Q, self.LAST_MAIN_Q + 1):
            xstring_attr_name = f"q{qnum}"
            qlines.append(tr_qa(
                self.wxstring(req, xstring_attr_name),
                options_main.get(getattr(self, xstring_attr_name))))
        q_a = "".join(qlines)
        return f"""
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
                {q_a}
                {tr_qa(self.wxstring(req, "q_ff_rating"),
                       options_ff.get(self.ff_rating))}
                {tr_qa(self.wxstring(req, "q_ff_why"),
                       self.ff_why or "")}
                {tr_qa(self.wxstring(req, "q_comments"),
                       self.comments or "")}
            </table>
        """
