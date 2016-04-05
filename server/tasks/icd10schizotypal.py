#!/usr/bin/env python3
# icd10schizotypal.py

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

import cardinal_pythonlib.rnc_web as ws
from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
    DATEFORMAT,
    ICD10_COPYRIGHT_DIV,
    PV,
)
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_dt import format_datetime_string
from cc_modules.cc_html import (
    get_yes_no_none,
    td,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import Task


# =============================================================================
# Icd10Schizotypal
# =============================================================================

class Icd10Schizotypal(Task):
    N_A = 9

    tablename = "icd10schizotypal"
    shortname = "ICD10-SZTYP"
    longname = "ICD-10 criteria for schizotypal disorder (F21)"
    fieldspecs = (
        [
            dict(name="date_pertains_to", cctype="ISO8601",
                 comment="Date the assessment pertains to"),
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
            dict(name="b", cctype="BOOL", pv=PV.BIT,
                 comment="Criterion (B). True if: the subject has never met "
                 "the criteria for any disorder in F20 (Schizophrenia)."),
        ]
        + repeat_fieldspec(
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
    has_clinician = True

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        c = self.meets_criteria()
        if c is None:
            category = "Unknown if met or not met"
        elif c:
            category = "Met"
        else:
            category = "Not met"
        dl = [{
            "content":  "Pertains to: {}. Criteria for schizotypal "
                        "disorder: {}.".format(
                            format_datetime_string(self.date_pertains_to,
                                                   DATEFORMAT.LONG_DATE),
                            category
                        )
        }]
        if self.comments:
            dl.append({"content": ws.webify(self.comments)})
        return dl

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="meets_criteria", cctype="BOOL",
                 value=self.meets_criteria(),
                 comment="Meets criteria for schizotypal disorder?"),
        ]

    # Meets criteria? These also return null for unknown.
    def meets_criteria(self):
        if not self.is_complete:
            return None
        return (
            self.count_booleans(repeat_fieldname("a", 1,
                                                 Icd10Schizotypal.N_A)) >= 4
            and self.b
        )

    def is_complete(self):
        return (
            self.date_pertains_to is not None
            and self.are_all_fields_complete(repeat_fieldname(
                "a", 1, Icd10Schizotypal.N_A))
            and self.b is not None
            and self.field_contents_valid()
        )

    def text_row(self, wstringname):
        return tr(td(WSTRING(wstringname)),
                  td("", td_class="subheading"),
                  literal=True)

    def basic_row(self, stem, i):
        return self.get_twocol_bool_row(
            stem + str(i), WSTRING("icd10_" + stem + "_pd_" + str(i)))

    def get_task_html(self):
        h = self.get_standard_clinician_comments_block(self.comments) + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa(WSTRING("date_pertains_to"),
                   format_datetime_string(self.date_pertains_to,
                                          DATEFORMAT.LONG_DATE, default=None))
        h += tr_qa(WSTRING("meets_criteria"),
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
        h += self.text_row("icd10schizotypal_a")
        for i in range(1, Icd10Schizotypal.N_A + 1):
            h += self.get_twocol_bool_row_true_false(
                "a" + str(i), WSTRING("icd10schizotypal_a" + str(i)))
        h += self.get_twocol_bool_row_true_false(
            "b", WSTRING("icd10schizotypal_b"))
        h += """
            </table>
        """ + ICD10_COPYRIGHT_DIV
        return h
