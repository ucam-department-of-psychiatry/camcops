#!/usr/bin/env python
# camcops_server/tasks_discarded/epds.py

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
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import get_yes_no
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import (
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# EPDS
# =============================================================================

class EpdsMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Epds'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(cls, "q", 1, cls.NQUESTIONS)
        super().__init__(name, bases, classdict)


class Epds(TaskHasPatientMixin, Task,
           metaclass=EpdsMetaclass):
    __tablename__ = "epds"
    shortname = "EPDS"
    longname = "Edinburgh Postnatal Depression Scale"
    provides_trackers = True

    NQUESTIONS = 10
    TASK_FIELDS = strseq("q", 1, NQUESTIONS)
    MAX_TOTAL = 30

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="EPDS total score (rating depressive symptoms)",
            axis_label="Total score (out of {})".format(self.MAX_TOTAL),
            axis_min=-0.5,
            axis_max=self.MAX_TOTAL + 0.5,
            horizontal_lines=[
                12.5,
                9.5,
            ],
            horizontal_labels=[
                TrackerLabel(13, "likely depression"),
                TrackerLabel(10, "possible depression"),
            ]
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total", coltype=Integer(),
                value=self.total_score(),
                comment="Total score (out of {})".format(self.MAX_TOTAL)
            ),
        ]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        above_cutoff_1 = score >= 10
        above_cutoff_2 = score >= 13
        answer_dicts = []
        for q in range(1, self.NQUESTIONS + 1):
            d = {None: "?"}
            for option in range(0, 4):
                d[option] = (
                    str(option) + " — " +
                    self.wxstring(req, "q" + str(q) + "_option" + str(option)))
            answer_dicts.append(d)

        q_a = ""
        for q in range(1, self.NQUESTIONS + 1):
            q_a += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                self.wxstring(req, "q" + str(q) + "_question"),
                get_from_dict(answer_dicts[q - 1], getattr(self, "q" + str(q)))
            )

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {is_complete}
                    <tr>
                        <td>{total_score_str}</td>
                        <td><b>{score}</b> / {max_total}</td>
                    </tr>
                    <tr>
                        <td>{ac1str} <sup>[1]</sup></td>
                        <td><b>{above_cutoff_1}</b></td>
                    </tr>
                    <tr>
                        <td>{ac2str} <sup>[2]</sup></td>
                        <td><b>{above_cutoff_2}</b></td>
                    </tr>
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                Ratings are over the last week.
                <b>{suicide}</b>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] &ge;10.
                [2] &ge;13.
                (Cox et al. 1987, PubMed ID 3651732.)
            </div>
        """.format(
            CssClass=CssClass,
            is_complete=self.get_is_complete_tr(req),
            total_score_str=req.wappstring("total_score"),
            score=score,
            max_total=self.MAX_TOTAL,
            ac1str=self.wxstring(req, "above_cutoff_1"),
            above_cutoff_1=get_yes_no(req, above_cutoff_1),
            ac2str=self.wxstring(req, "above_cutoff_2"),
            above_cutoff_2=get_yes_no(req, above_cutoff_2),
            suicide=self.wxstring(req, "always_look_at_suicide"),
            q_a=q_a,
        )
        return h
