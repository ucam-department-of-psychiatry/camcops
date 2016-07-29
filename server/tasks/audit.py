#!/usr/bin/env python3
# audit.py

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

from ..cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
)
from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    get_yes_no,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# AUDIT
# =============================================================================

class Audit(Task):
    NQUESTIONS = 10

    tablename = "audit"
    shortname = "AUDIT"
    longname = "WHO Alcohol Use Disorders Identification Test"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=4,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        comment_strings=[
            "how often drink", "drinks per day", "how often six drinks",
            "unable to stop", "unable to do what was expected", "eye opener",
            "guilt", "unable to remember", "injuries", "others concerned"])

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "AUDIT total score",
                "axis_label": "Total score (out of 40)",
                "axis_min": -0.5,
                "axis_max": 40.5,
                "horizontal_lines": [
                    7.5,
                ],
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "AUDIT total score {}/40".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/40)"),
        ]

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        if self.q1 is None or self.q9 is None or self.q10 is None:
            return False
        if self.q1 == 0:
            # Special limited-information completeness
            return True
        if self.q2 is not None \
                and self.q3 is not None \
                and (self.q2 + self.q3 == 0):
            # Special limited-information completeness
            return True
        # Otherwise, any null values cause problems
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self):
        return self.sum_fields(self.TASK_FIELDS)

    # noinspection PyPep8Naming
    def get_task_html(self):
        score = self.total_score()
        exceeds_cutoff = score >= 8
        Q1_DICT = {None: None}
        Q2_DICT = {None: None}
        Q3_TO_8_DICT = {None: None}
        Q9_TO_10_DICT = {None: None}
        for option in range(0, 5):
            Q1_DICT[option] = str(option) + " – " + \
                WSTRING("audit_q1_option" + str(option))
            Q2_DICT[option] = str(option) + " – " + \
                WSTRING("audit_q2_option" + str(option))
            Q3_TO_8_DICT[option] = str(option) + " – " + \
                WSTRING("audit_q3to8_option" + str(option))
            if option != 1 and option != 3:
                Q9_TO_10_DICT[option] = str(option) + " – " + \
                    WSTRING("audit_q9to10_option" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 40")
        h += tr_qa(WSTRING("audit_exceeds_standard_cutoff"),
                   get_yes_no(exceeds_cutoff))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        h += tr_qa(WSTRING("audit_q1_s"), get_from_dict(Q1_DICT, self.q1))
        h += tr_qa(WSTRING("audit_q2_s"), get_from_dict(Q2_DICT, self.q2))
        for q in range(3, 8 + 1):
            h += tr_qa(
                WSTRING("audit_q" + str(q) + "_s"),
                get_from_dict(Q3_TO_8_DICT, getattr(self, "q" + str(q)))
            )
        h += tr_qa(WSTRING("audit_q9_s"),
                   get_from_dict(Q9_TO_10_DICT, self.q9))
        h += tr_qa(WSTRING("audit_q10_s"),
                   get_from_dict(Q9_TO_10_DICT, self.q10))
        h += """
            </table>
            <div class="copyright">
                AUDIT: Copyright © World Health Organization.
                Reproduced here under the permissions granted for
                NON-COMMERCIAL use only. You must obtain permission from the
                copyright holder for any other use.
            </div>
        """
        return h


# =============================================================================
# AUDIT-C
# =============================================================================

class AuditC(Task):
    NQUESTIONS = 3

    tablename = "audit_c"
    shortname = "AUDIT-C"
    longname = "AUDIT Alcohol Consumption Questions"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=4,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        comment_strings=[
            "how often drink", "drinks per day", "how often six drinks"
        ]
    )

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "AUDIT-C total score",
                "axis_label": "Total score (out of 12)",
                "axis_min": -0.5,
                "axis_max": 12.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "AUDIT-C total score {}/12".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/12)"),
        ]

    def is_complete(self):
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self):
        return self.sum_fields(self.TASK_FIELDS)

    # noinspection PyPep8Naming
    def get_task_html(self):
        score = self.total_score()
        Q1_DICT = {None: None}
        Q2_DICT = {None: None}
        Q3_DICT = {None: None}
        for option in range(0, 5):
            Q1_DICT[option] = str(option) + " – " + \
                WSTRING("audit_q1_option" + str(option))
            if option == 0:  # special!
                Q2_DICT[option] = str(option) + " – " + \
                    WSTRING("audit_c_q2_option0")
            else:
                Q2_DICT[option] = str(option) + " – " + \
                    WSTRING("audit_q2_option" + str(option))
            Q3_DICT[option] = str(option) + " – " + \
                WSTRING("audit_q3to8_option" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 12")
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        h += tr_qa(WSTRING("audit_c_q1_question"),
                   get_from_dict(Q1_DICT, self.q1))
        h += tr_qa(WSTRING("audit_c_q2_question"),
                   get_from_dict(Q2_DICT, self.q2))
        h += tr_qa(WSTRING("audit_c_q3_question"),
                   get_from_dict(Q3_DICT, self.q3))
        h += """
            </table>
            <div class="copyright">
                AUDIT: Copyright © World Health Organization.
                Reproduced here under the permissions granted for
                NON-COMMERCIAL use only. You must obtain permission from the
                copyright holder for any other use.

                AUDIT-C: presumed to have the same restrictions.
            </div>
        """
        return h
