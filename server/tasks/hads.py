#!/usr/bin/env python3
# hads.py

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

from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    tr_qa,
)
from cc_modules.cc_string import task_extrastrings_exist, WSTRING, WXSTRING
from cc_modules.cc_task import (
    CTV_DICTLIST_INCOMPLETE,
    DATA_COLLECTION_UNLESS_UPGRADED_DIV,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# HADS (crippled unless upgraded locally)
# =============================================================================

class Hads(Task):
    NQUESTIONS = 14
    EXTRASTRING_TASKNAME = "hads"
    ANXIETY_QUESTIONS = [1, 3, 5, 7, 9, 11, 13]
    DEPRESSION_QUESTIONS = [2, 4, 6, 8, 10, 12, 14]
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=3,
        comment_fmt="Q{n}: {s} (0-3)",
        comment_strings=[
            "tense", "enjoy usual", "apprehensive", "laugh", "worry",
            "cheerful", "relaxed", "slow", "butterflies", "appearance",
            "restless", "anticipate", "panic", "book/TV/radio"
        ])
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "hads"

    @classmethod
    def get_taskshortname(cls):
        return "HADS"

    @classmethod
    def get_tasklongname(cls):
        return "Hospital Anxiety and Depression Scale (data collection only)"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + cls.TASK_FIELDSPECS

    def is_complete(self):
        return self.field_contents_valid() and self.are_all_fields_complete(
            repeat_fieldname("q", 1, self.NQUESTIONS))

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.anxiety_score(),
                "plot_label": "HADS anxiety score",
                "axis_label": "Anxiety score (out of 21)",
                "axis_min": -0.5,
                "axis_max": 21.5,
            },
            {
                "value": self.depression_score(),
                "plot_label": "HADS depression score",
                "axis_label": "Depression score (out of 21)",
                "axis_min": -0.5,
                "axis_max": 21.5,
            },
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "anxiety score {}/21, depression score {}/21".format(
                       self.anxiety_score(), self.depression_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="anxiety", cctype="INT",
                 value=self.anxiety_score(), comment="Anxiety score (/21)"),
            dict(name="depression", cctype="INT",
                 value=self.depression_score(),
                 comment="Depression score (/21)"),
        ]

    def score(self, questions):
        score = 0
        for q in questions:
            value = getattr(self, "q" + str(q))
            if value is not None:
                score += value
        return score

    def anxiety_score(self):
        return self.score(self.ANXIETY_QUESTIONS)

    def depression_score(self):
        return self.score(self.DEPRESSION_QUESTIONS)

    def get_task_html(self):
        MIN_SCORE = 0
        MAX_SCORE = 3
        crippled = not task_extrastrings_exist(self.EXTRASTRING_TASKNAME)
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
                    WXSTRING(self.EXTRASTRING_TASKNAME, "q" + str(n) + "_stem")
                )
            if n in self.ANXIETY_QUESTIONS:
                q += " (A)"
            if n in self.DEPRESSION_QUESTIONS:
                q += " (D)"
            v = getattr(self, "q" + str(n))
            if crippled or v is None or v < MIN_SCORE or v > MAX_SCORE:
                a = v
            else:
                a = "{}: {}".format(v, WXSTRING(self.EXTRASTRING_TASKNAME,
                                                "q{}_a{}".format(n, v)))
            h += tr_qa(q, a)
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
