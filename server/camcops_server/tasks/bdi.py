#!/usr/bin/env python
# camcops_server/tasks/bdi.py

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
import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, String

from camcops_server.cc_modules.cc_constants import DATA_COLLECTION_ONLY_DIV
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, tr, tr_qa
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# BDI (crippled)
# =============================================================================

class BdiMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Bdi'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS,
            minimum=0, maximum=3,
            comment_fmt="Q{n} [in BDI-II: {s}] (0-3, higher worse)",
            comment_strings=["sadness", "pessimism", "past failure",
                             "loss of pleasure", "guilt", "punishment",
                             "self-dislike", "self-criticality", "suicidality",
                             "crying", "agitation", "loss of interest",
                             "indecisive", "worthless", "energy", "sleep",
                             "irritability", "appetite", "concentration",
                             "fatigue", "libido"]
        )
        super().__init__(name, bases, classdict)


class Bdi(TaskHasPatientMixin, Task,
          metaclass=BdiMetaclass):
    __tablename__ = "bdi"
    shortname = "BDI"
    longname = "Beck Depression Inventory (data collection only)"
    provides_trackers = True

    NQUESTIONS = 21
    TASK_SCORED_FIELDS = strseq("q", 1, NQUESTIONS)
    MAX_SCORE = NQUESTIONS * 3

    bdi_scale = Column(
        "bdi_scale", String(length=10),  # was Text
        comment="Which BDI scale (BDI-I, BDI-IA, BDI-II)?"
    )

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid() and
            self.bdi_scale is not None and
            self.are_all_fields_complete(self.TASK_SCORED_FIELDS)
        )

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="BDI total score (rating depressive symptoms)",
            axis_label="Score for Q1-21 (out of {})".format(self.MAX_SCORE),
            axis_min=-0.5,
            axis_max=self.MAX_SCORE + 0.5
        )]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="{} total score {}/{}".format(
                ws.webify(self.bdi_scale), self.total_score(), self.MAX_SCORE)
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(name="total",
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score (/{})".format(self.MAX_SCORE)),
        ]

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_SCORED_FIELDS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr(req)
        h += tr(req.wappstring("total_score"),
                answer(score) + " / {}".format(self.MAX_SCORE))
        h += """
                </table>
            </div>
            <div class="explanation">
                All questions are scored from 0–3
                (0 free of symptoms, 3 most symptomatic).
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """
        h += tr_qa(req.wappstring("bdi_which_scale"), ws.webify(self.bdi_scale))

        for q in range(1, self.NQUESTIONS + 1):
            h += tr_qa("{} {}".format(req.wappstring("question"), q),
                       getattr(self, "q" + str(q)))
        h += """
            </table>
        """ + DATA_COLLECTION_ONLY_DIV
        return h
