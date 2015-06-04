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

from cc_html import (
    answer,
    italic,
    tr,
    tr_qa,
)
from cc_string import WSTRING
from cc_task import (
    CTV_DICTLIST_INCOMPLETE,
    CLINICIAN_FIELDSPECS,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# CGI
# =============================================================================

class Cgi(Task):
    TASK_FIELDSPECS = [
        dict(name="q1", cctype="INT", min=0, max=7,
             comment="Q1. Severity (1-7, higher worse, 0 not assessed)"),
        dict(name="q2", cctype="INT", min=0, max=7,
             comment="Q2. Global improvement (1-7, higher worse, "
             "0 not assessed)"),
        dict(name="q3t", cctype="INT", min=0, max=4,
             comment="Q3T. Therapeutic effects (1-4, higher worse, "
             "0 not assessed)"),
        dict(name="q3s", cctype="INT", min=0, max=4,
             comment="Q3S. Side effects (1-4, higher worse, 0 not assessed)"),
        dict(name="q3", cctype="INT", min=0, max=16,
             comment="Q3 (calculated). Efficacy index [(Q3T - 1) * 4 + Q3S]."),
    ]
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "cgi"

    @classmethod
    def get_taskshortname(cls):
        return "CGI"

    @classmethod
    def get_tasklongname(cls):
        return "Clinical Global Impressions"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + \
            cls.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "CGI total score",
                "axis_label": "Total score (out of 30)",
                "axis_min": -0.5,
                "axis_max": 30.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "CGI total score {}/30".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score()),
        ]

    def is_complete(self):
        if not (self.are_all_fields_complete(self.TASK_FIELDS)
                and self.field_contents_valid()):
            return False
        if self.q1 == 0 or self.q2 == 0 or self.q3t == 0 or self.q3s == 0:
            return False
        return True

    def total_score(self):
        return self.sum_fields(["q1", "q2", "q3"])

    def get_task_html(self):
        Q1_DICT = {
            None: None,
            0: WSTRING("cgi_q1_option0"),
            1: WSTRING("cgi_q1_option1"),
            2: WSTRING("cgi_q1_option2"),
            3: WSTRING("cgi_q1_option3"),
            4: WSTRING("cgi_q1_option4"),
            5: WSTRING("cgi_q1_option5"),
            6: WSTRING("cgi_q1_option6"),
            7: WSTRING("cgi_q1_option7"),
        }
        Q2_DICT = {
            None: None,
            0: WSTRING("cgi_q2_option0"),
            1: WSTRING("cgi_q2_option1"),
            2: WSTRING("cgi_q2_option2"),
            3: WSTRING("cgi_q2_option3"),
            4: WSTRING("cgi_q2_option4"),
            5: WSTRING("cgi_q2_option5"),
            6: WSTRING("cgi_q2_option6"),
            7: WSTRING("cgi_q2_option7"),
        }
        Q3T_DICT = {
            None: None,
            0: WSTRING("cgi_q3t_option0"),
            1: WSTRING("cgi_q3t_option1"),
            2: WSTRING("cgi_q3t_option2"),
            3: WSTRING("cgi_q3t_option3"),
            4: WSTRING("cgi_q3t_option4"),
        }
        Q3S_DICT = {
            None: None,
            0: WSTRING("cgi_q3s_option0"),
            1: WSTRING("cgi_q3s_option1"),
            2: WSTRING("cgi_q3s_option2"),
            3: WSTRING("cgi_q3s_option3"),
            4: WSTRING("cgi_q3s_option4"),
        }
        h = self.get_standard_clinician_block() + u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr("Total score <sup>[1]</sup>", answer(self.total_score()))
        h += u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="30%">Question</th>
                    <th width="70%">Answer</th>
                </tr>
        """
        h += tr_qa(WSTRING("cgi_q1_s") + u" <sup>[2]</sup>",
                   get_from_dict(Q1_DICT, self.q1))
        h += tr_qa(WSTRING("cgi_q2_s") + u" <sup>[2]</sup>",
                   get_from_dict(Q2_DICT, self.q2))
        h += tr_qa(WSTRING("cgi_q3t_s") + u" <sup>[3]</sup>",
                   get_from_dict(Q3T_DICT, self.q3t))
        h += tr_qa(WSTRING("cgi_q3s_s") + u" <sup>[3]</sup>",
                   get_from_dict(Q3S_DICT, self.q3s))
        h += tr(
            u"""
                {} <sup>[4]</sup>
                <div class="smallprint">
                    [(Q3T – 1) × 4 + Q3S]
                </div>
            """.format(WSTRING("cgi_q3_s")),
            answer(self.q3, formatter_answer=italic)
        )
        h += u"""
            </table>
            <div class="footnotes">
                [1] Total score: Q1 + Q2 + Q3. Range 3–30 when complete.
                [2] Questions 1 and 2 are scored 1–7 (0 for not assessed).
                [3] Questions 3T and 3S are scored 1–4 (0 for not assessed).
                [4] Q3 is scored 1–16 if Q3T/Q3S complete.
            </div>
        """
        return h


# =============================================================================
# CGI-I
# =============================================================================

class CgiI(Task):
    TASK_FIELDSPECS = [
        dict(name="q", cctype="INT", min=0, max=7,
             comment="Global improvement (1-7, higher worse)"),
    ]
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "cgi_i"

    @classmethod
    def get_taskshortname(cls):
        return "CGI-I"

    @classmethod
    def get_tasklongname(cls):
        return u"Clinical Global Impressions – Improvement"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + \
            cls.TASK_FIELDSPECS

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "CGI-I rating: {}".format(self.get_rating_text())
        }]

    def is_complete(self):
        return (self.are_all_fields_complete(self.TASK_FIELDS)
                and self.field_contents_valid())

    def get_rating_text(self):
        qdict = self.get_q_dict()
        return get_from_dict(qdict, self.q)

    @staticmethod
    def get_q_dict():
        return {
            None: None,
            0: WSTRING("cgi_q2_option0"),
            1: WSTRING("cgi_q2_option1"),
            2: WSTRING("cgi_q2_option2"),
            3: WSTRING("cgi_q2_option3"),
            4: WSTRING("cgi_q2_option4"),
            5: WSTRING("cgi_q2_option5"),
            6: WSTRING("cgi_q2_option6"),
            7: WSTRING("cgi_q2_option7"),
        }

    def get_task_html(self):
        h = self.get_standard_clinician_block() + u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr() + u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        h += tr_qa(WSTRING("cgi_i_q"), self.get_rating_text())
        h += u"""
            </table>
        """
        return h
