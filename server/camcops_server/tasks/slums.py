#!/usr/bin/env python
# slums.py

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

from ..cc_modules.cc_constants import PV
from ..cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    subheading_spanning_two_columns,
    td,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    Task,
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# SLUMS
# =============================================================================

class Slums(Task):
    PREAMBLE_FIELDSPECS = [
        dict(name="alert", cctype="INT", pv=PV.BIT,
             comment="Is the patient alert? (0 no, 1 yes)"),
        dict(name="highschooleducation", cctype="INT", pv=PV.BIT,
             comment="Does that patient have at least a high-school level of "
             "education? (0 no, 1 yes"),
    ]
    PREAMBLE_FIELDS = [x["name"] for x in PREAMBLE_FIELDSPECS]
    SCORED_FIELDSPECS = [
        dict(name="q1", cctype="INT", pv=PV.BIT,
             comment="Q1 (day) (0-1)"),
        dict(name="q2", cctype="INT", pv=PV.BIT,
             comment="Q2 (year) (0-1)"),
        dict(name="q3", cctype="INT", pv=PV.BIT,
             comment="Q3 (state) (0-1)"),
        dict(name="q5a", cctype="INT", pv=PV.BIT,
             comment="Q5a (money spent) (0-1)"),
        dict(name="q5b", cctype="INT", pv=[0, 2],
             comment="Q5b (money left) (0 or 2)"),  # worth 2 points
        dict(name="q6", cctype="INT", min=0, max=3,
             comment="Q6 (animal naming) (0-3)"),  # from 0 to 3 points
        dict(name="q7a", cctype="INT", pv=PV.BIT,
             comment="Q7a (recall apple) (0-1)"),
        dict(name="q7b", cctype="INT", pv=PV.BIT,
             comment="Q7b (recall pen) (0-1)"),
        dict(name="q7c", cctype="INT", pv=PV.BIT,
             comment="Q7c (recall tie) (0-1)"),
        dict(name="q7d", cctype="INT", pv=PV.BIT,
             comment="Q7d (recall house) (0-1)"),
        dict(name="q7e", cctype="INT", pv=PV.BIT,
             comment="Q7e (recall car) (0-1)"),
        dict(name="q8b", cctype="INT", pv=PV.BIT,
             comment="Q8b (reverse 648) (0-1)"),
        dict(name="q8c", cctype="INT", pv=PV.BIT,
             comment="Q8c (reverse 8537) (0-1)"),
        dict(name="q9a", cctype="INT", pv=[0, 2],
             comment="Q9a (clock - hour markers) (0 or 2)"),  # worth 2 points
        dict(name="q9b", cctype="INT", pv=[0, 2],
             comment="Q9b (clock - time) (0 or 2)"),  # worth 2 points
        dict(name="q10a", cctype="INT", pv=PV.BIT,
             comment="Q10a (X in triangle) (0-1)"),
        dict(name="q10b", cctype="INT", pv=PV.BIT,
             comment="Q10b (biggest figure) (0-1)"),
        dict(name="q11a", cctype="INT", pv=[0, 2],
             comment="Q11a (story - name) (0 or 2)"),  # worth 2 points
        dict(name="q11b", cctype="INT", pv=[0, 2],
             comment="Q11b (story - occupation) (0 or 2)"),  # worth 2 points
        dict(name="q11c", cctype="INT", pv=[0, 2],
             comment="Q11c (story - back to work) (0 or 2)"),  # worth 2 points
        dict(name="q11d", cctype="INT", pv=[0, 2],
             comment="Q11d (story - state) (0 or 2)"),  # worth 2 points
    ]
    SCORED_FIELDS = [x["name"] for x in SCORED_FIELDSPECS]
    OTHER_FIELDSPECS = [
        dict(name="clockpicture_blobid", cctype="INT",
             comment="BLOB ID of clock picture"),
        dict(name="shapespicture_blobid", cctype="INT",
             comment="BLOB ID of shapes picture"),
        dict(name="comments", cctype="TEXT",
             comments="Clinician's comments"),
    ]

    tablename = "slums"
    shortname = "SLUMS"
    longname = "St Louis University Mental Status"
    fieldspecs = (
        PREAMBLE_FIELDSPECS +
        SCORED_FIELDSPECS +
        OTHER_FIELDSPECS
    )
    has_clinician = True
    pngblob_name_idfield_rotationfield_list = [
        ("clockpicture", "clockpicture_blobid", None),
        ("shapespicture", "shapespicture_blobid", None),
    ]

    def get_trackers(self) -> List[TrackerInfo]:
        if self.highschooleducation == 1:
            hlines = [26.5, 20.5]
            y_upper = 28.25
            y_middle = 23.5
        else:
            hlines = [24.5, 19.5]
            y_upper = 27.25
            y_middle = 22
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="SLUMS total score",
            axis_label="Total score (out of 30)",
            axis_min=-0.5,
            axis_max=30.5,
            horizontal_lines=hlines,
            horizontal_labels=[
                TrackerLabel(y_upper, wappstring("normal")),
                TrackerLabel(y_middle, self.wxstring("category_mci")),
                TrackerLabel(17, self.wxstring("category_dementia")),
            ]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="SLUMS total score {}/30 ({})".format(
                self.total_score(), self.category())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/30)"),
            dict(name="category", cctype="TEXT", value=self.category(),
                 comment="Category"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.PREAMBLE_FIELDS +
                                         self.SCORED_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(self.SCORED_FIELDS)

    def category(self) -> str:
        score = self.total_score()
        if self.highschooleducation == 1:
            if score >= 27:
                return wappstring("normal")
            elif score >= 21:
                return self.wxstring("category_mci")
            else:
                return self.wxstring("category_dementia")
        else:
            if score >= 25:
                return wappstring("normal")
            elif score >= 20:
                return self.wxstring("category_mci")
            else:
                return self.wxstring("category_dementia")

    def get_task_html(self) -> str:
        score = self.total_score()
        category = self.category()
        h = self.get_standard_clinician_comments_block(self.comments) + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(wappstring("total_score"), answer(score) + " / 30")
        h += tr_qa(wappstring("category") + " <sup>[1]</sup>", category)
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Score</th>
                </tr>
        """
        h += tr_qa(self.wxstring("alert_s"), get_yes_no_none(self.alert))
        h += tr_qa(self.wxstring("highschool_s"),
                   get_yes_no_none(self.highschooleducation))
        h += tr_qa(self.wxstring("q1_s"), self.q1)
        h += tr_qa(self.wxstring("q2_s"), self.q2)
        h += tr_qa(self.wxstring("q3_s"), self.q3)
        h += tr("Q5 <sup>[2]</sup> (money spent, money left "
                "[<i>scores 2</i>]",
                ", ".join([answer(x) for x in [self.q5a, self.q5b]]))
        h += tr_qa("Q6 (animal fluency) [<i>≥15 scores 3, 10–14 scores 2, "
                   "5–9 scores 1, 0–4 scores 0</i>]",
                   self.q6)
        h += tr("Q7 (recall: apple, pen, tie, house, car)",
                ", ".join([answer(x) for x in [self.q7a, self.q7b, self.q7c,
                                               self.q7d, self.q7e]]))
        h += tr("Q8 (backwards: 648, 8537)",
                ", ".join([answer(x) for x in [self.q8b, self.q8c]]))
        h += tr("Q9 (clock: hour markers, time [<i>score 2 each</i>]",
                ", ".join([answer(x) for x in [self.q9a, self.q9b]]))
        h += tr("Q10 (X in triangle; which is biggest?)",
                ", ".join([answer(x) for x in [self.q10a, self.q10b]]))
        h += tr("Q11 (story: Female’s name? Job? When back to work? "
                "State she lived in? [<i>score 2 each</i>])",
                ", ".join([answer(x) for x in [self.q11a, self.q11b,
                                               self.q11c, self.q11d]]))
        h += """
            </table>
            <table class="taskdetail">
        """
        h += subheading_spanning_two_columns("Images of tests: clock, shapes")
        h += tr(
            td(self.get_blob_png_html(self.clockpicture_blobid),
               td_width="50%", td_class="photo"),
            td(self.get_blob_png_html(self.shapespicture_blobid),
               td_width="50%", td_class="photo"),
            literal=True
        )
        h += """
            </table>
            <div class="footnotes">
                [1] With high school education:
                ≥27 normal, ≥21 MCI, ≤20 dementia.
                Without high school education:
                ≥25 normal, ≥20 MCI, ≤19 dementia.
                (Tariq et al. 2006, PubMed ID 17068312.)
                [2] Q4 (learning the five words) isn’t scored.
            </div>
        """
        return h
