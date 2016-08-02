#!/usr/bin/env python3
# ciwa.py

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

from typing import List

from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    subheading_spanning_two_columns,
    tr,
    tr_qa,
)
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
# CIWA
# =============================================================================

class Ciwa(Task):
    NSCOREDQUESTIONS = 10

    tablename = "ciwa"
    shortname = "CIWA-Ar"
    longname = ("Clinical Institute Withdrawal Assessment for Alcohol "
                "Scale, Revised")
    fieldspecs = repeat_fieldspec(
        "q", 1, NSCOREDQUESTIONS - 1, min=0, max=7,
        comment_fmt="Q{n}, {s} (0-7, higher worse)",
        comment_strings=[
            "nausea/vomiting", "tremor", "paroxysmal sweats", "anxiety",
            "agitation", "tactile disturbances", "auditory disturbances",
            "visual disturbances", "headache/fullness in head"
        ]
    ) + [
        dict(name="q10", cctype="INT", min=0, max=4,
             comment="Q10, orientation/clouding of sensorium "
             "(0-4, higher worse)"),
        dict(name="t", cctype="INT",
             comment="Temperature (degrees C)"),
        dict(name="hr", cctype="INT", min=0,
             comment="Heart rate (beats/minute)"),
        dict(name="sbp", cctype="INT", min=0,
             comment="Systolic blood pressure (mmHg)"),
        dict(name="dbp", cctype="INT", min=0,
             comment="Diastolic blood pressure (mmHg)"),
        dict(name="rr", cctype="INT", min=0,
             comment="Respiratory rate (breaths/minute)"),
    ]
    has_clinician = True

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="CIWA total score",
            axis_label="Total score (out of 67)",
            axis_min=-0.5,
            axis_max=67.5,
            horizontal_lines=[14.5, 7.5],
            horizontal_labels=[
                TrackerLabel(17, WSTRING("severe")),
                TrackerLabel(11, WSTRING("moderate")),
                TrackerLabel(3.75, WSTRING("mild")),
            ]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="CIWA total score: {}/67".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/67)"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="Likely severity"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(repeat_fieldname(
                "q", 1, Ciwa.NSCOREDQUESTIONS)) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 1, Ciwa.NSCOREDQUESTIONS))

    def severity(self) -> str:
        score = self.total_score()
        if score >= 15:
            severity = WSTRING("ciwa_category_severe")
        elif score >= 8:
            severity = WSTRING("ciwa_category_moderate")
        else:
            severity = WSTRING("ciwa_category_mild")
        return severity

    def get_task_html(self) -> str:
        score = self.total_score()
        severity = self.severity()
        answer_dicts_dict = {}
        for q in repeat_fieldname("q", 1, Ciwa.NSCOREDQUESTIONS):
            d = {None: None}
            for option in range(0, 8):
                if option > 4 and q == "q10":
                    continue
                d[option] = WSTRING("ciwa_" + q + "_option" + str(option))
            answer_dicts_dict[q] = d
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 67")
        h += tr_qa(WSTRING("ciwa_severity") + " <sup>[1]</sup>", severity)
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="35%">Question</th>
                    <th width="65%">Answer</th>
                </tr>
        """
        for q in range(1, Ciwa.NSCOREDQUESTIONS + 1):
            h += tr_qa(
                WSTRING("ciwa_q" + str(q) + "_s"),
                get_from_dict(answer_dicts_dict["q" + str(q)],
                              getattr(self, "q" + str(q)))
            )
        h += subheading_spanning_two_columns(WSTRING("ciwa_vitals_title"))
        h += tr_qa(WSTRING("ciwa_t"), self.t)
        h += tr_qa(WSTRING("ciwa_hr"), self.hr)
        h += tr(WSTRING("ciwa_bp"),
                answer(self.sbp) + " / " + answer(self.dbp))
        h += tr_qa(WSTRING("ciwa_rr"), self.rr)
        h += """
            </table>
            <div class="footnotes">
                [1] Total score ≥15 severe, ≥8 moderate, otherwise
                    mild/minimal.
            </div>
        """
        return h
