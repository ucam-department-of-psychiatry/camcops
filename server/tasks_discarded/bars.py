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

from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    CLINICIAN_FIELDSPECS,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


#==============================================================================
# BARS
#==============================================================================

class Bars(Task):
    NQUESTIONS = 4
    TASK_FIELDSPECS = repeat_fieldspec("q", 1, NQUESTIONS)
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "bars"

    @classmethod
    def get_taskshortname(cls):
        return "BARS"

    @classmethod
    def get_tasklongname(cls):
        return "Barnes Akathisia Rating Scale"

    @classmethod
    def get_fieldspecs(cls):
        return (STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS +
                Bars.TASK_FIELDSPECS)

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "BARS total score",
                "axis_label": "Total score (out of 14)",
                "axis_min": -0.5,
                "axis_max": 14.5,
            }
        ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score"),
        ]

    def is_complete(self):
        return self.are_all_fields_complete(Bars.TASK_FIELDS)

    def total_score(self):
        return self.sum_fields(Bars.TASK_FIELDS)

    def get_task_html(self):
        score = self.total_score()
        ANSWER_DICTS_DICT = {}
        for q in Bars.TASK_FIELDS:
            d = {None: "?"}
            for option in range(0, 6):
                if option > 3 and q == "q4":
                    continue
                d[option] = WSTRING("bars_" + q + "_option" + str(option))
            ANSWER_DICTS_DICT[q] = d
        h = self.get_standard_clinician_block() + u"""
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 14</td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="35%">Question</th>
                    <th width="65%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score
        )
        for q in Bars.TASK_FIELDS:
            h += u"""<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("bars_" + q + "_s"),
                get_from_dict(ANSWER_DICTS_DICT[q], getattr(self, q))
            )
        h += u"""
            </table>
        """
        return h
