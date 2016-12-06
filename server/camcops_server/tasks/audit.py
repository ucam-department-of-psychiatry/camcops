#!/usr/bin/env python
# audit.py

"""
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
"""

from typing import List

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    get_yes_no,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


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

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="AUDIT total score",
            axis_label="Total score (out of 40)",
            axis_min=-0.5,
            axis_max=40.5,
            horizontal_lines=[7.5]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="AUDIT total score {}/40".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/40)"),
        ]

    def is_complete(self) -> bool:
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

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self) -> str:
        score = self.total_score()
        exceeds_cutoff = score >= 8
        q1_dict = {None: None}
        q2_dict = {None: None}
        q3_to_8_dict = {None: None}
        q9_to_10_dict = {None: None}
        for option in range(0, 5):
            q1_dict[option] = str(option) + " – " + \
                self.WXSTRING("q1_option" + str(option))
            q2_dict[option] = str(option) + " – " + \
                self.WXSTRING("q2_option" + str(option))
            q3_to_8_dict[option] = str(option) + " – " + \
                self.WXSTRING("q3to8_option" + str(option))
            if option != 1 and option != 3:
                q9_to_10_dict[option] = str(option) + " – " + \
                    self.WXSTRING("q9to10_option" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 40")
        h += tr_qa(self.WXSTRING("exceeds_standard_cutoff"),
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
        h += tr_qa(self.WXSTRING("q1_s"), get_from_dict(q1_dict, self.q1))
        h += tr_qa(self.WXSTRING("q2_s"), get_from_dict(q2_dict, self.q2))
        for q in range(3, 8 + 1):
            h += tr_qa(
                self.WXSTRING("q" + str(q) + "_s"),
                get_from_dict(q3_to_8_dict, getattr(self, "q" + str(q)))
            )
        h += tr_qa(self.WXSTRING("q9_s"),
                   get_from_dict(q9_to_10_dict, self.q9))
        h += tr_qa(self.WXSTRING("q10_s"),
                   get_from_dict(q9_to_10_dict, self.q10))
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

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="AUDIT-C total score",
            axis_label="Total score (out of 12)",
            axis_min=-0.5,
            axis_max=12.5,
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="AUDIT-C total score {}/12".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/12)"),
        ]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self) -> str:
        score = self.total_score()
        q1_dict = {None: None}
        q2_dict = {None: None}
        q3_dict = {None: None}
        for option in range(0, 5):
            q1_dict[option] = str(option) + " – " + \
                self.WXSTRING("q1_option" + str(option))
            if option == 0:  # special!
                q2_dict[option] = str(option) + " – " + \
                    self.WXSTRING("c_q2_option0")
            else:
                q2_dict[option] = str(option) + " – " + \
                    self.WXSTRING("q2_option" + str(option))
            q3_dict[option] = str(option) + " – " + \
                self.WXSTRING("q3to8_option" + str(option))
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
        h += tr_qa(self.WXSTRING("c_q1_question"),
                   get_from_dict(q1_dict, self.q1))
        h += tr_qa(self.WXSTRING("c_q2_question"),
                   get_from_dict(q2_dict, self.q2))
        h += tr_qa(self.WXSTRING("c_q3_question"),
                   get_from_dict(q3_dict, self.q3))
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
