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

from typing import List

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import get_yes_no
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task, TrackerInfo, TrackerLabel


# =============================================================================
# FAB
# =============================================================================

class Fab(Task):
    NQUESTIONS = 6

    tablename = "fab"
    shortname = "FAB"
    longname = "Frontal Assessment Battery"
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="FAB total score",
            axis_label="Total score (out of 18)",
            axis_min=-0.5,
            axis_max=30.5,
            horizontal_lines=[
                12.5,
            ],
            horizontal_labels=[
                TrackerLabel(11, "suggests frontal dysfunction"),
            ]
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score"),
        ]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self) -> str:
        score = self.total_score()
        below_cutoff = score <= 12
        answer_dicts = []
        for q in range(1, self.NQUESTIONS + 1):
            d = {None: "?"}
            for option in range(0, 5):
                d[option] = (
                    str(option) + " — " +
                    WSTRING("fab_q" + str(q) + "_option" + str(option)))
            answer_dicts.append(d)
        h = """
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
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("fab_q" + str(q) + "_title"),
                get_from_dict(answer_dicts[q - 1], getattr(self, "q" + str(q)))
            )
        h += """
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
