#!/usr/bin/env python3
# sas.py

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
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# SAS
# =============================================================================

class Sas(Task):
    NQUESTIONS = 10
    TASK_FIELDSPECS = repeat_fieldspec("q", 1, NQUESTIONS)
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "sas"

    @classmethod
    def get_taskshortname(cls):
        return "SAS"

    @classmethod
    def get_tasklongname(cls):
        return u"Simpson–Angus Extrapyramidal Side Effects Scale"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + Sas.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "SAS total score",
                "axis_label": "Total score (out of 40)",
                "axis_min": -0.5,
                "axis_max": 40.5,
            }
        ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score"),
        ]

    def is_complete(self):
        return self.are_all_fields_complete(Sas.TASK_FIELDS)

    def total_score(self):
        return self.sum_fields(Sas.TASK_FIELDS)

    def get_task_html(self):
        score = self.total_score()
        ANSWER_DICTS = []
        for q in range(1, Sas.NQUESTIONS + 1):
            d = {None: "?"}
            for option in range(0, 5):
                d[option] = WSTRING("sas_q" + str(q) + "_option" + str(option))
            ANSWER_DICTS.append(d)
        h = u"""
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 40</td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="30%">Question</th>
                    <th width="70%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score
        )
        for q in range(1, Sas.NQUESTIONS + 1):
            h += u"""<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("sas_q" + str(q) + "_s"),
                get_from_dict(ANSWER_DICTS[q - 1], getattr(self, "q" + str(q)))
            )
        h += u"""
            </table>
        """
        return h
