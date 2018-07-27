#!/usr/bin/env python
# camcops_server/tasks/iesr.py

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
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import (
    CssClass,
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
)
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, tr, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# IES-R
# =============================================================================

class IesrMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Iesr'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS,
            minimum=cls.MIN_SCORE, maximum=cls.MAX_SCORE,
            comment_fmt="Q{n}, {s} (0-4, higher worse)",
            comment_strings=[
                "reminder feelings",  # 1
                "sleep maintenance",
                "reminder thinking",
                "irritable",
                "avoided getting upset",  # 5
                "thought unwanted",
                "unreal",
                "avoided reminder",
                "mental pictures",
                "jumpy",  # 10
                "avoided thinking",
                "feelings undealt",
                "numb",
                "as if then",
                "sleep initiation",  # 15
                "waves of emotion",
                "tried forgetting",
                "concentration",
                "reminder physical",
                "dreams",  # 20
                "vigilant",
                "avoided talking",
            ]
        )
        super().__init__(name, bases, classdict)


class Iesr(TaskHasPatientMixin, Task,
           metaclass=IesrMetaclass):
    __tablename__ = "iesr"
    shortname = "IES-R"
    longname = "Impact of Events Scale – Revised"
    provides_trackers = True

    event = Column("event", UnicodeText, comment="Relevant event")

    NQUESTIONS = 22
    MIN_SCORE = 0  # per question
    MAX_SCORE = 4  # per question

    MAX_TOTAL = 88
    MAX_AVOIDANCE = 32
    MAX_INTRUSION = 28
    MAX_HYPERAROUSAL = 28

    QUESTION_FIELDS = strseq("q", 1, NQUESTIONS)
    AVOIDANCE_QUESTIONS = [5, 7, 8, 11, 12, 13, 17, 22]
    AVOIDANCE_FIELDS = Task.fieldnames_from_list("q", AVOIDANCE_QUESTIONS)
    INTRUSION_QUESTIONS = [1, 2, 3, 6, 9, 16, 20]
    INTRUSION_FIELDS = Task.fieldnames_from_list("q", INTRUSION_QUESTIONS)
    HYPERAROUSAL_QUESTIONS = [4, 10, 14, 15, 18, 19, 21]
    HYPERAROUSAL_FIELDS = Task.fieldnames_from_list(
        "q", HYPERAROUSAL_QUESTIONS)

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.total_score(),
                plot_label="IES-R total score (lower is better)",
                axis_label="Total score (out of {})".format(self.MAX_TOTAL),
                axis_min=-0.5,
                axis_max=self.MAX_TOTAL + 0.5
            ),
            TrackerInfo(
                value=self.avoidance_score(),
                plot_label="IES-R avoidance score",
                axis_label="Avoidance score (out of {})".format(
                    self.MAX_AVOIDANCE),
                axis_min=-0.5,
                axis_max=self.MAX_AVOIDANCE + 0.5
            ),
            TrackerInfo(
                value=self.intrusion_score(),
                plot_label="IES-R intrusion score",
                axis_label="Intrusion score (out of {})".format(
                    self.MAX_INTRUSION),
                axis_min=-0.5,
                axis_max=self.MAX_INTRUSION + 0.5
            ),
            TrackerInfo(
                value=self.hyperarousal_score(),
                plot_label="IES-R hyperarousal score",
                axis_label="Hyperarousal score (out of {})".format(
                    self.MAX_HYPERAROUSAL),
                axis_min=-0.5,
                axis_max=self.MAX_HYPERAROUSAL + 0.5
            ),
        ]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total_score",
                coltype=Integer(),
                value=self.total_score(),
                comment="Total score (/ {})".format(self.MAX_TOTAL)),
            SummaryElement(
                name="avoidance_score",
                coltype=Integer(),
                value=self.avoidance_score(),
                comment="Avoidance score (/ {})".format(self.MAX_AVOIDANCE)),
            SummaryElement(
                name="intrusion_score",
                coltype=Integer(),
                value=self.intrusion_score(),
                comment="Intrusion score (/ {})".format(self.MAX_INTRUSION)),
            SummaryElement(
                name="hyperarousal_score",
                coltype=Integer(),
                value=self.hyperarousal_score(),
                comment="Hyperarousal score (/ {})".format(
                    self.MAX_HYPERAROUSAL)),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        t = self.total_score()
        a = self.avoidance_score()
        i = self.intrusion_score()
        h = self.hyperarousal_score()
        return [CtvInfo(
            content=(
                "IES-R total score {t}/{tmax} (avoidance {a}/{amax} "
                "intrusion {i}/{imax}, hyperarousal {h}/{hmax})".format(
                    t=t, a=a, i=i, h=h,
                    tmax=self.MAX_TOTAL,
                    amax=self.MAX_AVOIDANCE,
                    imax=self.MAX_INTRUSION,
                    hmax=self.MAX_HYPERAROUSAL,
                )
            )
        )]

    def total_score(self) -> int:
        return self.sum_fields(self.QUESTION_FIELDS)

    def avoidance_score(self) -> int:
        return self.sum_fields(self.AVOIDANCE_FIELDS)

    def intrusion_score(self) -> int:
        return self.sum_fields(self.INTRUSION_FIELDS)

    def hyperarousal_score(self) -> int:
        return self.sum_fields(self.HYPERAROUSAL_FIELDS)

    def is_complete(self) -> bool:
        return bool(
            self.field_contents_valid() and
            self.event and
            self.are_all_fields_complete(self.QUESTION_FIELDS)
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        option_dict = {None: None}
        for a in range(self.MIN_SCORE, self.MAX_SCORE + 1):
            option_dict[a] = req.wappstring("iesr_a" + str(a))
        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {complete_tr}
                    <tr>
                        <td>Total score</td>
                        <td>{total} / {maxtotal}</td>
                    </td>
                    <tr>
                        <td>Avoidance score</td>
                        <td>{avoidance} / {maxavoidance}</td>
                    </td>
                    <tr>
                        <td>Intrusion score</td>
                        <td>{intrusion} / {maxintrusion}</td>
                    </td>
                    <tr>
                        <td>Hyperarousal score</td>
                        <td>{hyperarousal} / {maxhyperarousal}</td>
                    </td>
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                {tr_event}
            </table>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="75%">Question</th>
                    <th width="25%">Answer (0–4)</th>
                </tr>
        """.format(
            CssClass=CssClass,
            complete_tr=self.get_is_complete_tr(req),
            total=answer(self.total_score()),
            maxtotal=self.MAX_TOTAL,
            avoidance=answer(self.avoidance_score()),
            maxavoidance=self.MAX_AVOIDANCE,
            intrusion=answer(self.intrusion_score()),
            maxintrusion=self.MAX_INTRUSION,
            hyperarousal=answer(self.hyperarousal_score()),
            maxhyperarousal=self.MAX_HYPERAROUSAL,
            tr_event=tr_qa(req.wappstring("event"), self.event),
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            fa = ("{}: {}".format(a, get_from_dict(option_dict, a))
                  if a is not None else None)
            h += tr(self.wxstring(req, "q" + str(q)), answer(fa))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
