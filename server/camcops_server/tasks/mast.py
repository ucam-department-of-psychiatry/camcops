#!/usr/bin/env python
# camcops_server/tasks/mast.py

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
from sqlalchemy.sql.sqltypes import Boolean, Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, get_yes_no, tr, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import CharColType
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import LabelAlignment, TrackerInfo, TrackerLabel  # noqa


# =============================================================================
# MAST
# =============================================================================

class MastMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Mast'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS, CharColType,
            pv=['Y', 'N'],
            comment_fmt="Q{n}: {s} (Y or N)",
            comment_strings=[
                "feel you are a normal drinker",
                "couldn't remember evening before",
                "relative worries/complains",
                "stop drinking after 1-2 drinks",
                "feel guilty",
                "friends/relatives think you are a normal drinker",
                "can stop drinking when you want",
                "attended Alcoholics Anonymous",
                "physical fights",
                "drinking caused problems with relatives",
                "family have sought help",
                "lost friends",
                "trouble at work/school",
                "lost job",
                "neglected obligations for >=2 days",
                "drink before noon often",
                "liver trouble",
                "delirium tremens",
                "sought help",
                "hospitalized",
                "psychiatry admission",
                "clinic visit or professional help",
                "arrested for drink-driving",
                "arrested for other drunk behaviour",
            ]
        )
        super().__init__(name, bases, classdict)


class Mast(TaskHasPatientMixin, Task,
           metaclass=MastMetaclass):
    __tablename__ = "mast"
    shortname = "MAST"
    longname = "Michigan Alcohol Screening Test"
    provides_trackers = True

    NQUESTIONS = 24
    TASK_FIELDS = strseq("q", 1, NQUESTIONS)
    MAX_SCORE = 53
    ROSS_THRESHOLD = 13

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="MAST total score",
            axis_label="Total score (out of {})".format(self.MAX_SCORE),
            axis_min=-0.5,
            axis_max=self.MAX_SCORE + 0.5,
            horizontal_lines=[self.ROSS_THRESHOLD - 0.5],
            horizontal_labels=[
                TrackerLabel(self.ROSS_THRESHOLD,
                             "Ross threshold", LabelAlignment.bottom)
            ]
        )]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="MAST total score {}/{}".format(self.total_score(),
                                                    self.MAX_SCORE)
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total",
                coltype=Integer(),
                value=self.total_score(),
                comment="Total score (/{})".format(self.MAX_SCORE)),
            SummaryElement(
                name="exceeds_threshold",
                coltype=Boolean(),
                value=self.exceeds_ross_threshold(),
                comment="Exceeds Ross threshold (total score >= {})".format(
                    self.ROSS_THRESHOLD)),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def get_score(self, q: int) -> int:
        yes = "Y"
        value = getattr(self, "q" + str(q))
        if value is None:
            return 0
        if q == 1 or q == 4 or q == 6 or q == 7:
            presence = 0 if value == yes else 1
        else:
            presence = 1 if value == yes else 0
        if q == 3 or q == 5 or q == 9 or q == 16:
            points = 1
        elif q == 8 or q == 19 or q == 20:
            points = 5
        else:
            points = 2
        return points * presence

    def total_score(self) -> int:
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            total += self.get_score(q)
        return total

    def exceeds_ross_threshold(self) -> bool:
        score = self.total_score()
        return score >= self.ROSS_THRESHOLD

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        exceeds_threshold = self.exceeds_ross_threshold()
        main_dict = {
            None: None,
            "Y": req.wappstring("yes"),
            "N": req.wappstring("no")
        }
        q_a = ""
        for q in range(1, self.NQUESTIONS + 1):
            q_a += tr(
                self.wxstring(req, "q" + str(q)),
                (
                    answer(get_from_dict(main_dict,
                                         getattr(self, "q" + str(q)))) +
                    answer(" — " + str(self.get_score(q)))
                )
            )
        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                    {exceeds_threshold}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
                {q_a}
            </table>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.wappstring("total_score"),
                answer(score) + " / {}".format(self.MAX_SCORE)
            ),
            exceeds_threshold=tr_qa(
                self.wxstring(req, "exceeds_threshold"),
                get_yes_no(req, exceeds_threshold)
            ),
            q_a=q_a,
        )
        return h
