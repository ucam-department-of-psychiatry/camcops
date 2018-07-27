#!/usr/bin/env python
# camcops_server/tasks/cgisch.py

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

from typing import Any, Dict, List, Tuple, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import (
    subheading_spanning_two_columns,
    tr_qa,
    tr_span_col,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# CGI-SCH
# =============================================================================

QUESTION_FRAGMENTS = ["positive", "negative", "depressive", "cognitive",
                      "overall"]


class CgiSchMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['CgiSch'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "severity", 1, 5,
            minimum=1, maximum=7,
            comment_fmt="Severity Q{n}, {s} (1-7, higher worse)",
            comment_strings=QUESTION_FRAGMENTS
        )
        add_multiple_columns(
            cls, "change", 1, 5,
            pv=list(range(1, 7 + 1)) + [9],
            comment_fmt="Change Q{n}, {s} (1-7, higher worse, or 9 N/A)",
            comment_strings=QUESTION_FRAGMENTS
        )
        super().__init__(name, bases, classdict)


class CgiSch(TaskHasPatientMixin, TaskHasClinicianMixin, Task,
             metaclass=CgiSchMetaclass):
    __tablename__ = "cgisch"
    shortname = "CGI-SCH"
    longname = "Clinical Global Impression – Schizophrenia"
    provides_trackers = True

    TASK_FIELDS = strseq("severity", 1, 5) + strseq("change", 1, 5)

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        prefix = "CGI-SCH severity: "
        ylabel = "Score (1-7)"
        return [
            TrackerInfo(
                value=self.severity1,
                plot_label=prefix + "positive symptoms",
                axis_label=ylabel,
                axis_min=0.5,
                axis_max=7.5
            ),
            TrackerInfo(
                value=self.severity2,
                plot_label=prefix + "negative symptoms",
                axis_label=ylabel,
                axis_min=0.5,
                axis_max=7.5
            ),
            TrackerInfo(
                value=self.severity3,
                plot_label=prefix + "depressive symptoms",
                axis_label=ylabel,
                axis_min=0.5,
                axis_max=7.5
            ),
            TrackerInfo(
                value=self.severity4,
                plot_label=prefix + "cognitive symptoms",
                axis_label=ylabel,
                axis_min=0.5,
                axis_max=7.5
            ),
            TrackerInfo(
                value=self.severity5,
                plot_label=prefix + "overall severity",
                axis_label=ylabel,
                axis_min=0.5,
                axis_max=7.5
            ),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content=(
                "CGI-SCH. Severity: positive {}, negative {}, "
                "depressive {}, cognitive {}, overall {}. Change: "
                "positive {}, negative {}, depressive {}, "
                "cognitive {}, overall {}.".format(
                    self.severity1,
                    self.severity2,
                    self.severity3,
                    self.severity4,
                    self.severity5,
                    self.change1,
                    self.change2,
                    self.change3,
                    self.change4,
                    self.change5,
                )
            )
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields()

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        severity_dict = {
            None: None,
            1: self.wxstring(req, "i_option1"),
            2: self.wxstring(req, "i_option2"),
            3: self.wxstring(req, "i_option3"),
            4: self.wxstring(req, "i_option4"),
            5: self.wxstring(req, "i_option5"),
            6: self.wxstring(req, "i_option6"),
            7: self.wxstring(req, "i_option7"),
        }
        change_dict = {
            None: None,
            1: self.wxstring(req, "ii_option1"),
            2: self.wxstring(req, "ii_option2"),
            3: self.wxstring(req, "ii_option3"),
            4: self.wxstring(req, "ii_option4"),
            5: self.wxstring(req, "ii_option5"),
            6: self.wxstring(req, "ii_option6"),
            7: self.wxstring(req, "ii_option7"),
            9: self.wxstring(req, "ii_option9"),
        }
        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer <sup>[1]</sup></th>
                </tr>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req)
        )
        h += subheading_spanning_two_columns(self.wxstring(req, "i_title"))
        h += tr_span_col(self.wxstring(req, "i_question"), cols=2)
        h += tr_qa(self.wxstring(req, "q1"),
                   get_from_dict(severity_dict, self.severity1))
        h += tr_qa(self.wxstring(req, "q2"),
                   get_from_dict(severity_dict, self.severity2))
        h += tr_qa(self.wxstring(req, "q3"),
                   get_from_dict(severity_dict, self.severity3))
        h += tr_qa(self.wxstring(req, "q4"),
                   get_from_dict(severity_dict, self.severity4))
        h += tr_qa(self.wxstring(req, "q5"),
                   get_from_dict(severity_dict, self.severity5))
        h += subheading_spanning_two_columns(self.wxstring(req, "ii_title"))
        h += tr_span_col(self.wxstring(req, "ii_question"), cols=2)
        h += tr_qa(self.wxstring(req, "q1"),
                   get_from_dict(change_dict, self.change1))
        h += tr_qa(self.wxstring(req, "q2"),
                   get_from_dict(change_dict, self.change2))
        h += tr_qa(self.wxstring(req, "q3"),
                   get_from_dict(change_dict, self.change3))
        h += tr_qa(self.wxstring(req, "q4"),
                   get_from_dict(change_dict, self.change4))
        h += tr_qa(self.wxstring(req, "q5"),
                   get_from_dict(change_dict, self.change5))
        h += """
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] All questions are scored 1–7, or 9 (not applicable, for
                change questions).
                {postscript}
            </div>
        """.format(
            CssClass=CssClass,
            postscript=self.wxstring(req, "ii_postscript"),
        )
        return h
