#!/usr/bin/env python
# gmcpq.py

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

import cardinal_pythonlib.rnc_web as ws
from ..cc_modules.cc_constants import PV
from ..cc_modules.cc_html import (
    get_yes_no_none,
    subheading_spanning_two_columns,
    td,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# GMCPQ
# =============================================================================

class GMCPQ(Task):
    RATING_TEXT = " (1 poor - 5 very good, 0 does not apply)"
    AGREE_TEXT = (
        " (1 strongly disagree - 5 strongly agree, 0 does not apply)"
    )

    tablename = "gmcpq"
    shortname = "GMC-PQ"
    longname = "GMC Patient Questionnaire"
    fieldspecs = [
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
    is_anonymous = True

    def is_complete(self) -> bool:
        return (
            self.is_field_complete("q1") and
            self.is_field_complete("q3") and
            self.is_field_complete("q4a") and
            self.is_field_complete("q4b") and
            self.is_field_complete("q4c") and
            self.is_field_complete("q4d") and
            self.is_field_complete("q4e") and
            self.is_field_complete("q4f") and
            self.is_field_complete("q4g") and
            self.is_field_complete("q5a") and
            self.is_field_complete("q5b") and
            self.is_field_complete("q6") and
            self.is_field_complete("q7") and
            self.is_field_complete("q8") and
            self.field_contents_valid()
        )

    def get_task_html(self) -> str:
        dict_q1 = {None: None}
        dict_q3 = {None: None}
        dict_q4 = {None: None}
        dict_q5 = {None: None}
        dict_q11 = {None: None}
        dict_q12 = {None: None}
        for option in range(1, 5):
            dict_q1[option] = self.wxstring("q1_option" + str(option))
        for option in range(1, 6):
            dict_q3[option] = self.wxstring("q3_option" + str(option))
            dict_q11[option] = self.wxstring("q11_option" + str(option))
        for option in range(0, 6):
            prefix = str(option) + " – " if option > 0 else ""
            dict_q4[option] = prefix + self.wxstring("q4_option" + str(option))
            dict_q5[option] = prefix + self.wxstring("q5_option" + str(option))
        for option in range(1, 17):
            dict_q12[option] = self.wxstring("ethnicity_option" + str(option))
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
        sep_row = subheading_spanning_two_columns("<br>")
        blank_cell = td("", td_class="subheading")
        h += tr_qa(self.wxstring("q_doctor"), ws.webify(self.doctor))
        h += sep_row
        h += tr_qa(self.wxstring("q1"), get_from_dict(dict_q1, self.q1))
        h += tr(td(self.wxstring("q2")), blank_cell, literal=True)
        h += tr_qa(ell + self.wxstring("q2_a"), get_yes_no_none(self.q2a),
                   default="")
        h += tr_qa(ell + self.wxstring("q2_b"), get_yes_no_none(self.q2b),
                   default="")
        h += tr_qa(ell + self.wxstring("q2_c"), get_yes_no_none(self.q2c),
                   default="")
        h += tr_qa(ell + self.wxstring("q2_d"), get_yes_no_none(self.q2d),
                   default="")
        h += tr_qa(ell + self.wxstring("q2_e"), get_yes_no_none(self.q2e),
                   default="")
        h += tr_qa(ell + self.wxstring("q2_f"), get_yes_no_none(self.q2f),
                   default="")
        h += tr_qa(ell + ell + self.wxstring("q2f_s"),
                   ws.webify(self.q2f_details))
        h += tr_qa(self.wxstring("q3"), get_from_dict(dict_q3, self.q3))
        h += tr(td(self.wxstring("q4")), blank_cell, literal=True)
        h += tr_qa(ell + self.wxstring("q4_a"),
                   get_from_dict(dict_q4, self.q4a))
        h += tr_qa(ell + self.wxstring("q4_b"),
                   get_from_dict(dict_q4, self.q4b))
        h += tr_qa(ell + self.wxstring("q4_c"),
                   get_from_dict(dict_q4, self.q4c))
        h += tr_qa(ell + self.wxstring("q4_d"),
                   get_from_dict(dict_q4, self.q4d))
        h += tr_qa(ell + self.wxstring("q4_e"),
                   get_from_dict(dict_q4, self.q4e))
        h += tr_qa(ell + self.wxstring("q4_f"),
                   get_from_dict(dict_q4, self.q4f))
        h += tr_qa(ell + self.wxstring("q4_g"),
                   get_from_dict(dict_q4, self.q4g))
        h += tr(td(self.wxstring("q5")), blank_cell, literal=True)
        h += tr_qa(ell + self.wxstring("q5_a"),
                   get_from_dict(dict_q5, self.q5a))
        h += tr_qa(ell + self.wxstring("q5_b"),
                   get_from_dict(dict_q5, self.q5b))
        h += tr_qa(self.wxstring("q6"), get_yes_no_none(self.q6))
        h += tr_qa(self.wxstring("q7"), get_yes_no_none(self.q7))
        h += tr_qa(self.wxstring("q8"), get_yes_no_none(self.q8))
        h += tr_qa(self.wxstring("q9_s"), ws.webify(self.q9))
        h += sep_row
        h += tr_qa(wappstring("sex"), ws.webify(self.q10))
        h += tr_qa(self.wxstring("q11"), get_from_dict(dict_q11, self.q11))
        h += tr_qa(self.wxstring("q12"), get_from_dict(dict_q12, self.q12))
        h += tr_qa(ell + self.wxstring("ethnicity_other_s"),
                   ws.webify(self.q12_details))
        h += """
            </table>
        """
        return h
