#!/usr/bin/env python
# camcops_server/tasks/factg.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

from cardinal_pythonlib.stringfunc import strseq
from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import tr_qa, tr, answer
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    BIT_CHECKER,
    CamcopsColumn,
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import (
    TrackerInfo,
)
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Boolean
from typing import Any, Dict, List, Tuple, Type


# =============================================================================
# Fact-G
# =============================================================================

class FactgMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Factg'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:

        add_multiple_columns(
            cls, "p_q", 1, cls.N_QUESTIONS_PHYSICAL,
            minimum=0, maximum=4,
        )
        add_multiple_columns(
            cls, "s_q", 1, cls.N_QUESTIONS_SOCIAL,
            minimum=0, maximum=4,
        )
        add_multiple_columns(
            cls, "e_q", 1, cls.N_QUESTIONS_EMOTIONAL,
            minimum=0, maximum=4,
        )
        add_multiple_columns(
            cls, "f_q", 1, cls.N_QUESTIONS_FUNCTIONAL,
            minimum=0, maximum=4,
        )
        super().__init__(name, bases, classdict)


class Factg(TaskHasPatientMixin, Task,
            metaclass=FactgMetaclass):
    """
    Server implementation of the Fact-G task.
    """
    __tablename__ = "factg"
    shortname = "FACT-G"
    longname = "Functional Assessment of Cancer Therapy - General"
    provides_trackers = True

    N_QUESTIONS_PHYSICAL = 7
    N_QUESTIONS_SOCIAL = 7
    N_QUESTIONS_EMOTIONAL = 6
    N_QUESTIONS_FUNCTIONAL = 7

    MAX_SCORE_PHYSICAL = 28
    MAX_SCORE_SOCIAL = 28
    MAX_SCORE_EMOTIONAL = 24
    MAX_SCORE_FUNCTIONAL = 28

    MAX_SCORE_TOTAL = MAX_SCORE_PHYSICAL + MAX_SCORE_SOCIAL
    MAX_SCORE_TOTAL += MAX_SCORE_EMOTIONAL + MAX_SCORE_FUNCTIONAL

    QUESTIONS_PHYSICAL = strseq("p_q", 1, N_QUESTIONS_PHYSICAL)
    QUESTIONS_SOCIAL = strseq("s_q", 1, N_QUESTIONS_SOCIAL)
    QUESTIONS_EMOTIONAL = strseq("e_q", 1, N_QUESTIONS_EMOTIONAL)
    QUESTIONS_FUNCTIONAL = strseq("f_q", 1, N_QUESTIONS_FUNCTIONAL)

    ALL_QUESTIONS = [QUESTIONS_PHYSICAL, QUESTIONS_SOCIAL, QUESTIONS_EMOTIONAL, QUESTIONS_FUNCTIONAL]

    OPTIONAL_Q = "s_q7"

    ignore_q7 = CamcopsColumn("ignore_q7", Boolean, permitted_value_checker=BIT_CHECKER)

    # print("HERE")

    HTML = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                    {section_1}
                    {section_2}
                    {section_3}
                    {section_4}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th colspan="2" class="{CssClass.QA_TABLE_HEADING}">
                        Physical Well-being
                    </th>
                </tr>
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a_1}
                <tr>
                    <th colspan="2" class="{CssClass.QA_TABLE_HEADING}">
                        Social/Family Well-being
                    </th>
                </tr>
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a_2}
                <tr>
                    <th colspan="2" class="{CssClass.QA_TABLE_HEADING}">
                        Emotional Well-being
                    </th>
                </tr>
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a_3}
                <tr>
                    <th colspan="2" class="{CssClass.QA_TABLE_HEADING}">
                        Functional Well-being
                    </th>
                </tr>
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a_4}
            </table>
    """

    def is_complete(self) -> bool:

        ignore_q7 = getattr(self, "ignore_q7")
        questions_social = self.QUESTIONS_SOCIAL

        if ignore_q7 and self.OPTIONAL_Q in questions_social:
            questions_social.remove(self.OPTIONAL_Q)

        all_qs = [self.QUESTIONS_PHYSICAL, questions_social,
                  self.QUESTIONS_EMOTIONAL, self.QUESTIONS_FUNCTIONAL]

        for qlist in all_qs:
            if not self.are_all_fields_complete(qlist):
                return False
            if not self.field_contents_valid():
                return False

        return True

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        pass

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        pass

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        pass

    def subscore(self, fields, qnum) -> float:
        complete = self.n_complete(fields)
        if complete == 0:
            return 0
        result = self.sum_fields(fields) * qnum / complete

        return round(result, 2)

    def total_score(self) -> float:
        score_physical = self.subscore(self.QUESTIONS_PHYSICAL, self.N_QUESTIONS_PHYSICAL)
        score_social = self.subscore(self.QUESTIONS_SOCIAL, self.N_QUESTIONS_SOCIAL)
        score_emotional = self.subscore(self.QUESTIONS_EMOTIONAL, self.N_QUESTIONS_EMOTIONAL)
        score_functional = self.subscore(self.QUESTIONS_FUNCTIONAL, self.N_QUESTIONS_FUNCTIONAL)

        total = score_physical + score_social + score_emotional + score_functional

        return round(total, 2)

    def get_task_html(self, req: CamcopsRequest) -> str:

        answers = {
            None: None,
            0: "0 — " + self.wxstring(req, "a0"),
            1: "1 — " + self.wxstring(req, "a1"),
            2: "2 — " + self.wxstring(req, "a2"),
            3: "3 — " + self.wxstring(req, "a3"),
            4: "4 — " + self.wxstring(req, "a4"),
        }
        dlen = len(answers.keys())

        q_rows = []

        rev = True
        for q_group in self.ALL_QUESTIONS:
            q_row = ''
            for q in q_group:
                answer_val = getattr(self, q)
                if answer_val is not None and rev:
                    answer_val = str(dlen - int(answer_val) - 2)
                q_row += tr_qa(self.wxstring(req, q), get_from_dict(answers, answer_val))
            q_rows.append(q_row)

        score = answer(self.subscore(self.QUESTIONS_PHYSICAL, self.N_QUESTIONS_PHYSICAL))
        phys_score = score + " / {}".format(self.MAX_SCORE_PHYSICAL)

        score = answer(self.subscore(self.QUESTIONS_SOCIAL, self.N_QUESTIONS_SOCIAL))
        soc_score = score + " / {}".format(self.MAX_SCORE_SOCIAL)

        score = answer(self.subscore(self.QUESTIONS_EMOTIONAL, self.N_QUESTIONS_EMOTIONAL))
        emo_score = score + " / {}".format(self.MAX_SCORE_EMOTIONAL)

        score = answer(self.subscore(self.QUESTIONS_FUNCTIONAL, self.N_QUESTIONS_FUNCTIONAL))
        func_score = score + " / {}".format(self.MAX_SCORE_FUNCTIONAL)

        return self.HTML.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.wappstring("total_score"),
                answer(self.total_score()) +
                " / {}".format(self.MAX_SCORE_TOTAL)
            ),
            section_1=tr("Physical Well-being", phys_score),
            section_2=tr("Social/Family Well-being", soc_score),
            section_3=tr("Emotional", emo_score),
            section_4=tr("Functional", func_score),
            q_a_1=q_rows[0],
            q_a_2=q_rows[1],
            q_a_3=q_rows[2],
            q_a_4=q_rows[3],
        )
