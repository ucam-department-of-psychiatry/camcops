#!/usr/bin/env python
# camcops_server/tasks/cgi_task.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================
"""

from typing import Dict, List

from ..cc_modules.cc_html import (
    answer,
    italic,
    tr,
    tr_qa,
)
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


# =============================================================================
# CGI
# =============================================================================

class Cgi(Task):
    tablename = "cgi"
    shortname = "CGI"
    longname = "Clinical Global Impressions"
    has_clinician = True
    provides_trackers = True

    fieldspecs = [
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
    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="CGI total score",
            axis_label="Total score (out of 30)",
            axis_min=-0.5,
            axis_max=30.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="CGI total score {}/30".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score()),
        ]

    def is_complete(self) -> bool:
        if not (self.are_all_fields_complete(self.TASK_FIELDS) and
                self.field_contents_valid()):
            return False
        # Requirement for everything to be non-zero removed in v2.0.0
        # if self.q1 == 0 or self.q2 == 0 or self.q3t == 0 or self.q3s == 0:
        #     return False
        return True

    def total_score(self) -> int:
        return self.sum_fields(["q1", "q2", "q3"])

    def get_task_html(self) -> str:
        q1_dict = {
            None: None,
            0: self.wxstring("q1_option0"),
            1: self.wxstring("q1_option1"),
            2: self.wxstring("q1_option2"),
            3: self.wxstring("q1_option3"),
            4: self.wxstring("q1_option4"),
            5: self.wxstring("q1_option5"),
            6: self.wxstring("q1_option6"),
            7: self.wxstring("q1_option7"),
        }
        q2_dict = {
            None: None,
            0: self.wxstring("q2_option0"),
            1: self.wxstring("q2_option1"),
            2: self.wxstring("q2_option2"),
            3: self.wxstring("q2_option3"),
            4: self.wxstring("q2_option4"),
            5: self.wxstring("q2_option5"),
            6: self.wxstring("q2_option6"),
            7: self.wxstring("q2_option7"),
        }
        q3t_dict = {
            None: None,
            0: self.wxstring("q3t_option0"),
            1: self.wxstring("q3t_option1"),
            2: self.wxstring("q3t_option2"),
            3: self.wxstring("q3t_option3"),
            4: self.wxstring("q3t_option4"),
        }
        q3s_dict = {
            None: None,
            0: self.wxstring("q3s_option0"),
            1: self.wxstring("q3s_option1"),
            2: self.wxstring("q3s_option2"),
            3: self.wxstring("q3s_option3"),
            4: self.wxstring("q3s_option4"),
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr("Total score <sup>[1]</sup>", answer(self.total_score()))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="30%">Question</th>
                    <th width="70%">Answer</th>
                </tr>
        """
        h += tr_qa(self.wxstring("q1_s") + " <sup>[2]</sup>",
                   get_from_dict(q1_dict, self.q1))
        h += tr_qa(self.wxstring("q2_s") + " <sup>[2]</sup>",
                   get_from_dict(q2_dict, self.q2))
        h += tr_qa(self.wxstring("q3t_s") + " <sup>[3]</sup>",
                   get_from_dict(q3t_dict, self.q3t))
        h += tr_qa(self.wxstring("q3s_s") + " <sup>[3]</sup>",
                   get_from_dict(q3s_dict, self.q3s))
        h += tr(
            """
                {} <sup>[4]</sup>
                <div class="smallprint">
                    [(Q3T – 1) × 4 + Q3S]
                </div>
            """.format(self.wxstring("q3_s")),
            answer(self.q3, formatter_answer=italic)
        )
        h += """
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
    tablename = "cgi_i"
    shortname = "CGI-I"
    longname = "Clinical Global Impressions – Improvement"
    extrastring_taskname = "cgi"  # shares with CGI
    fieldspecs = [
        dict(name="q", cctype="INT", min=0, max=7,
             comment="Global improvement (1-7, higher worse)"),
    ]
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="CGI-I rating: {}".format(self.get_rating_text())
        )]

    def is_complete(self) -> bool:
        return (self.are_all_fields_complete(self.TASK_FIELDS) and
                self.field_contents_valid())

    def get_rating_text(self) -> str:
        qdict = self.get_q_dict()
        return get_from_dict(qdict, self.q)

    def get_q_dict(self) -> Dict:
        return {
            None: None,
            0: self.wxstring("q2_option0"),
            1: self.wxstring("q2_option1"),
            2: self.wxstring("q2_option2"),
            3: self.wxstring("q2_option3"),
            4: self.wxstring("q2_option4"),
            5: self.wxstring("q2_option5"),
            6: self.wxstring("q2_option6"),
            7: self.wxstring("q2_option7"),
        }

    def get_task_html(self) -> str:
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr() + """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        h += tr_qa(self.wxstring("i_q"), self.get_rating_text())
        h += """
            </table>
        """
        return h
