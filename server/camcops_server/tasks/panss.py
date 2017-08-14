#!/usr/bin/env python
# camcops_server/tasks/panss.py

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

from ..cc_modules.cc_constants import DATA_COLLECTION_ONLY_DIV
from ..cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import tr_qa
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import get_from_dict, Task
from ..cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# PANSS
# =============================================================================

class Panss(Task):
    tablename = "panss"
    shortname = "PANSS"
    longname = "Positive and Negative Syndrome Scale"
    has_clinician = True
    provides_trackers = True

    P_FIELDSPECS = repeat_fieldspec(
        "p", 1, 7, min=1, max=7,
        comment_fmt="P{n}: {s} (1 absent - 7 extreme)",
        comment_strings=[
            "delusions", "conceptual disorganisation",
            "hallucinatory behaviour", "excitement",
            "grandiosity", "suspiciousness/persecution",
            "hostility",
        ])
    N_FIELDSPECS = repeat_fieldspec(
        "n", 1, 7, min=1, max=7,
        comment_fmt="N{n}: {s} (1 absent - 7 extreme)",
        comment_strings=[
            "blunted affect", "emotional withdrawal",
            "poor rapport", "passive/apathetic social withdrawal",
            "difficulty in abstract thinking",
            "lack of spontaneity/conversation flow",
            "stereotyped thinking",
        ])
    G_FIELDSPECS = repeat_fieldspec(
        "g", 1, 16, min=1, max=7,
        comment_fmt="G{n}: {s} (1 absent - 7 extreme)",
        comment_strings=[
            "somatic concern",
            "anxiety",
            "guilt feelings",
            "tension",
            "mannerisms/posturing",
            "depression",
            "motor retardation",
            "uncooperativeness",
            "unusual thought content",
            "disorientation",
            "poor attention",
            "lack of judgement/insight",
            "disturbance of volition",
            "poor impulse control",
            "preoccupation",
            "active social avoidance",
        ])

    fieldspecs = P_FIELDSPECS + N_FIELDSPECS + G_FIELDSPECS

    P_FIELDS = repeat_fieldname("p", 1, 7)
    N_FIELDS = repeat_fieldname("n", 1, 7)
    G_FIELDS = repeat_fieldname("g", 1, 16)
    TASK_FIELDS = P_FIELDS + N_FIELDS + G_FIELDS

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.total_score(),
                plot_label="PANSS total score",
                axis_label="Total score (30-210)",
                axis_min=-0.5,
                axis_max=210.5
            ),
            TrackerInfo(
                value=self.score_p(),
                plot_label="PANSS P score",
                axis_label="P score (7-49)",
                axis_min=6.5,
                axis_max=49.5
            ),
            TrackerInfo(
                value=self.score_n(),
                plot_label="PANSS N score",
                axis_label="N score (7-49)",
                axis_min=6.5,
                axis_max=49.5
            ),
            TrackerInfo(
                value=self.score_g(),
                plot_label="PANSS G score",
                axis_label="G score (16-112)",
                axis_min=15.5,
                axis_max=112.5
            ),
            TrackerInfo(
                value=self.composite(),
                plot_label="PANSS composite score",
                axis_label="P - N"
            ),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content=(
                "PANSS total score {} (P {}, N {}, G {}, "
                "composite P–N {})".format(
                    self.total_score(),
                    self.score_p(),
                    self.score_n(),
                    self.score_g(),
                    self.composite()
                )
            )
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(name="total",
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score (30-210)"),
            SummaryElement(name="p",
                           coltype=Integer(),
                           value=self.score_p(),
                           comment="Positive symptom (P) score (7-49)"),
            SummaryElement(name="n",
                           coltype=Integer(),
                           value=self.score_n(),
                           comment="Negative symptom (N) score (7-49)"),
            SummaryElement(name="g",
                           coltype=Integer(),
                           value=self.score_g(),
                           comment="General symptom (G) score (16-112)"),
            SummaryElement(name="composite",
                           coltype=Integer(),
                           value=self.composite(),
                           comment="Composite score (P - N)"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def score_p(self) -> int:
        return self.sum_fields(self.P_FIELDS)

    def score_n(self) -> int:
        return self.sum_fields(self.N_FIELDS)

    def score_g(self) -> int:
        return self.sum_fields(self.G_FIELDS)

    def composite(self) -> int:
        return self.score_p() - self.score_n()

    def get_task_html(self, req: CamcopsRequest) -> str:
        p = self.score_p()
        n = self.score_n()
        g = self.score_g()
        composite = self.composite()
        total = p + n + g
        answers = {
            None: None,
            1: self.wxstring(req, "option1"),
            2: self.wxstring(req, "option2"),
            3: self.wxstring(req, "option3"),
            4: self.wxstring(req, "option4"),
            5: self.wxstring(req, "option5"),
            6: self.wxstring(req, "option6"),
            7: self.wxstring(req, "option7"),
        }
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr_qa("{} (30–210)".format(req.wappstring("total_score")), total)
        h += tr_qa("{} (7–49)".format(self.wxstring(req, "p")), p)
        h += tr_qa("{} (7–49)".format(self.wxstring(req, "n")), n)
        h += tr_qa("{} (16–112)".format(self.wxstring(req, "g")), g)
        h += tr_qa(self.wxstring(req, "composite"), composite)
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="40%">Question</th>
                    <th width="60%">Answer</th>
                </tr>
        """
        for q in self.TASK_FIELDS:
            h += tr_qa(
                self.wxstring(req, "" + q + "_s"),
                get_from_dict(answers, getattr(self, q))
            )
        h += """
            </table>
        """ + DATA_COLLECTION_ONLY_DIV
        return h
