#!/usr/bin/env python
# camcops_server/tasks/honos.py

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

from typing import List, Optional

from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    subheading_spanning_two_columns,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


PV_MAIN = [0, 1, 2, 3, 4, 9]
PV_PROBLEMTYPE = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']


# =============================================================================
# HoNOS
# =============================================================================

class Honos(Task):
    NQUESTIONS = 12

    tablename = "honos"
    shortname = "HoNOS"
    longname = "Health of the Nation Outcome Scales, working age adults"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, pv=PV_MAIN,
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

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="HoNOS total score",
            axis_label="Total score (out of 48)",
            axis_min=-0.5,
            axis_max=48.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="HoNOS total score {}/48".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/48)"),
        ]

    def is_complete(self) -> bool:
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

    def total_score(self) -> int:
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            value = getattr(self, "q" + str(q))
            if value is not None and 0 <= value <= 4:
                # i.e. ignore null values and 9 (= not known)
                total += value
        return total

    def get_q(self, q: int) -> str:
        return self.wxstring("q" + str(q) + "_s")

    def get_answer(self, q: int, a: int) -> Optional[str]:
        if a == 9:
            return self.wxstring("option9")
        if a is None or a < 0 or a > 4:
            return None
        return self.wxstring("q" + str(q) + "_option" + str(a))

    def get_task_html(self) -> str:
        q8_problem_type_dict = {
            None: None,
            "A": self.wxstring("q8problemtype_option_a"),
            "B": self.wxstring("q8problemtype_option_b"),
            "C": self.wxstring("q8problemtype_option_c"),
            "D": self.wxstring("q8problemtype_option_d"),
            "E": self.wxstring("q8problemtype_option_e"),
            "F": self.wxstring("q8problemtype_option_f"),
            "G": self.wxstring("q8problemtype_option_g"),
            "H": self.wxstring("q8problemtype_option_h"),
            "I": self.wxstring("q8problemtype_option_i"),
            "J": self.wxstring("q8problemtype_option_j"),
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(wappstring("total_score"),
                answer(self.total_score()) + " / 48")
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                </tr>
        """
        h += tr_qa(self.wxstring("period_rated"), self.period_rated)
        for i in range(1, 8 + 1):
            h += tr_qa(
                self.get_q(i),
                self.get_answer(i, getattr(self, "q" + str(i)))
            )
        h += tr_qa(self.wxstring("q8problemtype_s"),
                   get_from_dict(q8_problem_type_dict, self.q8problemtype))
        h += tr_qa(self.wxstring("q8otherproblem_s"),
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
        "q", 1, NQUESTIONS, pv=PV_MAIN,
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

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="HoNOS-65+ total score",
            axis_label="Total score (out of 48)",
            axis_min=-0.5,
            axis_max=48.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="HoNOS-65+ total score {}/48".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/48)"),
        ]

    def is_complete(self) -> bool:
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

    def total_score(self) -> int:
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            value = getattr(self, "q" + str(q))
            if value is not None and 0 <= value <= 4:
                # i.e. ignore null values and 9 (= not known)
                total += value
        return total

    def get_q(self, q: int) -> str:
        return self.wxstring("q" + str(q) + "_s")

    def get_answer(self, q: int, a: int) -> str:
        if a == 9:
            return self.wxstring("option9")
        if a is None or a < 0 or a > 4:
            return None
        return self.wxstring("q" + str(q) + "_option" + str(a))

    def get_task_html(self) -> str:
        q8_problem_type_dict = {
            None: None,
            "A": self.wxstring("q8problemtype_option_a"),
            "B": self.wxstring("q8problemtype_option_b"),
            "C": self.wxstring("q8problemtype_option_c"),
            "D": self.wxstring("q8problemtype_option_d"),
            "E": self.wxstring("q8problemtype_option_e"),
            "F": self.wxstring("q8problemtype_option_f"),
            "G": self.wxstring("q8problemtype_option_g"),
            "H": self.wxstring("q8problemtype_option_h"),
            "I": self.wxstring("q8problemtype_option_i"),
            "J": self.wxstring("q8problemtype_option_j"),
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(wappstring("total_score"),
                answer(self.total_score()) + " / 48")
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                </tr>
        """
        h += tr_qa(self.wxstring("period_rated"), self.period_rated)
        for i in range(1, 8 + 1):
            h += tr_qa(
                self.get_q(i),
                self.get_answer(i, getattr(self, "q" + str(i)))
            )
        h += tr_qa(self.wxstring("q8problemtype_s"),
                   get_from_dict(q8_problem_type_dict, self.q8problemtype))
        h += tr_qa(self.wxstring("q8otherproblem_s"),
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
        "q", 1, NQUESTIONS, pv=PV_MAIN,
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

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="HoNOSCA total score",
            axis_label="Total score (out of 60)",
            axis_min=-0.5,
            axis_max=60.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="HoNOSCA total score {}/60".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/60)"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            value = getattr(self, "q" + str(q))
            if value is not None and 0 <= value <= 4:
                # i.e. ignore null values and 9 (= not known)
                total += value
        return total

    def get_q(self, q: int) -> str:
        return self.wxstring("q" + str(q) + "_s")

    def get_answer(self, q: int, a: int) -> str:
        if a == 9:
            return self.wxstring("option9")
        if a is None or a < 0 or a > 4:
            return None
        return self.wxstring("q" + str(q) + "_option" + str(a))

    def get_task_html(self) -> str:
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(wappstring("total_score"),
                answer(self.total_score()) + " / 60")
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                </tr>
        """
        h += tr_qa(self.wxstring("period_rated"), self.period_rated)
        h += subheading_spanning_two_columns(
            self.wxstring("section_a_title"))
        for i in range(1, 13 + 1):
            h += tr_qa(
                self.get_q(i),
                self.get_answer(i, getattr(self, "q" + str(i)))
            )
        h += subheading_spanning_two_columns(
            self.wxstring("section_b_title"))
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
