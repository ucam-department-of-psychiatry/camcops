#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

from cc_db import repeat_fieldspec
from cc_html import (
    answer,
    tr,
    tr_qa,
)
from cc_string import WSTRING
from cc_task import (
    CTV_DICTLIST_INCOMPLETE,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# SMAST
# =============================================================================

class Smast(Task):
    NQUESTIONS = 13
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, "CHAR", pv=['Y', 'N'],
        comment_fmt="Q{n}: {s} (Y or N)",
        comment_strings=[
            "believe you are a normal drinker",
            "near relative worries/complains",
            "feel guilty",
            "friends/relative think you are a normal drinker",
            "stop when you want to",
            "ever attended Alcoholics Anonymous",
            "problems with close relative",
            "trouble at work",
            "neglected obligations for >=2 days",
            "sought help",
            "hospitalized",
            "arrested for drink-driving",
            "arrested for other drunken behaviour",
        ]
    )
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "smast"

    @classmethod
    def get_taskshortname(cls):
        return "SMAST"

    @classmethod
    def get_tasklongname(cls):
        return "Short Michigan Alcohol Screening Test"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + Smast.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "SMAST total score",
                "axis_label": "Total score (out of 13)",
                "axis_min": -0.5,
                "axis_max": 13.5,
                "horizontal_lines": [
                    2.5,
                    1.5,
                ],
                "horizontal_labels": [
                    (4, WSTRING("smast_problem_probable")),
                    (2, WSTRING("smast_problem_possible")),
                    (0.75, WSTRING("smast_problem_unlikely")),
                ]
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "SMAST total score {}/13 ({})".format(
                self.total_score(), self.likelihood())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/13)"),
            dict(name="likelihood", cctype="TEXT",
                 value=self.likelihood(),
                 comment="Likelihood of problem"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(Smast.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def get_score(self, q):
        yes = "Y"
        value = getattr(self, "q" + str(q))
        if value is None:
            return 0
        if q == 1 or q == 4 or q == 5:
            return 0 if value == yes else 1
        else:
            return 1 if value == yes else 0

    def total_score(self):
        total = 0
        for q in range(1, Smast.NQUESTIONS + 1):
            total += self.get_score(q)
        return total

    def likelihood(self):
        score = self.total_score()
        if score >= 3:
            return WSTRING("smast_problem_probable")
        elif score >= 2:
            return WSTRING("smast_problem_possible")
        else:
            return WSTRING("smast_problem_unlikely")

    def get_task_html(self):
        score = self.total_score()
        likelihood = self.likelihood()
        MAIN_DICT = {
            None: None,
            "Y": WSTRING("Yes"),
            "N": WSTRING("No")
        }
        h = u"""
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 13")
        h += tr_qa(WSTRING("smast_problem_likelihood") + " <sup>[1]</sup>",
                   likelihood)
        h += u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """
        for q in range(1, Smast.NQUESTIONS + 1):
            h += tr(
                WSTRING("smast_q" + str(q)),
                answer(get_from_dict(MAIN_DICT, getattr(self, "q" + str(q))))
                + u" — " + str(self.get_score(q))
            )
        h += u"""
            </table>
            <div class="footnotes">
                [1] Total score ≥3 probable, ≥2 possible, 0–1 unlikely.
            </div>
        """
        return h
