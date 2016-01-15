#!/usr/bin/env python3
# gmcpq.py

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

import pythonlib.rnc_web as ws
from cc_modules.cc_constants import (
    PV,
    STANDARD_ANONYMOUS_TASK_FIELDSPECS,
)
from cc_modules.cc_html import (
    get_yes_no_none,
    subheading_spanning_two_columns,
    td,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# GMCPQ
# =============================================================================

class GMCPQ(Task):

    @classmethod
    def get_tablename(cls):
        return "gmcpq"

    @classmethod
    def get_taskshortname(cls):
        return "GMC-PQ"

    @classmethod
    def get_tasklongname(cls):
        return "GMC Patient Questionnaire"

    @classmethod
    def get_fieldspecs(cls):
        RATING_TEXT = " (1 poor - 5 very good, 0 does not apply)"
        AGREE_TEXT = (
            " (1 strongly disagree - 5 strongly agree, 0 does not apply)"
        )
        return STANDARD_ANONYMOUS_TASK_FIELDSPECS + [
            dict(name="doctor", cctype="TEXT",
                 comment="Doctor's name"),
            dict(name="q1", cctype="INT", min=1, max=4,
                 comment="Filling in questionnaire for... (1 yourself, "
                 "2 child, 3 spouse/partner, 4 other relative/friend)"),
            dict(name="q2a", cctype="INT", pv=PV.BIT,
                 comment="Reason: advice? (0 no, 1 yes)"),
            dict(name="q2b", cctype="INT", pv=PV.BIT,
                 comment="Reason: one-off problem? (0 no, 1 yes)"),
            dict(name="q2c", cctype="INT", pv=PV.BIT,
                 comment="Reason: ongoing problem? (0 no, 1 yes)"),
            dict(name="q2d", cctype="INT", pv=PV.BIT,
                 comment="Reason: routine check? (0 no, 1 yes)"),
            dict(name="q2e", cctype="INT", pv=PV.BIT,
                 comment="Reason: treatment? (0 no, 1 yes)"),
            dict(name="q2f", cctype="INT", pv=PV.BIT,
                 comment="Reason: other? (0 no, 1 yes)"),
            dict(name="q2f_details", cctype="TEXT",
                 comment="Reason, other, details"),
            dict(name="q3", cctype="INT", min=1, max=5,
                 comment="How important to health/wellbeing was the reason "
                 "(1 not very - 5 very)"),
            dict(name="q4a", cctype="INT", min=0, max=5,
                 comment="How good: being polite" + RATING_TEXT),
            dict(name="q4b", cctype="INT", min=0, max=5,
                 comment="How good: making you feel at ease" + RATING_TEXT),
            dict(name="q4c", cctype="INT", min=0, max=5,
                 comment="How good: listening" + RATING_TEXT),
            dict(name="q4d", cctype="INT", min=0, max=5,
                 comment="How good: assessing medical condition" +
                 RATING_TEXT),
            dict(name="q4e", cctype="INT", min=0, max=5,
                 comment="How good: explaining" + RATING_TEXT),
            dict(name="q4f", cctype="INT", min=0, max=5,
                 comment="How good: involving you in decisions" + RATING_TEXT),
            dict(name="q4g", cctype="INT", min=0, max=5,
                 comment="How good: providing/arranging treatment" +
                 RATING_TEXT),
            dict(name="q5a", cctype="INT", min=0, max=5,
                 comment="Agree/disagree: will keep info confidential" +
                 AGREE_TEXT),
            dict(name="q5b", cctype="INT", min=0, max=5,
                 comment="Agree/disagree: honest/trustworthy" + AGREE_TEXT),
            dict(name="q6", cctype="INT", pv=PV.BIT,
                 comment="Confident in doctor's ability to provide care "
                 "(0 no, 1 yes)"),
            dict(name="q7", cctype="INT", pv=PV.BIT,
                 comment="Would be completely happy to see this doctor again "
                 "(0 no, 1 yes)"),
            dict(name="q8", cctype="INT", pv=PV.BIT,
                 comment="Was this visit with your usual doctor "
                 "(0 no, 1 yes)"),
            dict(name="q9", cctype="TEXT",
                 comments="Other comments"),
            dict(name="q10", cctype="TEXT", pv=["M", "F"],
                 comment="Sex of rater (M, F)"),
            dict(name="q11", cctype="INT", min=1, max=5,
                 comment="Age (1 = under 15, 2 = 15-20, 3 = 21-40, "
                 "4 = 40-60, 5 = 60 or over"),  # yes, I know it's daft
            dict(name="q12", cctype="INT", min=1, max=16,
                 comment="Ethnicity (1 = White British, 2 = White Irish, "
                 "3 = White other, 4 = Mixed W/B Caribbean, "
                 "5 = Mixed W/B African, 6 = Mixed W/Asian, 7 = Mixed other, "
                 "8 = Asian/Asian British - Indian, 9 = A/AB - Pakistani, "
                 "10 = A/AB - Bangladeshi, 11 = A/AB - other, "
                 "12 = Black/Black British - Caribbean, 13 = B/BB - African, "
                 "14 = B/BB - other, 15 = Chinese, 16 = other)"),
            dict(name="q12_details", cctype="TEXT",
                 comment="Ethnic group, other, details"),
        ]

    @classmethod
    def is_anonymous(cls):
        return True

    def is_complete(self):
        return (
            self.is_field_complete("q1")
            and self.is_field_complete("q3")
            and self.is_field_complete("q4a")
            and self.is_field_complete("q4b")
            and self.is_field_complete("q4c")
            and self.is_field_complete("q4d")
            and self.is_field_complete("q4e")
            and self.is_field_complete("q4f")
            and self.is_field_complete("q4g")
            and self.is_field_complete("q5a")
            and self.is_field_complete("q5b")
            and self.is_field_complete("q6")
            and self.is_field_complete("q7")
            and self.is_field_complete("q8")
            and self.field_contents_valid()
        )

    def get_task_html(self):
        DICTQ1 = {None: None}
        DICTQ3 = {None: None}
        DICTQ4 = {None: None}
        DICTQ5 = {None: None}
        DICTQ11 = {None: None}
        DICTQ12 = {None: None}
        for option in range(1, 5):
            DICTQ1[option] = WSTRING("gmcpq_q1_option" + str(option))
        for option in range(1, 6):
            DICTQ3[option] = WSTRING("gmcpq_q3_option" + str(option))
            DICTQ11[option] = WSTRING("gmcpq_q11_option" + str(option))
        for option in range(0, 6):
            prefix = str(option) + " – " if option > 0 else ""
            DICTQ4[option] = prefix + WSTRING("gmcpq_q4_option" + str(option))
            DICTQ5[option] = prefix + WSTRING("gmcpq_q5_option" + str(option))
        for option in range(1, 17):
            DICTQ12[option] = WSTRING("gmcpq_ethnicity_option" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
        """.format(self.get_is_complete_tr())
        ell = "&hellip; "  # horizontal ellipsis
        sep_row = subheading_spanning_two_columns("")
        blank_cell = td("", td_class="subheading")
        h += tr_qa(WSTRING("gmcpq_q_doctor"), ws.webify(self.doctor))
        h += sep_row
        h += tr_qa(WSTRING("gmcpq_q1"), get_from_dict(DICTQ1, self.q1))
        h += tr(td(WSTRING("gmcpq_q2")), blank_cell, literal=True)
        h += tr_qa(ell + WSTRING("gmcpq_q2_a"), get_yes_no_none(self.q2a))
        h += tr_qa(ell + WSTRING("gmcpq_q2_b"), get_yes_no_none(self.q2b))
        h += tr_qa(ell + WSTRING("gmcpq_q2_c"), get_yes_no_none(self.q2c))
        h += tr_qa(ell + WSTRING("gmcpq_q2_d"), get_yes_no_none(self.q2d))
        h += tr_qa(ell + WSTRING("gmcpq_q2_e"), get_yes_no_none(self.q2e))
        h += tr_qa(ell + WSTRING("gmcpq_q2_f"), get_yes_no_none(self.q2f))
        h += tr_qa(ell + ell + WSTRING("gmcpq_q2f_s"),
                   ws.webify(self.q2f_details))
        h += tr_qa(WSTRING("gmcpq_q3"), get_from_dict(DICTQ3, self.q3))
        h += tr(td(WSTRING("gmcpq_q4")), blank_cell, literal=True)
        h += tr_qa(ell + WSTRING("gmcpq_q4_a"),
                   get_from_dict(DICTQ4, self.q4a))
        h += tr_qa(ell + WSTRING("gmcpq_q4_b"),
                   get_from_dict(DICTQ4, self.q4b))
        h += tr_qa(ell + WSTRING("gmcpq_q4_c"),
                   get_from_dict(DICTQ4, self.q4c))
        h += tr_qa(ell + WSTRING("gmcpq_q4_d"),
                   get_from_dict(DICTQ4, self.q4d))
        h += tr_qa(ell + WSTRING("gmcpq_q4_e"),
                   get_from_dict(DICTQ4, self.q4e))
        h += tr_qa(ell + WSTRING("gmcpq_q4_f"),
                   get_from_dict(DICTQ4, self.q4f))
        h += tr_qa(ell + WSTRING("gmcpq_q4_g"),
                   get_from_dict(DICTQ4, self.q4g))
        h += tr(td(WSTRING("gmcpq_q5")), blank_cell, literal=True)
        h += tr_qa(ell + WSTRING("gmcpq_q5_a"),
                   get_from_dict(DICTQ5, self.q5a))
        h += tr_qa(ell + WSTRING("gmcpq_q5_b"),
                   get_from_dict(DICTQ5, self.q5b))
        h += tr_qa(WSTRING("gmcpq_q6"), get_yes_no_none(self.q6))
        h += tr_qa(WSTRING("gmcpq_q7"), get_yes_no_none(self.q7))
        h += tr_qa(WSTRING("gmcpq_q8"), get_yes_no_none(self.q8))
        h += tr_qa(WSTRING("gmcpq_q9_s"), ws.webify(self.q9))
        h += sep_row
        h += tr_qa(WSTRING("sex"), ws.webify(self.q10))
        h += tr_qa(WSTRING("gmcpq_q11"), get_from_dict(DICTQ11, self.q11))
        h += tr_qa(WSTRING("gmcpq_q12"), get_from_dict(DICTQ12, self.q12))
        h += tr_qa(ell + WSTRING("gmcpq_ethnicity_other_s"),
                   ws.webify(self.q12_details))
        h += """
            </table>
        """
        return h
