#!/usr/bin/env python3
# panss.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from cc_modules.cc_constants import (
    CLINICIAN_FIELDSPECS,
    CTV_DICTLIST_INCOMPLETE,
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
    STANDARD_TASK_FIELDSPECS,
)
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


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
    TASK_FIELDSPECS = P_FIELDSPECS + N_FIELDSPECS + G_FIELDSPECS
    P_FIELDS = repeat_fieldname("p", 1, 7)
    N_FIELDS = repeat_fieldname("n", 1, 7)
    G_FIELDS = repeat_fieldname("g", 1, 16)
    TASK_FIELDS = P_FIELDS + N_FIELDS + G_FIELDS

    @classmethod
    def get_tablename(cls):
        return "panss"

    @classmethod
    def get_taskshortname(cls):
        return "PANSS"

    @classmethod
    def get_tasklongname(cls):
        return "Positive and Negative Syndrome Scale"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + \
            Panss.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "PANSS total score",
                "axis_label": "Total score (30-210)",
                "axis_min": -0.5,
                "axis_max": 210.5,
            },
            {
                "value": self.score_p(),
                "plot_label": "PANSS P score",
                "axis_label": "P score (7-49)",
                "axis_min": 6.5,
                "axis_max": 49.5,
            },
            {
                "value": self.score_n(),
                "plot_label": "PANSS N score",
                "axis_label": "N score (7-49)",
                "axis_min": 6.5,
                "axis_max": 49.5,
            },
            {
                "value": self.score_g(),
                "plot_label": "PANSS G score",
                "axis_label": "G score (16-112)",
                "axis_min": 15.5,
                "axis_max": 112.5,
            },
            {
                "value": self.composite(),
                "plot_label": "PANSS composite score",
                "axis_label": "P - N",
            },
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content":  "PANSS total score {} (P {}, N {}, G {}, "
                        "composite P–N {})".format(
                            self.total_score(),
                            self.score_p(),
                            self.score_n(),
                            self.score_g(),
                            self.composite()
                        )
        }]

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

    def is_complete(self):
        return (
            self.are_all_fields_complete(Panss.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def total_score(self):
        return self.sum_fields(Panss.TASK_FIELDS)

    def score_p(self):
        return self.sum_fields(Panss.P_FIELDS)

    def score_n(self):
        return self.sum_fields(Panss.N_FIELDS)

    def score_g(self):
        return self.sum_fields(Panss.G_FIELDS)

    def composite(self):
        return self.score_p() - self.score_n()

    def get_task_html(self):
        p = self.score_p()
        n = self.score_n()
        g = self.score_g()
        composite = self.composite()
        total = p + n + g
        ANSWERS = {
            None: None,
            1: WSTRING("panss_option1"),
            2: WSTRING("panss_option2"),
            3: WSTRING("panss_option3"),
            4: WSTRING("panss_option4"),
            5: WSTRING("panss_option5"),
            6: WSTRING("panss_option6"),
            7: WSTRING("panss_option7"),
        }
        h = self.get_standard_clinician_block() + """
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
        for q in Panss.TASK_FIELDS:
            h += tr_qa(
                WSTRING("panss_" + q + "_s"),
                get_from_dict(ANSWERS, getattr(self, q))
            )
        h += """
            </table>
        """ + DATA_COLLECTION_ONLY_DIV
        return h
