#!/usr/bin/env python
# panss.py

"""
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
"""

from typing import List

from ..cc_modules.cc_constants import DATA_COLLECTION_ONLY_DIV
from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import tr_qa
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# PANSS
# =============================================================================

class Panss(Task):
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

    tablename = "panss"
    shortname = "PANSS"
    longname = "Positive and Negative Syndrome Scale"
    fieldspecs = P_FIELDSPECS + N_FIELDSPECS + G_FIELDSPECS
    has_clinician = True

    P_FIELDS = repeat_fieldname("p", 1, 7)
    N_FIELDS = repeat_fieldname("n", 1, 7)
    G_FIELDS = repeat_fieldname("g", 1, 16)
    TASK_FIELDS = P_FIELDS + N_FIELDS + G_FIELDS

    def get_trackers(self) -> List[TrackerInfo]:
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

    def get_clinical_text(self) -> List[CtvInfo]:
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

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (30-210)"),
            dict(name="p", cctype="INT", value=self.score_p(),
                 comment="Positive symptom (P) score (7-49)"),
            dict(name="n", cctype="INT", value=self.score_n(),
                 comment="Negative symptom (N) score (7-49)"),
            dict(name="g", cctype="INT", value=self.score_g(),
                 comment="General symptom (G) score (16-112)"),
            dict(name="composite", cctype="INT",
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

    def get_task_html(self) -> str:
        p = self.score_p()
        n = self.score_n()
        g = self.score_g()
        composite = self.composite()
        total = p + n + g
        answers = {
            None: None,
            1: WSTRING("panss_option1"),
            2: WSTRING("panss_option2"),
            3: WSTRING("panss_option3"),
            4: WSTRING("panss_option4"),
            5: WSTRING("panss_option5"),
            6: WSTRING("panss_option6"),
            7: WSTRING("panss_option7"),
        }
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr_qa("{} (30–210)".format(WSTRING("total_score")), total)
        h += tr_qa("{} (7–49)".format(WSTRING("panss_p")), p)
        h += tr_qa("{} (7–49)".format(WSTRING("panss_n")), n)
        h += tr_qa("{} (16–112)".format(WSTRING("panss_g")), g)
        h += tr_qa(WSTRING("panss_composite"), composite)
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
                WSTRING("panss_" + q + "_s"),
                get_from_dict(answers, getattr(self, q))
            )
        h += """
            </table>
        """ + DATA_COLLECTION_ONLY_DIV
        return h
