#!/usr/bin/env python3
# fab.py

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

from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import get_yes_no
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    CLINICIAN_FIELDSPECS,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# FAB
# =============================================================================

class Fab(Task):
    NQUESTIONS = 6
    TASK_FIELDSPECS = repeat_fieldspec("q", 1, NQUESTIONS)
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "fab"

    @classmethod
    def get_taskshortname(cls):
        return "FAB"

    @classmethod
    def get_tasklongname(cls):
        return "Frontal Assessment Battery"

    @classmethod
    def get_fieldspecs(cls):
        return (STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS +
                Fab.TASK_FIELDSPECS)

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "FAB total score",
                "axis_label": "Total score (out of 18)",
                "axis_min": -0.5,
                "axis_max": 30.5,
                "horizontal_lines": [
                    12.5,
                ],
                "horizontal_labels": [
                    (11, "suggests frontal dysfunction"),
                ]
            }
        ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score"),
        ]

    def is_complete(self):
        return self.are_all_fields_complete(Fab.TASK_FIELDS)

    def total_score(self):
        return self.sum_fields(Fab.TASK_FIELDS)

    def get_task_html(self):
        score = self.total_score()
        below_cutoff = score <= 12
        ANSWER_DICTS = []
        for q in range(1, Fab.NQUESTIONS + 1):
            d = {None: "?"}
            for option in range(0, 5):
                d[option] = (
                    str(option) + u" — " +
                    WSTRING("fab_q" + str(q) + "_option" + str(option)))
            ANSWER_DICTS.append(d)
        h = self.get_standard_clinician_block() + u"""
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 18</td></tr>
                    <tr><td>{} <sup>[1]</sup></td><td><b>{}</b></td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="40%">Question</th>
                    <th width="60%">Score</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score,
            WSTRING("fab_below_cutoff"), get_yes_no(below_cutoff),
        )
        for q in range(1, Fab.NQUESTIONS + 1):
            h += u"""<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("fab_q" + str(q) + "_title"),
                get_from_dict(ANSWER_DICTS[q - 1], getattr(self, "q" + str(q)))
            )
        h += u"""
            </table>
            <div class="footnotes">
                [1] Cutoff is &le;12.
                In patients with early dementia (MMSE > 24), a cutoff score of
                FAB &le;12 (*) can differentiate frontotemporal dementia from
                Alzheimer's disease (sensitivity for FTD 77%, specificy 87%;
                Slachevksy et al. 2004, PubMed ID 15262742).
                (*) I think: the phrase is "a cutoff of 12", which is somewhat
                ambiguous!
            </div>
        """
        return h
