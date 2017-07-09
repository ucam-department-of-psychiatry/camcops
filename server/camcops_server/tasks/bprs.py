#!/usr/bin/env python
# bprs.py

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

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, tr, tr_qa
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


# =============================================================================
# BPRS
# =============================================================================

class Bprs(Task):
    NQUESTIONS = 20

    tablename = "bprs"
    shortname = "BPRS"
    longname = "Brief Psychiatric Rating Scale"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=7,
        comment_fmt="Q{n}, {s} (1-7, higher worse, 0 for unable to rate)",
        comment_strings=[
            "somatic concern", "anxiety", "emotional withdrawal",
            "conceptual disorganisation", "guilt", "tension",
            "mannerisms/posturing", "grandiosity", "depressive mood",
            "hostility", "suspiciousness", "hallucinatory behaviour",
            "motor retardation", "uncooperativeness",
            "unusual thought content", "blunted affect", "excitement",
            "disorientation", "severity of illness", "global improvement"])
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]
    SCORED_FIELDS = [x for x in TASK_FIELDS if (x != "q19" and x != "q20")]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="BPRS total score",
            axis_label="Total score (out of 126)",
            axis_min=-0.5,
            axis_max=126.5,
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="BPRS total score {}/126".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/126)"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(Bprs.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(Bprs.SCORED_FIELDS, ignorevalue=0)
        # "0" means "not rated"

    def get_task_html(self) -> str:
        main_dict = {
            None: None,
            0: "0 — " + self.wxstring("old_option0"),
            1: "1 — " + self.wxstring("old_option1"),
            2: "2 — " + self.wxstring("old_option2"),
            3: "3 — " + self.wxstring("old_option3"),
            4: "4 — " + self.wxstring("old_option4"),
            5: "5 — " + self.wxstring("old_option5"),
            6: "6 — " + self.wxstring("old_option6"),
            7: "7 — " + self.wxstring("old_option7")
        }
        q19_dict = {
            None: None,
            1: self.wxstring("q19_option1"),
            2: self.wxstring("q19_option2"),
            3: self.wxstring("q19_option3"),
            4: self.wxstring("q19_option4"),
            5: self.wxstring("q19_option5"),
            6: self.wxstring("q19_option6"),
            7: self.wxstring("q19_option7")
        }
        q20_dict = {
            None: None,
            0: self.wxstring("q20_option0"),
            1: self.wxstring("q20_option1"),
            2: self.wxstring("q20_option2"),
            3: self.wxstring("q20_option3"),
            4: self.wxstring("q20_option4"),
            5: self.wxstring("q20_option5"),
            6: self.wxstring("q20_option6"),
            7: self.wxstring("q20_option7")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(wappstring("total_score") +
                " (0–126; 18–126 if all rated) <sup>[1]</sup>",
                answer(self.total_score()))
        h += """
                </table>
            </div>
            <div class="explanation">
                Ratings pertain to the past week, or behaviour during
                interview. Each question has specific answer definitions (see
                e.g. tablet app).
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer <sup>[2]</sup></th>
                </tr>
        """
        for i in range(1, Bprs.NQUESTIONS - 1):  # only does 1-18
            h += tr_qa(
                self.wxstring("q" + str(i) + "_title"),
                get_from_dict(main_dict, getattr(self, "q" + str(i)))
            )
        h += tr_qa(self.wxstring("q19_title"),
                   get_from_dict(q19_dict, self.q19))
        h += tr_qa(self.wxstring("q20_title"),
                   get_from_dict(q20_dict, self.q20))
        h += """
            </table>
            <div class="footnotes">
                [1] Only questions 1–18 are scored.
                [2] All answers are in the range 1–7, or 0 (not assessed, for
                    some).
            </div>
        """
        return h
