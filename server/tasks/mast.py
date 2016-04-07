#!/usr/bin/env python3
# mast.py

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

from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
)
from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    get_yes_no,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# MAST
# =============================================================================

class Mast(Task):
    NQUESTIONS = 24

    tablename = "mast"
    shortname = "MAST"
    longname = "Michigan Alcohol Screening Test"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, "CHAR", pv=['Y', 'N'],
        comment_fmt="Q{n}: {s} (Y or N)",
        comment_strings=[
            "feel you are a normal drinker",
            "couldn't remember evening before",
            "relative worries/complains",
            "stop drinking after 1-2 drinks",
            "feel guilty",
            "friends/relatives think you are a normal drinker",
            "can stop drinking when you want",
            "attended Alcoholics Anonymous",
            "physical fights",
            "drinking caused problems with relatives",
            "family have sought help",
            "lost friends",
            "trouble at work/school",
            "lost job",
            "neglected obligations for >=2 days",
            "drink before noon often",
            "liver trouble",
            "delirium tremens",
            "sought help",
            "hospitalized",
            "psychiatry admission",
            "clinic visit or professional help",
            "arrested for drink-driving",
            "arrested for other drunk behaviour",
        ]
    )

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "MAST total score",
                "axis_label": "Total score (out of 53)",
                "axis_min": -0.5,
                "axis_max": 53.5,
                "horizontal_lines": [
                    12.5
                ],
                "horizontal_labels": [
                    (13, "Ross threshold", "bottom"),
                ]
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "MAST total score {}/53".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/53)"),
            dict(name="exceeds_threshold", cctype="BOOL",
                 value=self.exceeds_ross_threshold(),
                 comment="Exceeds Ross threshold (total score >= 13)"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def get_score(self, q):
        yes = "Y"
        value = getattr(self, "q" + str(q))
        if value is None:
            return 0
        if q == 1 or q == 4 or q == 6 or q == 7:
            presence = 0 if value == yes else 1
        else:
            presence = 1 if value == yes else 0
        if q == 3 or q == 5 or q == 9 or q == 16:
            points = 1
        elif q == 8 or q == 19 or q == 20:
            points = 5
        else:
            points = 2
        return points * presence

    def total_score(self):
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            total += self.get_score(q)
        return total

    def exceeds_ross_threshold(self):
        score = self.total_score()
        return score >= 13

    def get_task_html(self):
        score = self.total_score()
        exceeds_threshold = self.exceeds_ross_threshold()
        MAIN_DICT = {
            None: None,
            "Y": WSTRING("Yes"),
            "N": WSTRING("No")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 53")
        h += tr_qa(WSTRING("mast_exceeds_threshold"),
                   get_yes_no(exceeds_threshold))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """
        for q in range(1, self.NQUESTIONS + 1):
            h += tr(
                WSTRING("mast_q" + str(q)),
                (
                    answer(get_from_dict(MAIN_DICT,
                                         getattr(self, "q" + str(q)))) +
                    answer(" — " + str(self.get_score(q)))
                )
            )
        h += """
            </table>
        """
        return h
