#!/usr/bin/env python3
# lshs.py

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
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task, TrackerInfo


# =============================================================================
# LSHS-A
# =============================================================================

class LshsA(Task):
    NQUESTIONS = 12

    tablename = "lshs_a"
    shortname = "LSHS-A"
    longname = "Launay–Slade Hallucination Scale, revision A"
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="LSHS-A total score",
            axis_label="Total score (out of 48)",
            axis_min=-0.5,
            axis_max=48.5
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
        answer_dict = {None: "?"}
        for option in range(0, 5):
            answer_dict[option] = (str(option) + " — " +
                                   WSTRING("lshs_a_option" + str(option)))
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 48</td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("lshs_a_q" + str(q) + "_question"),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )
        h += """
            </table>
        """
        return h


# =============================================================================
# LSHS-Laroi2005
# =============================================================================

class LshsLaroi2005(Task):
    NQUESTIONS = 16

    tablename = "lshs_laroi2005"
    shortname = "LSHS-Larøi"
    longname = (
        "Launay–Slade Hallucination Scale, revision of "
        "Larøi et al. (2005)"
    )
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self) -> str:
        score = self.total_score()
        answer_dict = {None: "?"}
        for option in range(0, 5):
            answer_dict[option] = (
                str(option) + " — " +
                WSTRING("lshs_laroi2005_option" + str(option)))
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 64</td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                "Q" + str(q) + " – " +
                WSTRING("lshs_laroi2005_q" + str(q) + "_question"),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )
        h += """
            </table>
        """
        return h
