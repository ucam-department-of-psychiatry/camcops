#!/usr/bin/env python
# moca.py

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
from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    italic,
    subheading_spanning_two_columns,
    td,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    LabelAlignment,
    Task,
    TrackerInfo,
    TrackerLabel,
)


WORDLIST = ["FACE", "VELVET", "CHURCH", "DAISY", "RED"]


# =============================================================================
# MoCA
# =============================================================================

class Moca(Task):
    NQUESTIONS = 28

    tablename = "moca"
    shortname = "MoCA"
    longname = "Montreal Cognitive Assessment"
    fieldspecs = (
        repeat_fieldspec(
            "q", 1, NQUESTIONS, min=0, max=1,  # see below
            comment_fmt="{s}",
            comment_strings=[
                "Q1 (VSE/path) (0-1)",
                "Q2 (VSE/cube) (0-1)",
                "Q3 (VSE/clock/contour) (0-1)",
                "Q4 (VSE/clock/numbers) (0-1)",
                "Q5 (VSE/clock/hands) (0-1)",
                "Q6 (naming/lion) (0-1)",
                "Q7 (naming/rhino) (0-1)",
                "Q8 (naming/camel) (0-1)",
                "Q9 (attention/5 digits) (0-1)",
                "Q10 (attention/3 digits) (0-1)",
                "Q11 (attention/tapping) (0-1)",
                "Q12 (attention/serial 7s) (0-3)",  # different max
                "Q13 (language/sentence 1) (0-1)",
                "Q14 (language/sentence 2) (0-1)",
                "Q15 (language/fluency) (0-1)",
                "Q16 (abstraction 1) (0-1)",
                "Q17 (abstraction 2) (0-1)",
                "Q18 (recall word/face) (0-1)",
                "Q19 (recall word/velvet) (0-1)",
                "Q20 (recall word/church) (0-1)",
                "Q21 (recall word/daisy) (0-1)",
                "Q22 (recall word/red) (0-1)",
                "Q23 (orientation/date) (0-1)",
                "Q24 (orientation/month) (0-1)",
                "Q25 (orientation/year) (0-1)",
                "Q26 (orientation/day) (0-1)",
                "Q27 (orientation/place) (0-1)",
                "Q28 (orientation/city) (0-1)",
            ]
        ) + [
            dict(name="education12y_or_less", cctype="INT", pv=PV.BIT,
                 comment="<=12 years of education (0 no, 1 yes)"),
            dict(name="trailpicture_blobid", cctype="INT",
                 comment="BLOB ID of trail picture"),
            dict(name="cubepicture_blobid", cctype="INT",
                 comment="BLOB ID of cube picture"),
            dict(name="clockpicture_blobid", cctype="INT",
                 comment="BLOB ID of clock picture"),
        ] +
        repeat_fieldspec(
            "register_trial1_", 1, 5, pv=PV.BIT,
            comment_fmt="Registration, trial 1 (not scored), {n}: {s} "
            "(0 or 1)", comment_strings=WORDLIST) +
        repeat_fieldspec(
            "register_trial2_", 1, 5, pv=PV.BIT,
            comment_fmt="Registration, trial 2 (not scored), {n}: {s} "
            "(0 or 1)", comment_strings=WORDLIST) +
        repeat_fieldspec(
            "recall_category_cue_", 1, 5, pv=PV.BIT,
            comment_fmt="Recall with category cue (not scored), {n}: {s} "
            "(0 or 1)", comment_strings=WORDLIST) +
        repeat_fieldspec(
            "recall_mc_cue_", 1, 5, pv=PV.BIT,
            comment_fmt="Recall with multiple-choice cue (not scored), "
            "{n}: {s} (0 or 1)", comment_strings=WORDLIST) +
        [
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
        ]
    )
    # Fix error above. Hardly elegant!
    for item in fieldspecs:
        if item["name"] == "q12":
            item["max"] = 3
    has_clinician = True
    pngblob_name_idfield_rotationfield_list = [
        ("trailpicture", "trailpicture_blobid", None),
        ("cubepicture", "cubepicture_blobid", None),
        ("clockpicture", "clockpicture_blobid", None),
    ]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="MOCA total score",
            axis_label="Total score (out of 30)",
            axis_min=-0.5,
            axis_max=30.5,
            horizontal_lines=[25.5],
            horizontal_labels=[
                TrackerLabel(26, WSTRING("normal"), LabelAlignment.bottom),
                TrackerLabel(25, WSTRING("abnormal"), LabelAlignment.top),
            ]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="MOCA total score {}/30".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/30)"),
            dict(name="category", cctype="TEXT", value=self.category(),
                 comment="Categorization"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(
                repeat_fieldname("q", 1, self.NQUESTIONS)) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(
            repeat_fieldname("q", 1, self.NQUESTIONS) +
            ["education12y_or_less"]  # extra point for this
        )

    def score_vsp(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 1, 5))

    def score_naming(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 6, 8))

    def score_attention(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 9, 12))

    def score_language(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 13, 15))

    def score_abstraction(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 16, 17))

    def score_memory(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 18, 22))

    def score_orientation(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 23, 28))

    def category(self) -> str:
        totalscore = self.total_score()
        return WSTRING("normal") if totalscore >= 26 else WSTRING("abnormal")

    def get_task_html(self) -> str:
        vsp = self.score_vsp()
        naming = self.score_naming()
        attention = self.score_attention()
        language = self.score_language()
        abstraction = self.score_abstraction()
        memory = self.score_memory()
        orientation = self.score_orientation()
        totalscore = self.total_score()
        category = self.category()

        h = self.get_standard_clinician_comments_block(self.comments) + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(totalscore) + " / 30")
        h += tr_qa(WSTRING("moca_category") + " <sup>[1]</sup>",
                   category)
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="69%">Question</th>
                    <th width="31%">Score</th>
                </tr>
        """

        h += tr(WSTRING("moca_subscore_visuospatial"),
                answer(vsp) + " / 5",
                tr_class="subheading")
        h += tr("Path, cube, clock/contour, clock/numbers, clock/hands",
                ", ".join([answer(x) for x in [self.q1, self.q2, self.q3,
                                               self.q4, self.q5]]))

        h += tr(WSTRING("moca_subscore_naming"),
                answer(naming) + " / 3",
                tr_class="subheading")
        h += tr("Lion, rhino, camel",
                ", ".join([answer(x) for x in [self.q6, self.q7, self.q8]]))

        h += tr(WSTRING("moca_subscore_attention"),
                answer(attention) + " / 6",
                tr_class="subheading")
        h += tr("5 digits forwards, 3 digits backwards, tapping, serial 7s "
                "[<i>scores 3</i>]",
                ", ".join([answer(x) for x in [self.q9, self.q10, self.q11,
                                               self.q12]]))

        h += tr(WSTRING("moca_subscore_language"),
                answer(language) + " / 3",
                tr_class="subheading")
        h += tr("Repeat sentence 1, repeat sentence 2, fluency to letter ‘F’",
                ", ".join([answer(x) for x in [self.q13, self.q14, self.q15]]))

        h += tr(WSTRING("moca_subscore_abstraction"),
                answer(abstraction) + " / 2",
                tr_class="subheading")
        h += tr("Means of transportation, measuring instruments",
                ", ".join([answer(x) for x in [self.q16, self.q17]]))

        h += tr(WSTRING("moca_subscore_memory"),
                answer(memory) + " / 5",
                tr_class="subheading")
        h += tr(
            "Registered on first trial [<i>not scored</i>]",
            ", ".join([
                answer(x, formatter_answer=italic)
                for x in [
                    self.register_trial1_1,
                    self.register_trial1_2,
                    self.register_trial1_3,
                    self.register_trial1_4,
                    self.register_trial1_5
                ]
            ])
        )
        h += tr(
            "Registered on second trial [<i>not scored</i>]",
            ", ".join([
                answer(x, formatter_answer=italic)
                for x in [
                    self.register_trial2_1,
                    self.register_trial2_2,
                    self.register_trial2_3,
                    self.register_trial2_4,
                    self.register_trial2_5
                ]
            ])
        )
        h += tr(
            "Recall FACE, VELVET, CHURCH, DAISY, RED with no cue",
            ", ".join([
                answer(x) for x in [
                    self.q18, self.q19, self.q20, self.q21, self.q22
                ]
            ])
        )
        h += tr(
            "Recall with category cue [<i>not scored</i>]",
            ", ".join([
                answer(x, formatter_answer=italic)
                for x in [
                    self.recall_category_cue_1,
                    self.recall_category_cue_2,
                    self.recall_category_cue_3,
                    self.recall_category_cue_4,
                    self.recall_category_cue_5
                ]
            ])
        )
        h += tr(
            "Recall with multiple-choice cue [<i>not scored</i>]",
            ", ".join([
                answer(x, formatter_answer=italic)
                for x in [
                    self.recall_mc_cue_1,
                    self.recall_mc_cue_2,
                    self.recall_mc_cue_3,
                    self.recall_mc_cue_4,
                    self.recall_mc_cue_5
                ]
            ])
        )

        h += tr(WSTRING("moca_subscore_orientation"),
                answer(orientation) + " / 6",
                tr_class="subheading")
        h += tr(
            "Date, month, year, day, place, city",
            ", ".join([
                answer(x) for x in [
                    self.q23, self.q24, self.q25, self.q26, self.q27, self.q28
                ]
            ])
        )

        h += subheading_spanning_two_columns(WSTRING("moca_education_s"))
        h += tr_qa("≤12 years’ education?", self.education12y_or_less)
        h += """
            </table>
            <table class="taskdetail">
        """
        h += subheading_spanning_two_columns(
            "Images of tests: trail, cube, clock",
            th_not_td=True)
        h += tr(
            td(self.get_blob_png_html(self.trailpicture_blobid),
               td_class="photo", td_width="50%"),
            td(self.get_blob_png_html(self.cubepicture_blobid),
               td_class="photo", td_width="50%"),
            literal=True,
        )
        h += tr(
            td(self.get_blob_png_html(self.trailpicture_blobid),
               td_class="photo", td_width="50%"),
            td("", td_class="subheading"),
            literal=True,
        )
        h += """
            </table>
            <div class="footnotes">
                [1] Normal is ≥26 (Nasreddine et al. 2005, PubMed ID 15817019).
            </div>
            <div class="copyright">
                MoCA: Copyright © Ziad Nasreddine.
                May be reproduced without permission for CLINICAL and
                EDUCATIONAL use. You must obtain permission from the copyright
                holder for any other use.
            </div>
        """
        return h
