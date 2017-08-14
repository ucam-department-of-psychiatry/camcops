#!/usr/bin/env python
# camcops_server/tasks/icd10schizotypal.py

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

import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.sql.sqltypes import Boolean

from ..cc_modules.cc_constants import (
    DATEFORMAT,
    ICD10_COPYRIGHT_DIV,
    PV,
)
from ..cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_dt import format_datetime_string
from ..cc_modules.cc_html import (
    get_yes_no_none,
    td,
    tr,
    tr_qa,
)
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import Task


# =============================================================================
# Icd10Schizotypal
# =============================================================================

class Icd10Schizotypal(Task):
    tablename = "icd10schizotypal"
    shortname = "ICD10-SZTYP"
    longname = "ICD-10 criteria for schizotypal disorder (F21)"
    has_clinician = True

    N_A = 9
    fieldspecs = (
        [
            dict(name="date_pertains_to", cctype="ISO8601",
                 comment="Date the assessment pertains to"),
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
            dict(name="b", cctype="BOOL", pv=PV.BIT,
                 comment="Criterion (B). True if: the subject has never met "
                 "the criteria for any disorder in F20 (Schizophrenia)."),
        ] +
        repeat_fieldspec(
            "a", 1, N_A, "BOOL", pv=PV.BIT,
            comment_fmt="Criterion A({n}), {s}",
            comment_strings=[
                "inappropriate/constricted affect",
                "odd/eccentric/peculiar",
                "poor rapport/social withdrawal",
                "odd beliefs/magical thinking",
                "suspiciousness/paranoid ideas",
                "ruminations without inner resistance",
                "unusual perceptual experiences",
                "vague/circumstantial/metaphorical/over-elaborate/stereotyped "
                "thinking",
                "occasional transient quasi-psychotic episodes",
            ]
        )
    )

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        c = self.meets_criteria()
        if c is None:
            category = "Unknown if met or not met"
        elif c:
            category = "Met"
        else:
            category = "Not met"
        infolist = [CtvInfo(
            content=(
                "Pertains to: {}. Criteria for schizotypal "
                "disorder: {}.".format(
                    format_datetime_string(self.date_pertains_to,
                                           DATEFORMAT.LONG_DATE),
                    category
                )
            )
        )]
        if self.comments:
            infolist.append(CtvInfo(content=ws.webify(self.comments)))
        return infolist

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(name="meets_criteria", coltype=Boolean(),
                           value=self.meets_criteria(),
                           comment="Meets criteria for schizotypal disorder?"),
        ]

    # Meets criteria? These also return null for unknown.
    def meets_criteria(self) -> Optional[bool]:
        if not self.is_complete:
            return None
        return (
            self.count_booleans(
                repeat_fieldname("a", 1, Icd10Schizotypal.N_A)) >= 4 and
            self.b
        )

    def is_complete(self) -> bool:
        return (
            self.date_pertains_to is not None and
            self.are_all_fields_complete(repeat_fieldname(
                "a", 1, Icd10Schizotypal.N_A)) and
            self.b is not None and
            self.field_contents_valid()
        )

    def text_row(self, wstringname: str) -> str:
        return tr(td(self.wxstring(req, wstringname)),
                  td("", td_class="subheading"),
                  literal=True)

    def get_task_html(self, req: CamcopsRequest) -> str:
        h = self.get_standard_clinician_comments_block(self.comments) + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa(req.wappstring("date_pertains_to"),
                   format_datetime_string(self.date_pertains_to,
                                          DATEFORMAT.LONG_DATE, default=None))
        h += tr_qa(req.wappstring("meets_criteria"),
                   get_yes_no_none(self.meets_criteria()))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """
        h += self.text_row("a")
        for i in range(1, Icd10Schizotypal.N_A + 1):
            h += self.get_twocol_bool_row_true_false(
                "a" + str(i), self.wxstring(req, "a" + str(i)))
        h += self.get_twocol_bool_row_true_false(
            "b", self.wxstring(req, "b"))
        h += """
            </table>
        """ + ICD10_COPYRIGHT_DIV
        return h
