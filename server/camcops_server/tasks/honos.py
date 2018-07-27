#!/usr/bin/env python
# camcops_server/tasks/honos.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

from typing import Any, Dict, List, Optional, Tuple, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import (
    answer,
    subheading_spanning_two_columns,
    tr,
    tr_qa,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    CharColType,
    PermittedValueChecker,
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo


PV_MAIN = [0, 1, 2, 3, 4, 9]
PV_PROBLEMTYPE = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']

FOOTNOTE_SCORING = """
    [1] 0 = no problem;
    1 = minor problem requiring no action;
    2 = mild problem but definitely present;
    3 = moderately severe problem;
    4 = severe to very severe problem;
    9 = not known.
"""


# =============================================================================
# HoNOS abstract base class
# =============================================================================

# noinspection PyAbstractClass
class HonosBase(TaskHasPatientMixin, TaskHasClinicianMixin, Task):
    __abstract__ = True
    provides_trackers = True

    period_rated = Column(
        "period_rated", UnicodeText,
        comment="Period being rated"
    )

    COPYRIGHT_DIV = """
        <div class="{css_copyright}">
            Health of the Nation Outcome Scales:
            Copyright © Royal College of Psychiatrists.
            Used here with permission.
        </div>
    """.format(
        css_copyright=CssClass.COPYRIGHT,
    )

    QFIELDS = None  # type: List[str]  # must be overridden
    MAX_SCORE = None  # type: int  # must be overridden

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="{} total score".format(self.shortname),
            axis_label="Total score (out of {})".format(self.MAX_SCORE),
            axis_min=-0.5,
            axis_max=self.MAX_SCORE + 0.5
        )]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="{} total score {}/{}".format(
                self.shortname, self.total_score(), self.MAX_SCORE)
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(name="total",
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score (/{})".format(self.MAX_SCORE)),
        ]

    def total_score(self) -> int:
        total = 0
        for qname in self.QFIELDS:
            value = getattr(self, qname)
            if value is not None and 0 <= value <= 4:
                # i.e. ignore null values and 9 (= not known)
                total += value
        return total

    def get_q(self, req: CamcopsRequest, q: int) -> str:
        return self.wxstring(req, "q" + str(q) + "_s")

    def get_answer(self, req: CamcopsRequest, q: int, a: int) -> Optional[str]:
        if a == 9:
            return self.wxstring(req, "option9")
        if a is None or a < 0 or a > 4:
            return None
        return self.wxstring(req, "q" + str(q) + "_option" + str(a))


# =============================================================================
# HoNOS
# =============================================================================

class HonosMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Honos'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS,
            pv=PV_MAIN,
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
        )
        super().__init__(name, bases, classdict)


class Honos(HonosBase,
            metaclass=HonosMetaclass):
    __tablename__ = "honos"
    shortname = "HoNOS"
    longname = "Health of the Nation Outcome Scales, working age adults"

    q8problemtype = CamcopsColumn(
        "q8problemtype", CharColType,
        permitted_value_checker=PermittedValueChecker(
            permitted_values=PV_PROBLEMTYPE),
        comment="Q8: type of problem (A phobic; B anxiety; "
                "C obsessive-compulsive; D mental strain/tension; "
                "E dissociative; F somatoform; G eating; H sleep; "
                "I sexual; J other, specify)"
    )
    q8otherproblem = Column(
        "q8otherproblem", UnicodeText,
        comment="Q8: other problem: specify"
    )

    NQUESTIONS = 12
    QFIELDS = strseq("q", 1, NQUESTIONS)
    MAX_SCORE = 48

    def is_complete(self) -> bool:
        if not self.are_all_fields_complete(self.QFIELDS):
            return False
        if not self.field_contents_valid():
            return False
        if self.q8 != 0 and self.q8 != 9 and self.q8problemtype is None:
            return False
        if self.q8 != 0 and self.q8 != 9 and self.q8problemtype == "J" \
                and self.q8otherproblem is None:
            return False
        return self.period_rated is not None

    def get_task_html(self, req: CamcopsRequest) -> str:
        q8_problem_type_dict = {
            None: None,
            "A": self.wxstring(req, "q8problemtype_option_a"),
            "B": self.wxstring(req, "q8problemtype_option_b"),
            "C": self.wxstring(req, "q8problemtype_option_c"),
            "D": self.wxstring(req, "q8problemtype_option_d"),
            "E": self.wxstring(req, "q8problemtype_option_e"),
            "F": self.wxstring(req, "q8problemtype_option_f"),
            "G": self.wxstring(req, "q8problemtype_option_g"),
            "H": self.wxstring(req, "q8problemtype_option_h"),
            "I": self.wxstring(req, "q8problemtype_option_i"),
            "J": self.wxstring(req, "q8problemtype_option_j"),
        }
        one_to_eight = ""
        for i in range(1, 8 + 1):
            one_to_eight += tr_qa(
                self.get_q(req, i),
                self.get_answer(req, i, getattr(self, "q" + str(i)))
            )
        nine_onwards = ""
        for i in range(9, self.NQUESTIONS + 1):
            nine_onwards += tr_qa(
                self.get_q(req, i),
                self.get_answer(req, i, getattr(self, "q" + str(i)))
            )

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                </tr>
                {period_rated}
                {one_to_eight}
                {q8problemtype}
                {q8otherproblem}
                {nine_onwards}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                {FOOTNOTE_SCORING}
            </div>
            {copyright_div}
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.wappstring("total_score"),
                answer(self.total_score()) + " / {}".format(self.MAX_SCORE)
            ),
            period_rated=tr_qa(self.wxstring(req, "period_rated"),
                               self.period_rated),
            one_to_eight=one_to_eight,
            q8problemtype=tr_qa(
                self.wxstring(req, "q8problemtype_s"),
                get_from_dict(q8_problem_type_dict, self.q8problemtype)
            ),
            q8otherproblem=tr_qa(
                self.wxstring(req, "q8otherproblem_s"),
                self.q8otherproblem
            ),
            nine_onwards=nine_onwards,
            FOOTNOTE_SCORING=FOOTNOTE_SCORING,
            copyright_div=self.COPYRIGHT_DIV,
        )
        return h


# =============================================================================
# HoNOS 65+
# =============================================================================

class Honos65Metaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Honos65'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS,
            pv=PV_MAIN,
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
        )
        super().__init__(name, bases, classdict)


class Honos65(HonosBase,
              metaclass=Honos65Metaclass):
    __tablename__ = "honos65"
    shortname = "HoNOS 65+"
    longname = "Health of the Nation Outcome Scales, older adults"

    q8problemtype = CamcopsColumn(
        "q8problemtype", CharColType,
        permitted_value_checker=PermittedValueChecker(
            permitted_values=PV_PROBLEMTYPE),
        comment="Q8: type of problem (A phobic; B anxiety; "
                "C obsessive-compulsive; D stress; "  # NB slight difference: D
                "E dissociative; F somatoform; G eating; H sleep; "
                "I sexual; J other, specify)"
    )
    q8otherproblem = Column(
        "q8otherproblem", UnicodeText,
        comment="Q8: other problem: specify"
    )

    NQUESTIONS = 12
    QFIELDS = strseq("q", 1, NQUESTIONS)
    MAX_SCORE = 48

    def is_complete(self) -> bool:
        if not self.are_all_fields_complete(self.QFIELDS):
            return False
        if not self.field_contents_valid():
            return False
        if self.q8 != 0 and self.q8 != 9 and self.q8problemtype is None:
            return False
        if self.q8 != 0 and self.q8 != 9 and self.q8problemtype == "J" \
                and self.q8otherproblem is None:
            return False
        return self.period_rated is not None

    def get_task_html(self, req: CamcopsRequest) -> str:
        q8_problem_type_dict = {
            None: None,
            "A": self.wxstring(req, "q8problemtype_option_a"),
            "B": self.wxstring(req, "q8problemtype_option_b"),
            "C": self.wxstring(req, "q8problemtype_option_c"),
            "D": self.wxstring(req, "q8problemtype_option_d"),
            "E": self.wxstring(req, "q8problemtype_option_e"),
            "F": self.wxstring(req, "q8problemtype_option_f"),
            "G": self.wxstring(req, "q8problemtype_option_g"),
            "H": self.wxstring(req, "q8problemtype_option_h"),
            "I": self.wxstring(req, "q8problemtype_option_i"),
            "J": self.wxstring(req, "q8problemtype_option_j"),
        }
        one_to_eight = ""
        for i in range(1, 8 + 1):
            one_to_eight += tr_qa(
                self.get_q(req, i),
                self.get_answer(req, i, getattr(self, "q" + str(i)))
            )
        nine_onwards = ""
        for i in range(9, Honos.NQUESTIONS + 1):
            nine_onwards += tr_qa(
                self.get_q(req, i),
                self.get_answer(req, i, getattr(self, "q" + str(i)))
            )

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                </tr>
                {period_rated}
                {one_to_eight}
                {q8problemtype}
                {q8otherproblem}
                {nine_onwards}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                {FOOTNOTE_SCORING}
            </div>
            {copyright_div}
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.wappstring("total_score"),
                answer(self.total_score()) + " / {}".format(self.MAX_SCORE)
            ),
            period_rated=tr_qa(self.wxstring(req, "period_rated"),
                               self.period_rated),
            one_to_eight=one_to_eight,
            q8problemtype=tr_qa(
                self.wxstring(req, "q8problemtype_s"),
                get_from_dict(q8_problem_type_dict, self.q8problemtype)
            ),
            q8otherproblem=tr_qa(
                self.wxstring(req, "q8otherproblem_s"),
                self.q8otherproblem
            ),
            nine_onwards=nine_onwards,
            FOOTNOTE_SCORING=FOOTNOTE_SCORING,
            copyright_div=self.COPYRIGHT_DIV,
        )
        return h


# =============================================================================
# HoNOSCA
# =============================================================================

class HonoscaMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Honosca'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS,
            pv=PV_MAIN,
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
        )
        super().__init__(name, bases, classdict)


class Honosca(HonosBase,
              metaclass=HonoscaMetaclass):
    __tablename__ = "honosca"
    shortname = "HoNOSCA"
    longname = "Health of the Nation Outcome Scales, Children and Adolescents"

    NQUESTIONS = 15
    QFIELDS = strseq("q", 1, NQUESTIONS)
    MAX_SCORE = 60
    TASK_FIELDS = QFIELDS + ["period_rated"]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        section_a = ""
        for i in range(1, 13 + 1):
            section_a += tr_qa(
                self.get_q(req, i),
                self.get_answer(req, i, getattr(self, "q" + str(i)))
            )
        section_b = ""
        for i in range(14, self.NQUESTIONS + 1):
            section_b += tr_qa(
                self.get_q(req, i),
                self.get_answer(req, i, getattr(self, "q" + str(i)))
            )

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer <sup>[1]</sup></th>
                </tr>
                {period_rated}
                {section_a_subhead}
                {section_a}
                {section_b_subhead}
                {section_b}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                {FOOTNOTE_SCORING}
            </div>
            {copyright_div}
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.wappstring("total_score"),
                answer(self.total_score()) + " / {}".format(self.MAX_SCORE)
            ),
            period_rated=tr_qa(self.wxstring(req, "period_rated"),
                               self.period_rated),
            section_a_subhead=subheading_spanning_two_columns(
                self.wxstring(req, "section_a_title")),
            section_a=section_a,
            section_b_subhead=subheading_spanning_two_columns(
                self.wxstring(req, "section_b_title")),
            section_b=section_b,
            FOOTNOTE_SCORING=FOOTNOTE_SCORING,
            copyright_div=self.COPYRIGHT_DIV,
        )
        return h
