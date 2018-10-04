#!/usr/bin/env python
# camcops_server/tasks/core10.py

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
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo, CTV_INCOMPLETE
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import (
    answer, get_yes_no, subheading_spanning_two_columns, tr, tr_qa
)
from camcops_server.cc_modules.cc_request import CamcopsRequest

from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import (
    equally_spaced_int,
    regular_tracker_axis_ticks_int,
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# CESD
# =============================================================================

class CesdMetaclass(DeclarativeMeta):
    """
    There is a multilayer metaclass problem; see hads.py for discussion.
    """
    # noinspection PyInitNewSignature
    def __init__(cls: Type['cesd'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.N_QUESTIONS,
            minimum=0, maximum=4,
            comment_fmt=(
                "Q{n} ({s}) (0 rarely/none of the time - 4 all of the time)"
            ),
            comment_strings=[
                "sensitivity/irritability",
                "poor appetite",
                "unshakeable blues",
                "low self-esteem",
                "focus",
                "depressed",
                "low energy",
                "lack of optimism",
                "feelings of failure",
                "fearful",
                "sleep problems",
                "happy",
                "uncommunicative",
                "lonely",
                "perceived hostility",
                "enjoyment",
                "crying spells",
                "sadness",
                "feeling disliked",
                "lack of enthusiasm"

            ]
        )
        super().__init__(name, bases, classdict)


class Cesd(TaskHasPatientMixin, Task,
           metaclass=CesdMetaclass):
    """
    Server implementation of the PCL-5 task.
    """
    __tablename__ = 'cesd'
    shortname = 'CESD'
    longname = 'Center for Epidemiologic Studies Depression Scale'
    provides_trackers = True
    extrastring_taskname = "cesd"
    N_QUESTIONS = 20
    SCORED_FIELDS = strseq("q", 1, N_QUESTIONS)
    TASK_FIELDS = SCORED_FIELDS  # may be overridden
    TASK_TYPE = "?"  # will be overridden
    # ... not really used; we display the generic question forms on the server
    MIN_SCORE = 0
    MAX_SCORE = 4 * N_QUESTIONS

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(self.SCORED_FIELDS)

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        line_step = 20
        preliminary_cutoff = 16
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="CESD total score",
            axis_label="Total score ({}-{})".format(self.MIN_SCORE,
                                                    self.MAX_SCORE),
            axis_min=self.MIN_SCORE - 0.5,
            axis_max=self.MAX_SCORE + 0.5,
            axis_ticks=regular_tracker_axis_ticks_int(
                self.MIN_SCORE,
                self.MAX_SCORE,
                step=line_step
            ),
            horizontal_lines=equally_spaced_int(
                self.MIN_SCORE + line_step,
                self.MAX_SCORE - line_step,
                step=line_step
            ) + [preliminary_cutoff],
            horizontal_labels=[
                TrackerLabel(preliminary_cutoff,
                             self.wxstring(req, "preliminary_cutoff")),
            ]
        )]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="CESD total score {}".format(self.total_score())
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="depression",
                coltype=Boolean(),
                value=self.hasDepressionRisk(),
                comment="Has depression or risk of."),
        ]

    def hasDepressionRisk(self) -> bool:
        true

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        hasDepressionRisk = self.hasDepressionRisk()
        answer_dict = {None: None}
        for option in range(5):
            answer_dict[option] = str(option) + " – " + \
                self.wxstring(req, "a" + str(option))
        q_a = ""

        section_start = {
            1: 'B (intrusion symptoms)',
            6: 'C (avoidance)',
            8: 'D (negative cognition/mood)',
            15: 'E (arousal/reactivity)'
        }

        for q in range(1, self.N_QUESTIONS + 1):
            if q in section_start:
                section = section_start[q]
                q_a += subheading_spanning_two_columns(
                    "DSM-5 section {}".format(section)
                )

            q_a += tr_qa(
                self.wxstring(req, "q" + str(q) + "_s"),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {dsm_criteria_met}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Questions with scores ≥2 are considered symptomatic.
                [2] ≥1 ‘B’ symptoms and ≥1 ‘C’ symptoms and ≥2 'D' symptoms
                    and ≥2 ‘E’ symptoms.
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            dsm_criteria_met=tr_qa(
                self.wxstring(req, "dsm_criteria_met") + " <sup>[2]</sup>",
                get_yes_no(req, hasDepressionRisk)
            ),
            q_a=q_a,
        )
        return h
