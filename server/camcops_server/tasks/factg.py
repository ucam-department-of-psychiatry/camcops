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

from typing import Any, Dict, List, Tuple, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Boolean, Float

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import (
    answer,
    tr_qa,
    subheading_spanning_two_columns,
    tr
)
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
    TrackerAxisTick,
    TrackerInfo,
)


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

    N_ALL = (
        N_QUESTIONS_PHYSICAL + N_QUESTIONS_SOCIAL +
        N_QUESTIONS_EMOTIONAL + N_QUESTIONS_FUNCTIONAL
    )

    MAX_QSCORE = 4

    MAX_SCORE_TOTAL = N_ALL * MAX_QSCORE

    PHYSICAL_PREFIX = "p_q"
    SOCIAL_PREFIX = "s_q"
    EMOTIONAL_PREFIX = "e_q"
    FUNCTIONAL_PREFIX = "f_q"

    QUESTIONS_PHYSICAL = strseq(PHYSICAL_PREFIX, 1, N_QUESTIONS_PHYSICAL)
    QUESTIONS_SOCIAL = strseq(SOCIAL_PREFIX, 1, N_QUESTIONS_SOCIAL)
    QUESTIONS_EMOTIONAL = strseq(EMOTIONAL_PREFIX, 1, N_QUESTIONS_EMOTIONAL)
    QUESTIONS_FUNCTIONAL = strseq(FUNCTIONAL_PREFIX, 1, N_QUESTIONS_FUNCTIONAL)

    GROUPS = [
        # xstring name, subgroup question prefix, list of question fieldnames, summary fieldname
        ("h1", PHYSICAL_PREFIX, QUESTIONS_PHYSICAL, "physical_wellbeing"),
        ("h2", SOCIAL_PREFIX, QUESTIONS_SOCIAL, "social_family_wellbeing"),
        ("h3", EMOTIONAL_PREFIX, QUESTIONS_EMOTIONAL, "emotional_wellbeing"),
        ("h4", FUNCTIONAL_PREFIX, QUESTIONS_FUNCTIONAL, "functional_wellbeing"),
    ]

    OPTIONAL_Q = "s_q7"

    # Index into a list of fields in the emotional group. Question 2 (index 1)
    # is NOT reversed scored, as opposed to the rest of the qroup
    EMO_NORMAL_Q_IDX = 1

    ignore_s_q7 = CamcopsColumn("ignore_s_q7", Boolean,
                                permitted_value_checker=BIT_CHECKER)

    total = None

    def is_complete(self) -> bool:
        questions_social = self.QUESTIONS_SOCIAL

        if self.ignore_s_q7 and self.OPTIONAL_Q in questions_social:
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
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="FACT-G total score (rating well-being)",
            axis_label="Total score".format(
                self.MAX_SCORE_TOTAL),
            axis_min=-0.5,
            axis_max=self.MAX_SCORE_TOTAL + 0.5,
            axis_ticks=[
                TrackerAxisTick(108, "108"),
                TrackerAxisTick(100, "100"),
                TrackerAxisTick(80, "80"),
                TrackerAxisTick(60, "60"),
                TrackerAxisTick(40, "40"),
                TrackerAxisTick(20, "20"),
                TrackerAxisTick(0, "0"),
            ],
            horizontal_lines=[
                80,
                60,
                40,
                20
            ],
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        elements = self.standard_task_summary_fields()
        for description, prefix, questions, fieldname in self.GROUPS:
            nquestions = len(questions)
            score = self.subscore(questions, nquestions, prefix)
            elements.append(SummaryElement(
                name=fieldname, coltype=Float(),
                value=score,
                comment="{} ({} / {})".format(description, score, nquestions)
            ))
        elements.append(SummaryElement(
            name="total_score", coltype=Float(),
            value=self.total_score()
        ))
        return elements

    def subscore(self, fields, qnum, prefix) -> float:
        answered = self.n_complete(fields)
        if answered == 0:
            return 0

        if prefix == self.PHYSICAL_PREFIX or prefix == self.EMOTIONAL_PREFIX:
            result = self.MAX_QSCORE * qnum - self.sum_fields(fields)
        else:
            result = self.sum_fields(fields)

        if prefix == self.EMOTIONAL_PREFIX:
            value = getattr(self, fields[self.EMO_NORMAL_Q_IDX])
            result -= self.MAX_QSCORE
            result += value * 2

        result = result * qnum / answered

        return round(result, 2)

    def subscores(self) -> List[float]:
        sscores = []
        for _, qprefix, questions, _ in self.GROUPS:
            sscores.append(self.subscore(questions, len(questions), qprefix))
        return sscores

    def total_score(self) -> float:
        return round(sum(self.subscores()), 2)

    def get_task_html(self, req: CamcopsRequest) -> str:
        answers = {
            None: None,
            0: "0 — " + self.wxstring(req, "a0"),
            1: "1 — " + self.wxstring(req, "a1"),
            2: "2 — " + self.wxstring(req, "a2"),
            3: "3 — " + self.wxstring(req, "a3"),
            4: "4 — " + self.wxstring(req, "a4"),
        }

        subheadings = [items[0] for items in self.GROUPS]
        subscores = self.subscores()
        tscore = round(self.total_score(), 2)

        h = """
            <div class="{CssClass.SUMMARY}">
                 <table class="{CssClass.SUMMARY}">
                     {tr_is_complete}
                     {total_score}
                     {s1}
                     {s2}
                     {s3}
                     {s4}
                 </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.wappstring("total_score"),
                answer(tscore) + " / {}".format(self.MAX_SCORE_TOTAL)
            ),
            s1=tr(subheadings[0], answer(subscores[0])
                  + " / {}".format(self.MAX_SCORE_PHYSICAL)),
            s2=tr(subheadings[1], answer(subscores[1])
                  + " / {}".format(self.MAX_SCORE_SOCIAL)),
            s3=tr(subheadings[2], answer(subscores[2])
                  + " / {}".format(self.MAX_SCORE_EMOTIONAL)),
            s4=tr(subheadings[3], answer(subscores[3])
                  + " / {}".format(self.MAX_SCORE_FUNCTIONAL)),
        )

        dlen = len(answers.keys())

        for xstringname, _, questions, _ in self.GROUPS:
            h += subheading_spanning_two_columns(
                self.wxstring(req, xstringname))
            for q in questions:
                answer_val = getattr(self, q)
                h += tr_qa(self.wxstring(req, q),
                           get_from_dict(answers, answer_val))
        h += """
            </table>
        """
        return h
