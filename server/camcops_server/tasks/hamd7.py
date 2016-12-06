#!/usr/bin/env python
# hamd7.py

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

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, tr, tr_qa
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
# HAMD-7
# =============================================================================

class Hamd7(Task):
    NQUESTIONS = 7

    tablename = "hamd7"
    shortname = "HAMD-7"
    longname = "Hamilton Rating Scale for Depression (7-item scale)"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=4,  # see below
        comment_fmt="Q{n}, {s} (0-4, except Q6 0-2; higher worse)",
        comment_strings=["depressed mood", "guilt",
                         "interest/pleasure/level of activities",
                         "psychological anxiety", "somatic anxiety",
                         "energy/somatic symptoms", "suicide"]
    )
    # Now fix the wrong bits. Hardly elegant!
    for item in fieldspecs:
        if item["name"] == "q6":
            item["max"] = 2
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="HAM-D-7 total score",
            axis_label="Total score (out of 26)",
            axis_min=-0.5,
            axis_max=26.5,
            horizontal_lines=[19.5, 11.5, 3.5],
            horizontal_labels=[
                TrackerLabel(23, WSTRING("hamd7_severity_severe")),
                TrackerLabel(15.5, WSTRING("hamd7_severity_moderate")),
                TrackerLabel(7.5, WSTRING("hamd7_severity_mild")),
                TrackerLabel(1.75, WSTRING("hamd7_severity_none")),
            ]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="HAM-D-7 total score {}/26 ({})".format(
                self.total_score(), self.severity())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/26)"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="Severity"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def severity(self) -> str:
        score = self.total_score()
        if score >= 20:
            return WSTRING("hamd7_severity_severe")
        elif score >= 12:
            return WSTRING("hamd7_severity_moderate")
        elif score >= 4:
            return WSTRING("hamd7_severity_mild")
        else:
            return WSTRING("hamd7_severity_none")

    def get_task_html(self) -> str:
        score = self.total_score()
        severity = self.severity()
        answer_dicts = []
        for q in range(1, self.NQUESTIONS + 1):
            d = {None: None}
            for option in range(0, 5):
                if q == 6 and option > 2:
                    continue
                d[option] = WSTRING("hamd7_q" + str(q) + "_option" +
                                    str(option))
            answer_dicts.append(d)
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 26")
        h += tr_qa(WSTRING("hamd7_severity") + " <sup>[1]</sup>", severity)
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="30%">Question</th>
                    <th width="70%">Answer</th>
                </tr>
        """
        for q in range(1, self.NQUESTIONS + 1):
            h += tr_qa(
                WSTRING("hamd7_q" + str(q) + "_s"),
                get_from_dict(answer_dicts[q - 1], getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] ≥20 severe, ≥12 moderate, ≥4 mild, &lt;4 none.
            </div>
        """
        return h
