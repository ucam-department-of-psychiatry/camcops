#!/usr/bin/env python
# camcops_server/tasks/iesr.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

from typing import List

from sqlalchemy.sql.sqltypes import Integer

from ..cc_modules.cc_constants import DATA_COLLECTION_UNLESS_UPGRADED_DIV
from ..cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, tr, tr_qa
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import get_from_dict, Task
from ..cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# IES-R
# =============================================================================

class Iesr(Task):
    tablename = "iesr"
    shortname = "IES-R"
    longname = "Impact of Events Scale – Revised"
    provides_trackers = True

    MIN_SCORE = 0
    MAX_SCORE = 4
    QUESTION_SNIPPETS = [
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
    NQUESTIONS = 22
    QUESTION_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        min=MIN_SCORE, max=MAX_SCORE,
        comment_strings=QUESTION_SNIPPETS
    )

    fieldspecs = [
        dict(name="event", cctype="TEXT",
             comment="Relevant event"),
    ] + QUESTION_FIELDSPECS

    TASK_FIELDS = [x["name"] for x in fieldspecs]
    QUESTION_FIELDS = [x["name"] for x in QUESTION_FIELDSPECS]
    EXTRASTRING_TASKNAME = "iesr"
    AVOIDANCE_QUESTIONS = [5, 7, 8, 11, 12, 13, 17, 22]
    INTRUSION_QUESTIONS = [1, 2, 3, 6, 9, 16, 20]
    HYPERAROUSAL_QUESTIONS = [4, 10, 14, 15, 18, 19, 21]

    def get_trackers(self) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.total_score(),
                plot_label="IES-R total score (lower is better)",
                axis_label="Total score (out of 88)",
                axis_min=-0.5,
                axis_max=88.5
            ),
            TrackerInfo(
                value=self.avoidance_score(),
                plot_label="IES-R avoidance score",
                axis_label="Avoidance score (out of 32)",
                axis_min=-0.5,
                axis_max=32.5
            ),
            TrackerInfo(
                value=self.intrusion_score(),
                plot_label="IES-R intrusion score",
                axis_label="Intrusion score (out of 28)",
                axis_min=-0.5,
                axis_max=28.5
            ),
            TrackerInfo(
                value=self.hyperarousal_score(),
                plot_label="IES-R hyperarousal score",
                axis_label="Hyperarousal score (out of 28)",
                axis_min=-0.5,
                axis_max=28.5
            ),
        ]

    def get_summaries(self) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(name="total_score",
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score (/ 88)"),
            SummaryElement(name="avoidance_score",
                           coltype=Integer(),
                           value=self.avoidance_score(),
                           comment="Avoidance score (/ 32)"),
            SummaryElement(name="intrusion_score",
                           coltype=Integer(),
                           value=self.intrusion_score(),
                           comment="Intrusion score (/ 28)"),
            SummaryElement(name="hyperarousal_score",
                           coltype=Integer(),
                           value=self.hyperarousal_score(),
                           comment="Hyperarousal score (/ 28)"),
        ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        t = self.total_score()
        a = self.avoidance_score()
        i = self.intrusion_score()
        h = self.hyperarousal_score()
        return [CtvInfo(
            content=(
                "IES-R total score {t}/48 (avoidance {a}/32 "
                "intrusion {i}/28, hyperarousal {h}/28)".format(
                    t=t, a=a, i=i, h=h
                )
            )
        )]

    def total_score(self) -> int:
        return self.sum_fields(self.QUESTION_FIELDS)

    def avoidance_score(self) -> int:
        return self.sum_fields(
            self.fieldnames_from_list("q", self.AVOIDANCE_QUESTIONS))

    def intrusion_score(self) -> int:
        return self.sum_fields(
            self.fieldnames_from_list("q", self.INTRUSION_QUESTIONS))

    def hyperarousal_score(self) -> int:
        return self.sum_fields(
            self.fieldnames_from_list("q", self.HYPERAROUSAL_QUESTIONS))

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid() and
            self.event and
            self.are_all_fields_complete(self.QUESTION_FIELDS)
        )

    def get_task_html(self) -> str:
        option_dict = {None: None}
        for a in range(self.MIN_SCORE, self.MAX_SCORE + 1):
            option_dict[a] = wappstring("iesr_a" + str(a))
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score</td>
                        <td>{total} / 88</td>
                    </td>
                    <tr>
                        <td>Avoidance score</td>
                        <td>{avoidance} / 32</td>
                    </td>
                    <tr>
                        <td>Intrusion score</td>
                        <td>{intrusion} / 28</td>
                    </td>
                    <tr>
                        <td>Hyperarousal score</td>
                        <td>{hyperarousal} / 28</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                {tr_event}
            </table>
            <table class="taskdetail">
                <tr>
                    <th width="75%">Question</th>
                    <th width="25%">Answer (0–4)</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(self.total_score()),
            avoidance=answer(self.avoidance_score()),
            intrusion=answer(self.intrusion_score()),
            hyperarousal=answer(self.hyperarousal_score()),
            tr_event=tr_qa(wappstring("event"), self.event),
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            fa = ("{}: {}".format(a, get_from_dict(option_dict, a))
                  if a is not None else None)
            h += tr(self.wxstring("q" + str(q)), answer(fa))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
