#!/usr/bin/env python3
# pdss.py

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

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_constants import DATA_COLLECTION_UNLESS_UPGRADED_DIV
from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, tr
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task, TrackerInfo


# =============================================================================
# PDSS
# =============================================================================

DP = 3


class Pdss(Task):
    MIN_SCORE = 0
    MAX_SCORE = 4
    QUESTION_SNIPPETS = [
        "frequency",
        "distressing during",
        "anxiety about panic",
        "places or situations avoided",
        "activities avoided",
        "interference with responsibilities",
        "interference with social life",
    ]
    NQUESTIONS = 7

    tablename = "pdss"
    shortname = "PDSS"
    longname = "Panic Disorder Severity Scale"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        min=MIN_SCORE, max=MAX_SCORE,
        comment_strings=QUESTION_SNIPPETS
    )

    QUESTION_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="PDSS total score (lower is better)",
            axis_label="Total score (out of 28)",
            axis_min=-0.5,
            axis_max=28.5
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total_score", cctype="INT",
                 value=self.total_score(),
                 comment="Total score (/ 28)"),
            dict(name="composite_score", cctype="FLOAT",
                 value=self.composite_score(),
                 comment="Composite score (/ 4)"),
        ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        t = self.total_score()
        c = ws.number_to_dp(self.composite_score(), DP, default="?")
        return [CtvInfo(
            content="PDSS total score {t}/48 (composite {c}/4)".format(
                t=t, c=c)
        )]

    def total_score(self) -> int:
        return self.sum_fields(self.QUESTION_FIELDS)

    def composite_score(self) -> int:
        return self.mean_fields(self.QUESTION_FIELDS)

    def is_complete(self) -> bool:
        return (
            self.field_contents_valid() and
            self.are_all_fields_complete(self.QUESTION_FIELDS)
        )

    def get_task_html(self) -> str:
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score</td>
                        <td>{total} / 28</td>
                    </td>
                    <tr>
                        <td>Composite (mean) score</td>
                        <td>{composite} / 4</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer (0–4)</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(self.total_score()),
            composite=answer(ws.number_to_dp(self.composite_score(), DP,
                                             default="?")),
        )
        for q in range(1, self.NQUESTIONS + 1):
            qtext = self.WXSTRING("q" + str(q))
            a = getattr(self, "q" + str(q))
            atext = (self.WXSTRING("q{}_option{}".format(q, a), str(a))
                     if a is not None else None)
            h += tr(qtext, answer(atext))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
