#!/usr/bin/env python3
# phq15.py

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

from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import answer, get_yes_no, tr, tr_qa
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
# PHQ-15
# =============================================================================

class Phq15(Task):
    NQUESTIONS = 15

    tablename = "phq15"
    shortname = "PHQ-15"
    longname = "Patient Health Questionnaire-15"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=2,
        comment_fmt="Q{n} ({s}) (0 not bothered at all - 2 bothered a lot)",
        comment_strings=[
            "stomach pain",
            "back pain",
            "limb/joint pain",
            "F - menstrual",
            "headaches",
            "chest pain",
            "dizziness",
            "fainting",
            "palpitations",
            "breathless",
            "sex",
            "constipation/diarrhoea",
            "nausea/indigestion",
            "energy",
            "sleep",
        ]
    )

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def is_complete(self) -> bool:
        if not self.field_contents_valid():
            return False
        if not self.are_all_fields_complete(repeat_fieldname("q", 1, 3)):
            return False
        if not self.are_all_fields_complete(repeat_fieldname(
                                            "q", 5, self.NQUESTIONS)):
            return False
        if self.is_female():
            return self.q4 is not None
        else:
            return True

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="PHQ-15 total score (rating somatic symptoms)",
            axis_label="Score for Q1-15 (out of 30)",
            axis_min=-0.5,
            axis_max=30.5,
            horizontal_lines=[14.5, 9.5, 4.5],
            horizontal_labels=[
                TrackerLabel(22, WSTRING("severe")),
                TrackerLabel(12, WSTRING("moderate")),
                TrackerLabel(7, WSTRING("mild")),
                TrackerLabel(2.25, WSTRING("none")),
            ]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="PHQ-15 total score {}/30 ({})".format(
                self.total_score(), self.severity())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/30)"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="Severity"),
        ]

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def num_severe(self) -> int:
        n = 0
        for i in range(1, self.NQUESTIONS + 1):
            value = getattr(self, "q" + str(i))
            if value is not None and value >= 2:
                n += 1
        return n

    def severity(self) -> str:
        score = self.total_score()
        if score >= 15:
            return WSTRING("severe")
        elif score >= 10:
            return WSTRING("moderate")
        elif score >= 5:
            return WSTRING("mild")
        else:
            return WSTRING("none")

    def get_task_html(self) -> str:
        score = self.total_score()
        nsevere = self.num_severe()
        somatoform_likely = nsevere >= 3
        severity = self.severity()
        answer_dict = {None: None}
        for option in range(0, 3):
            answer_dict[option] = str(option) + " – " + \
                WSTRING("phq15_a" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score") + " <sup>[1]</sup>",
                answer(score) + " / 30")
        h += tr_qa(WSTRING("phq15_n_severe_symptoms") + " <sup>[2]</sup>",
                   nsevere)
        h += tr_qa(
            WSTRING("phq15_exceeds_somatoform_cutoff") + " <sup>[3]</sup>",
            get_yes_no(somatoform_likely))
        h += tr_qa(WSTRING("phq15_symptom_severity") + " <sup>[4]</sup>",
                   severity)
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """
        for q in range(1, self.NQUESTIONS + 1):
            h += tr_qa(
                WSTRING("phq15_q" + str(q)),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] In males, maximum score is actually 28.
                [2] Questions with scores ≥2 are considered severe.
                [3] ≥3 severe symptoms.
                [4] Total score ≥15 severe, ≥10 moderate, ≥5 mild,
                    otherwise none.
            </div>
        """
        return h
