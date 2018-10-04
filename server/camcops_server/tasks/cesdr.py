#!/usr/bin/env python
# camcops_server/tasks/cesdr.py

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
from sqlalchemy.sql.sqltypes import Boolean

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo, CTV_INCOMPLETE
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import (
    get_yes_no, tr, tr_qa
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
# CESD-R
# =============================================================================

class CesdrMetaclass(DeclarativeMeta):
    """
    There is a multilayer metaclass problem; see hads.py for discussion.
    """
    # noinspection PyInitNewSignature
    def __init__(cls: Type['cesdr'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.N_QUESTIONS,
            minimum=0, maximum=4,
            comment_fmt="Q{n} ({s}) (0 not at all - 4 extremely)",
            comment_strings=[
                "poor appetite",
                "unshakable blues",
                "lack of focus",
                "depressed",
                "sleep problems",
                "sad",
                "no enthusiasm",
                "depressed",
                "feelings of guilt",
                "loss of interest",
                "oversleeping",
                "lethargic",
                "fidgety",
                "severely depressed",
                "self - harm",
                "tiredness",
                "self - hatred",
                "weight loss",
                "sleep problems",
                "lack of focus"
            ]
        )
        super().__init__(name, bases, classdict)


class Cesdr(TaskHasPatientMixin, Task,
            metaclass=CesdrMetaclass):
    """
    Server implementation of the CESD task.
    """
    __tablename__ = 'cesdr'
    shortname = 'CESD-R'
    longname = 'CESD-R: Center for Epidemiologic Studies Depression Scale - Revised'
    provides_trackers = True
    extrastring_taskname = "cesdr"

    CAT_SUB = 0
    CAT_POSS_MAJOR = 1
    CAT_PROB_MAJOR = 2
    CAT_MAJOR = 3

    DEPRESSION_RISK_THRESHOLD = 16

    FREQ_NOT_AT_ALL = 0
    FREQ_1_2_DAYS = 1
    FREQ_3_4_DAYS = 2
    FREQ_5_7_DAYS = 3
    FREQ_DAILY = 4

    N_QUESTIONS = 20
    N_ANSWERS = 5

    POSS_MAJOR_THRESH = 2
    PROB_MAJOR_THRESH = 3
    MAJOR_THRESH = 4

    SCORED_FIELDS = strseq("q", 1, N_QUESTIONS)
    TASK_FIELDS = SCORED_FIELDS  # may be overridden
    TASK_TYPE = "?"  # will be overridden
    # ... not really used; we display the generic question forms on the server
    MIN_SCORE = 0
    MAX_SCORE = 3 * N_QUESTIONS

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(self.SCORED_FIELDS) - self.count_where(self.SCORED_FIELDS, [self.FREQ_DAILY])

    def get_depression_category(self) -> int:

        if not self.has_depression_risk():
            return self.CAT_SUB

        q_groups = {
            'dysphoria': [2, 4, 6],
            'anhedonia': [8, 10],
            'appetite': [1, 18],
            'sleep': [5, 11, 19],
            'thinking': [3, 20],
            'guilt': [9, 17],
            'tired': [7, 16],
            'movement': [12, 13],
            'suicidal': [14, 15]
        }

        if (not self.fufills_group_criteria(q_groups['dysphoria']) or
                not self.fufills_group_criteria(q_groups['anhedonia'])):
            return self.CAT_SUB

        count = 0

        for group, qnums in q_groups.items():
            if group == 'dysphoria' or group == 'anhedonia':
                continue
            if self.fufills_group_criteria(qnums):
                count += 1

        if count >= self.MAJOR_THRESH:
            return self.CAT_MAJOR
        if count >= self.PROB_MAJOR_THRESH:
            return self.CAT_PROB_MAJOR
        if count >= self.POSS_MAJOR_THRESH:
            return self.CAT_POSS_MAJOR

        return self.CAT_SUB

    def fufills_group_criteria(self, qnums: list) -> bool:
        qstrings = ["q" + str(qnum) for qnum in qnums]
        count = (self.count_where(qstrings, [self.FREQ_DAILY]) +
                self.count_where(qstrings, [self.FREQ_5_7_DAYS]))
        return count > 0

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        line_step = 20
        preliminary_cutoff = 16
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="CESD-R total score",
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
            content="CESD-R total score {}".format(self.total_score())
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="depression",
                coltype=Boolean(),
                value=self.has_depression_risk(),
                comment="Has depression or risk of."),
        ]

    def has_depression_risk(self) -> bool:
        return self.total_score() >= self.DEPRESSION_RISK_THRESHOLD

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        answer_dict = {None: None}
        for option in range(self.N_ANSWERS):
            answer_dict[option] = str(option) + " – " + \
                self.wxstring(req, "a" + str(option))
        q_a = ""
        for q in range(1, self.N_QUESTIONS):
            q_a += tr_qa(
                self.wxstring(req, "q" + str(q) + "_s"),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                    {depression_or_risk_of}
                    {provisional_diagnosis}
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
            [1] Presence of depression (or depression risk) is indicated by a score >= 16
            [2] Diagnostic criteria described https://cesd-r.com/cesdr/
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr_qa(
                "{} (0–60)".format(req.wappstring("total_score")),
                score
            ),
            depression_or_risk_of=tr_qa(
                self.wxstring(req, "depression_or_risk_of") + "? <sup>[1]</sup>",
                get_yes_no(req, self.has_depression_risk())
            ),
            provisional_diagnosis=tr('Provisional diagnosis <sup>[2]</sup>',
                                     self.wxstring(req, "category_" + str(self.get_depression_category()))),
            q_a=q_a,

        )
        return h
