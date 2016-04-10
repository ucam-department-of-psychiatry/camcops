#!/usr/bin/env python3
# honos.py

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

from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
)
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    subheading_spanning_two_columns,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


PV_PROBLEMTYPE = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']


# =============================================================================
# HoNOS
# =============================================================================

class Honos(Task):
    NQUESTIONS = 12

    tablename = "honos"
    shortname = "HoNOS"
    longname = "Health of the Nation Outcome Scales, working age adults"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=4,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        comment_strings=[
            "overactive/aggressive/disruptive/agitated",
            "deliberate self-harm",
            "problem-drinking/drug-taking",
            "cognitive problems",
            "physical illness/disability",
            "hallucinations/delusions",
            "depressed mood",
            "other mental/behavioural problem",
            "relationship problems",
            "activities of daily living",
            "problems with living conditions",
            "occupation/activities",
        ]
    ) + [
        dict(name="period_rated", cctype="TEXT",
             comment="Period being rated"),
        dict(name="q8problemtype", cctype="CHAR", pv=PV_PROBLEMTYPE,
             comment="Q8: type of problem (A phobic; B anxiety; "
             "C obsessive-compulsive; D mental strain/tension; "
             "E dissociative; F somatoform; G eating; H sleep; "
             "I sexual; J other, specify)"),
        dict(name="q8otherproblem", cctype="TEXT",
             comment="Q8: other problem: specify"),
    ]
    has_clinician = True

    COPYRIGHT_DIV = """
        <div class="copyright">
            Health of the Nation Outcome Scales:
            Copyright © Royal College of Psychiatrists.
            Used here with permission.
        </div>
    """

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "HoNOS total score",
                "axis_label": "Total score (out of 48)",
                "axis_min": -0.5,
                "axis_max": 48.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "HoNOS total score {}/48".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/48)"),
        ]

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        if not self.are_all_fields_complete(
                repeat_fieldname("q", 1, self.NQUESTIONS)):
            return False
        if self.q8 != 0 and self.q8 != 9 and self.q8problemtype is None:
            return False
        if self.q8 != 0 and self.q8 != 9 and self.q8problemtype == "J" \
                and self.q8otherproblem is None:
            return False
        return self.period_rated is not None

    def total_score(self):
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            value = getattr(self, "q" + str(q))
            if value is not None and 0 <= value <= 4:
                # i.e. ignore null values and 9 (= not known)
                total += value
        return total

    @staticmethod
    def get_q(q):
        return WSTRING("honos_q" + str(q) + "_s")

    @staticmethod
    def get_answer(q, a):
        if a == 9:
            return WSTRING("honos_option9")
        if a is None or a < 0 or a > 4:
            return None
        return WSTRING("honos_q" + str(q) + "_option" + str(a))

    def get_task_html(self):
        Q8PROBLEMTYPE_DICT = {
            None: None,
            "A": WSTRING("honos_q8problemtype_option_a"),
            "B": WSTRING("honos_q8problemtype_option_b"),
            "C": WSTRING("honos_q8problemtype_option_c"),
            "D": WSTRING("honos_q8problemtype_option_d"),
            "E": WSTRING("honos_q8problemtype_option_e"),
            "F": WSTRING("honos_q8problemtype_option_f"),
            "G": WSTRING("honos_q8problemtype_option_g"),
            "H": WSTRING("honos_q8problemtype_option_h"),
            "I": WSTRING("honos_q8problemtype_option_i"),
            "J": WSTRING("honos_q8problemtype_option_j"),
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(self.total_score()) + " / 48")
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                </tr>
        """
        h += tr_qa(WSTRING("honos_period_rated"), self.period_rated)
        for i in range(1, 8 + 1):
            h += tr_qa(
                self.get_q(i),
                self.get_answer(i, getattr(self, "q" + str(i)))
            )
        h += tr_qa(WSTRING("honos_q8problemtype_s"),
                   get_from_dict(Q8PROBLEMTYPE_DICT, self.q8problemtype))
        h += tr_qa(WSTRING("honos_q8otherproblem_s"),
                   self.q8otherproblem)
        for i in range(9, self.NQUESTIONS + 1):
            h += tr_qa(
                self.get_q(i),
                self.get_answer(i, getattr(self, "q" + str(i)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] 0 = no problem;
                1 = minor problem requiring no action;
                2 = mild problem but definitely present;
                3 = moderately severe problem;
                4 = severe to very severe problem;
                9 = not known.
            </div>
        """ + self.COPYRIGHT_DIV
        return h


# =============================================================================
# HoNOS 65+
# =============================================================================

class Honos65(Task):
    NQUESTIONS = 12

    tablename = "honos65"
    shortname = "HoNOS 65+"
    longname = "Health of the Nation Outcome Scales, older adults"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=4,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        comment_strings=[  # not exactly identical to HoNOS
            "behavioural disturbance",
            "deliberate self-harm",
            "problem drinking/drug-taking",
            "cognitive problems",
            "physical illness/disability",
            "hallucinations/delusions",
            "depressive symptoms",
            "other mental/behavioural problem",
            "relationship problems",
            "activities of daily living",
            "living conditions",
            "occupation/activities",
        ]
    ) + [
        dict(name="period_rated", cctype="TEXT",
             comment="Period being rated"),
        dict(name="q8problemtype", cctype="CHAR", pv=PV_PROBLEMTYPE,
             comment="Q8: type of problem (A phobic; B anxiety; "
             "C obsessive-compulsive; D stress; "  # NB slight difference (D)
             "E dissociative; F somatoform; G eating; H sleep; "
             "I sexual; J other, specify)"),
        dict(name="q8otherproblem", cctype="TEXT",
             comment="Q8: other problem: specify"),
    ]
    has_clinician = True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "HoNOS-65+ total score",
                "axis_label": "Total score (out of 48)",
                "axis_min": -0.5,
                "axis_max": 48.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "HoNOS-65+ total score {}/48".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/48)"),
        ]

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        if not self.are_all_fields_complete(
                repeat_fieldname("q", 1, self.NQUESTIONS)):
            return False
        if self.q8 != 0 and self.q8 != 9 and self.q8problemtype is None:
            return False
        if self.q8 != 0 and self.q8 != 9 and self.q8problemtype == "J" \
                and self.q8otherproblem is None:
            return False
        return self.period_rated is not None

    def total_score(self):
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            value = getattr(self, "q" + str(q))
            if value is not None and 0 <= value <= 4:
                # i.e. ignore null values and 9 (= not known)
                total += value
        return total

    @staticmethod
    def get_q(q):
        return WSTRING("honos65_q" + str(q) + "_s")

    @staticmethod
    def get_answer(q, a):
        if a == 9:
            return WSTRING("honos_option9")
        if a is None or a < 0 or a > 4:
            return None
        return WSTRING("honos65_q" + str(q) + "_option" + str(a))

    def get_task_html(self):
        Q8PROBLEMTYPE_DICT = {
            None: None,
            "A": WSTRING("honos65_q8problemtype_option_a"),
            "B": WSTRING("honos65_q8problemtype_option_b"),
            "C": WSTRING("honos65_q8problemtype_option_c"),
            "D": WSTRING("honos65_q8problemtype_option_d"),
            "E": WSTRING("honos65_q8problemtype_option_e"),
            "F": WSTRING("honos65_q8problemtype_option_f"),
            "G": WSTRING("honos65_q8problemtype_option_g"),
            "H": WSTRING("honos65_q8problemtype_option_h"),
            "I": WSTRING("honos65_q8problemtype_option_i"),
            "J": WSTRING("honos65_q8problemtype_option_j"),
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(self.total_score()) + " / 48")
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                </tr>
        """
        h += tr_qa(WSTRING("honos_period_rated"), self.period_rated)
        for i in range(1, 8 + 1):
            h += tr_qa(
                self.get_q(i),
                self.get_answer(i, getattr(self, "q" + str(i)))
            )
        h += tr_qa(WSTRING("honos65_q8problemtype_s"),
                   get_from_dict(Q8PROBLEMTYPE_DICT, self.q8problemtype))
        h += tr_qa(WSTRING("honos65_q8otherproblem_s"),
                   self.q8otherproblem)
        for i in range(9, Honos.NQUESTIONS + 1):
            h += tr_qa(
                self.get_q(i),
                self.get_answer(i, getattr(self, "q" + str(i)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] 0 = no problem;
                1 = minor problem requiring no action;
                2 = mild problem but definitely present;
                3 = moderately severe problem;
                4 = severe to very severe problem;
                9 = not known.
            </div>
        """ + Honos.COPYRIGHT_DIV
        return h


# =============================================================================
# HoNOSCA
# =============================================================================

class Honosca(Task):
    NQUESTIONS = 15

    tablename = "honosca"
    shortname = "HoNOSCA"
    longname = "Health of the Nation Outcome Scales, Children and Adolescents"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=4,
        comment_fmt="Q{n}, {s} (0-4, higher worse)",
        comment_strings=[
            "disruptive/antisocial/aggressive",
            "overactive/inattentive",
            "self-harm",
            "alcohol/drug misuse",
            "scholastic/language problems",
            "physical illness/disability",
            "delusions/hallucinations",
            "non-organic somatic symptoms",
            "emotional symptoms",
            "peer relationships",
            "self-care and independence",
            "family life/relationships",
            "school attendance",
            "problems with knowledge/understanding of child's problems",
            "lack of information about services",
        ]
    ) + [
        dict(name="period_rated", cctype="TEXT",
             comment="Period being rated"),
    ]
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "HoNOSCA total score",
                "axis_label": "Total score (out of 60)",
                "axis_min": -0.5,
                "axis_max": 60.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "HoNOSCA total score {}/60".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/60)"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self):
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            value = getattr(self, "q" + str(q))
            if value is not None and 0 <= value <= 4:
                # i.e. ignore null values and 9 (= not known)
                total += value
        return total

    @staticmethod
    def get_q(q):
        return WSTRING("honosca_q" + str(q) + "_s")

    @staticmethod
    def get_answer(q, a):
        if a == 9:
            return WSTRING("honos_option9")
        if a is None or a < 0 or a > 4:
            return None
        return WSTRING("honosca_q" + str(q) + "_option" + str(a))

    def get_task_html(self):
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(self.total_score()) + " / 60")
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                </tr>
        """
        h += tr_qa(WSTRING("honos_period_rated"), self.period_rated)
        h += subheading_spanning_two_columns(
            WSTRING("honosca_section_a_title"))
        for i in range(1, 13 + 1):
            h += tr_qa(
                self.get_q(i),
                self.get_answer(i, getattr(self, "q" + str(i)))
            )
        h += subheading_spanning_two_columns(
            WSTRING("honosca_section_b_title"))
        for i in range(14, self.NQUESTIONS + 1):
            h += tr_qa(
                self.get_q(i),
                self.get_answer(i, getattr(self, "q" + str(i)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] 0 = no problem;
                1 = minor problem requiring no action;
                2 = mild problem but definitely present;
                3 = moderately severe problem;
                4 = severe to very severe problem;
                9 = not known.
            </div>
        """ + Honos.COPYRIGHT_DIV
        return h
