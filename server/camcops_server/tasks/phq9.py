#!/usr/bin/env python
# camcops_server/tasks/phq9.py

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

from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import answer, get_yes_no, tr, tr_qa
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerAxisTick,
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# PHQ-9
# =============================================================================

class Phq9(Task):
    tablename = "phq9"
    shortname = "PHQ-9"
    longname = "Patient Health Questionnaire-9"
    fieldspecs = repeat_fieldspec(
        "q", 1, 9, min=0, max=3,
        comment_fmt="Q{n} ({s}) (0 not at all - 3 nearly every day)",
        comment_strings=[
            "anhedonia",
            "mood",
            "sleep",
            "energy",
            "appetite",
            "self-esteem/guilt",
            "concentration",
            "psychomotor",
            "death/self-harm",
        ]
    ) + [
        dict(name="q10", cctype="INT", min=0, max=3,
             comment="Q10 (difficulty in activities) (0 not difficult at "
                     "all - 3 extremely difficult)"),
    ]

    N_MAIN_QUESTIONS = 9

    def is_complete(self) -> bool:
        if not self.field_contents_valid():
            return False
        if not self.are_all_fields_complete(repeat_fieldname("q", 1, 9)):
            return False
        if self.total_score() > 0 and self.q10 is None:
            return False
        return True

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="PHQ-9 total score (rating depressive symptoms)",
            axis_label="Score for Q1-9 (out of 27)",
            axis_min=-0.5,
            axis_max=27.5,
            axis_ticks=[
                TrackerAxisTick(27, "27"),
                TrackerAxisTick(25, "25"),
                TrackerAxisTick(20, "20"),
                TrackerAxisTick(15, "15"),
                TrackerAxisTick(10, "10"),
                TrackerAxisTick(5, "5"),
                TrackerAxisTick(0, "0"),
            ],
            horizontal_lines=[
                19.5,
                14.5,
                9.5,
                4.5
            ],
            horizontal_labels=[
                TrackerLabel(23, wappstring("severe")),
                TrackerLabel(17, wappstring("moderately_severe")),
                TrackerLabel(12, wappstring("moderate")),
                TrackerLabel(7, wappstring("mild")),
                TrackerLabel(2.25, wappstring("none")),
            ]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="PHQ-9 total score {}/27 ({})".format(
                self.total_score(), self.severity())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/27)"),
            dict(name="n_core", cctype="INT", value=self.n_core(),
                 comment="Number of core symptoms"),
            dict(name="n_other", cctype="INT", value=self.n_other(),
                 comment="Number of other symptoms"),
            dict(name="n_total", cctype="INT", value=self.n_total(),
                 comment="Total number of symptoms"),
            dict(name="is_mds", cctype="BOOL", value=self.is_mds(),
                 comment="PHQ9 major depressive syndrome?"),
            dict(name="is_ods", cctype="BOOL", value=self.is_ods(),
                 comment="PHQ9 other depressive syndrome?"),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="PHQ9 depression severity"),
        ]

    def total_score(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 1, 9))

    def one_if_q_ge(self, qnum: int, threshold: int) -> int:
        value = getattr(self, "q" + str(qnum))
        return 1 if value is not None and value >= threshold else 0

    def n_core(self) -> int:
        return (self.one_if_q_ge(1, 2) +
                self.one_if_q_ge(2, 2))

    def n_other(self) -> int:
        return (self.one_if_q_ge(3, 2) +
                self.one_if_q_ge(4, 2) +
                self.one_if_q_ge(5, 2) +
                self.one_if_q_ge(6, 2) +
                self.one_if_q_ge(7, 2) +
                self.one_if_q_ge(8, 2) +
                self.one_if_q_ge(9, 1))  # suicidality
        # suicidality counted whenever present

    def n_total(self) -> int:
        return self.n_core() + self.n_other()

    def is_mds(self) -> bool:
        return self.n_core() >= 1 and self.n_total() >= 5

    def is_ods(self) -> bool:
        return self.n_core() >= 1 and 2 <= self.n_total() <= 4

    def severity(self) -> str:
        total = self.total_score()
        if total >= 20:
            return wappstring("severe")
        elif total >= 15:
            return wappstring("moderately_severe")
        elif total >= 10:
            return wappstring("moderate")
        elif total >= 5:
            return wappstring("mild")
        else:
            return wappstring("none")

    def get_task_html(self) -> str:
        main_dict = {
            None: None,
            0: "0 — " + self.wxstring("a0"),
            1: "1 — " + self.wxstring("a1"),
            2: "2 — " + self.wxstring("a2"),
            3: "3 — " + self.wxstring("a3")
        }
        q10_dict = {
            None: None,
            0: "0 — " + self.wxstring("fa0"),
            1: "1 — " + self.wxstring("fa1"),
            2: "2 — " + self.wxstring("fa2"),
            3: "3 — " + self.wxstring("fa3")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(wappstring("total_score") + " <sup>[1]</sup>",
                answer(self.total_score()) + " / 27")
        h += tr_qa(self.wxstring("depression_severity") + " <sup>[2]</sup>",
                   self.severity())
        h += tr(
            "Number of symptoms: core <sup>[3]</sup>, other <sup>[4]</sup>, "
            "total",
            answer(self.n_core()) + "/2, " +
            answer(self.n_other()) + "/7, " +
            answer(self.n_total()) + "/9"
        )
        h += tr_qa(self.wxstring("mds") + " <sup>[5]</sup>",
                   get_yes_no(self.is_mds()))
        h += tr_qa(self.wxstring("ods") + " <sup>[6]</sup>",
                   get_yes_no(self.is_ods()))
        h += """
                </table>
            </div>
            <div class="explanation">
                Ratings are over the last 2 weeks.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """
        for i in range(1, self.N_MAIN_QUESTIONS + 1):
            nstr = str(i)
            h += tr_qa(self.wxstring("q" + nstr),
                       get_from_dict(main_dict, getattr(self, "q" + nstr)))
        h += tr_qa("10. " + self.wxstring("finalq"),
                   get_from_dict(q10_dict, self.q10))
        h += """
            </table>
            <div class="footnotes">
                [1] Sum for questions 1–9.
                [2] Total score ≥20 severe, ≥15 moderately severe,
                    ≥10 moderate, ≥5 mild, &lt;5 none.
                [3] Number of questions 1–2 rated ≥2.
                [4] Number of questions 3–8 rated ≥2, or question 9
                    rated ≥1.
                [5] ≥1 core symptom and ≥5 total symptoms (as per
                    DSM-IV-TR page 356).
                [6] ≥1 core symptom and 2–4 total symptoms (as per
                    DSM-IV-TR page 775).
            </div>
        """
        return h
