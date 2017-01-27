#!/usr/bin/env python
# hads.py

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

from ..cc_modules.cc_constants import DATA_COLLECTION_UNLESS_UPGRADED_DIV
from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import answer, tr_qa
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task, TrackerInfo
from ..cc_modules.cc_logger import log


# =============================================================================
# HADS (crippled unless upgraded locally)
# =============================================================================

class Hads(Task):
    NQUESTIONS = 14
    ANXIETY_QUESTIONS = [1, 3, 5, 7, 9, 11, 13]
    DEPRESSION_QUESTIONS = [2, 4, 6, 8, 10, 12, 14]

    tablename = "hads"
    shortname = "HADS"
    longname = "Hospital Anxiety and Depression Scale (data collection only)"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=3,
        comment_fmt="Q{n}: {s} (0-3)",
        comment_strings=[
            "tense", "enjoy usual", "apprehensive", "laugh", "worry",
            "cheerful", "relaxed", "slow", "butterflies", "appearance",
            "restless", "anticipate", "panic", "book/TV/radio"
        ])

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def is_complete(self) -> bool:
        return self.field_contents_valid() and self.are_all_fields_complete(
            repeat_fieldname("q", 1, self.NQUESTIONS))

    def get_trackers(self) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.anxiety_score(),
                plot_label="HADS anxiety score",
                axis_label="Anxiety score (out of 21)",
                axis_min=-0.5,
                axis_max=21.5,
            ),
            TrackerInfo(
                value=self.depression_score(),
                plot_label="HADS depression score",
                axis_label="Depression score (out of 21)",
                axis_min=-0.5,
                axis_max=21.5
            ),
        ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="anxiety score {}/21, depression score {}/21".format(
                self.anxiety_score(), self.depression_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="anxiety", cctype="INT",
                 value=self.anxiety_score(), comment="Anxiety score (/21)"),
            dict(name="depression", cctype="INT",
                 value=self.depression_score(),
                 comment="Depression score (/21)"),
        ]

    def score(self, questions: List[int]) -> int:
        fields = self.fieldnames_from_list("q", questions)
        return self.sum_fields(fields)

    def anxiety_score(self) -> int:
        return self.score(self.ANXIETY_QUESTIONS)

    def depression_score(self) -> int:
        return self.score(self.DEPRESSION_QUESTIONS)

    def get_task_html(self) -> str:
        min_score = 0
        max_score = 3
        crippled = not self.extrastrings_exist()
        log.info("crippled: {}".format(crippled))
        a = self.anxiety_score()
        d = self.depression_score()
        h = """
            <div class="summary">
                <table class="summary">
                    {is_complete_tr}
                    <tr>
                        <td>{sa}</td><td>{a} / 21</td>
                    </tr>
                    <tr>
                        <td>{sd}</td><td>{d} / 21</td>
                    </tr>
                </table>
            </div>
            <div class="explanation">
                All questions are scored from 0–3
                (0 least symptomatic, 3 most symptomatic).
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            is_complete_tr=self.get_is_complete_tr(),
            sa=WSTRING("hads_anxiety_score"),
            a=answer(a),
            sd=WSTRING("hads_depression_score"),
            d=answer(d),
        )
        for n in range(1, self.NQUESTIONS + 1):
            if crippled:
                q = "HADS: Q{}".format(n)
            else:
                q = "Q{}. {}".format(
                    n,
                    self.WXSTRING("q" + str(n) + "_stem")
                )
            if n in self.ANXIETY_QUESTIONS:
                q += " (A)"
            if n in self.DEPRESSION_QUESTIONS:
                q += " (D)"
            v = getattr(self, "q" + str(n))
            if crippled or v is None or v < min_score or v > max_score:
                a = v
            else:
                a = "{}: {}".format(v, self.WXSTRING("q{}_a{}".format(n, v)))
            h += tr_qa(q, a)
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
