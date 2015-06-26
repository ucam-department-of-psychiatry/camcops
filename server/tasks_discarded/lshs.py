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
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


#==============================================================================
# LSHS-A
#==============================================================================

class LshsA(Task):
    NQUESTIONS = 12
    TASK_FIELDSPECS = repeat_fieldspec("q", 1, NQUESTIONS)
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "lshs_a"

    @classmethod
    def get_taskshortname(cls):
        return "LSHS-A"

    @classmethod
    def get_tasklongname(cls):
        return u"Launay–Slade Hallucination Scale, revision A"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + LshsA.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "LSHS-A total score",
                "axis_label": "Total score (out of 48)",
                "axis_min": -0.5,
                "axis_max": 48.5,
            }
        ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score"),
        ]

    def is_complete(self):
        return self.are_all_fields_complete(LshsA.TASK_FIELDS)

    def total_score(self):
        return self.sum_fields(LshsA.TASK_FIELDS)

    def get_task_html(self):
        score = self.total_score()
        ANSWER_DICT = {None: "?"}
        for option in range(0, 5):
            ANSWER_DICT[option] = (str(option) + u" — " +
                                   WSTRING("lshs_a_option" + str(option)))
        h = u"""
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
        for q in range(1, LshsA.NQUESTIONS + 1):
            h += u"""<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("lshs_a_q" + str(q) + "_question"),
                get_from_dict(ANSWER_DICT, getattr(self, "q" + str(q)))
            )
        h += u"""
            </table>
        """
        return h


#==============================================================================
# LSHS-Laroi2005
#==============================================================================

class LshsLaroi2005(Task):
    NQUESTIONS = 16
    TASK_FIELDSPECS = repeat_fieldspec("q", 1, NQUESTIONS)
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "lshs_laroi2005"

    @classmethod
    def get_taskshortname(cls):
        return u"LSHS-Larøi"

    @classmethod
    def get_tasklongname(cls):
        return (
            u"Launay–Slade Hallucination Scale, revision of "
            u"Larøi et al. (2005)"
        )

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + LshsLaroi2005.TASK_FIELDSPECS

    def is_complete(self):
        return self.are_all_fields_complete(LshsLaroi2005.TASK_FIELDS)

    def total_score(self):
        return self.sum_fields(LshsA.TASK_FIELDS)

    def get_task_html(self):
        score = self.total_score()
        ANSWER_DICT = {None: "?"}
        for option in range(0, 5):
            ANSWER_DICT[option] = (
                str(option) + u" — " +
                WSTRING("lshs_laroi2005_option" + str(option)))
        h = u"""
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
        for q in range(1, LshsLaroi2005.NQUESTIONS + 1):
            h += u"""<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                "Q" + str(q) + u" – " +
                WSTRING("lshs_laroi2005_q" + str(q) + "_question"),
                get_from_dict(ANSWER_DICT, getattr(self, "q" + str(q)))
            )
        h += u"""
            </table>
        """
        return h
