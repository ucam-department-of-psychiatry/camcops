#!/usr/bin/env python3
# icd10mixed.py

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
from cc_modules.cc_dt import format_datetime_string
from cc_modules.cc_html import (
    get_true_false_none,
    tr_qa,
)
from cc_modules.cc_lang import is_false
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import Task


# =============================================================================
# Icd10Mixed
# =============================================================================

class Icd10Mixed(Task):
    tablename = "icd10mixed"
    shortname = "ICD10-MIXED"
    longname = (
        "ICD-10 symptomatic criteria for a mixed affective episode "
        "(as in e.g. F06.3, F25, F38.00, F31.6)"
    )
    fieldspecs = [
        dict(name="date_pertains_to", cctype="ISO8601",
             comment="Date the assessment pertains to"),
        dict(name="comments", cctype="TEXT",
             comment="Clinician's comments"),
        dict(name="mixture_or_rapid_alternation", cctype="BOOL",
             pv=PV.BIT,
             comment="The episode is characterized by either a mixture or "
             "a rapid alternation (i.e. within a few hours) of hypomanic, "
             "manic and depressive symptoms."),
        dict(name="duration_at_least_2_weeks", cctype="BOOL",
             pv=PV.BIT,
             comment="Both manic and depressive symptoms must be prominent"
             " most of the time during a period of at least two weeks."),
    ]
    has_clinician = True

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        category = (
            ("Meets" if self.meets_criteria() else "Does not meet") +
            " criteria for mixed affective episode"
        )
        dl = [{
            "content": "Pertains to: {}. {}.".format(
                format_datetime_string(self.date_pertains_to,
                                       DATEFORMAT.LONG_DATE),
                category)
        }]
        if self.comments:
            dl.append({"content": ws.webify(self.comments)})
        return dl

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="meets_criteria", cctype="BOOL",
                 value=self.meets_criteria(),
                 comment="Meets criteria for a mixed affective episode?"),
        ]

    # Meets criteria? These also return null for unknown.
    def meets_criteria(self):
        if (self.mixture_or_rapid_alternation and
                self.duration_at_least_2_weeks):
            return True
        if is_false(self.mixture_or_rapid_alternation):
            return False
        if is_false(self.duration_at_least_2_weeks):
            return False
        return None

    def is_complete(self):
        return (
            self.meets_criteria() is not None and
            self.field_contents_valid()
        )

    def get_task_html(self):
        h = self.get_standard_clinician_comments_block(self.comments) + """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa(WSTRING("date_pertains_to"),
                   format_datetime_string(self.date_pertains_to,
                                          DATEFORMAT.LONG_DATE, default=None))
        h += tr_qa(WSTRING("meets_criteria"),
                   get_true_false_none(self.meets_criteria()))
        h += """
                </table>
            </div>
            <div class="explanation">
        """
        h += WSTRING("icd10_symptomatic_disclaimer")
        h += """
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """

        h += self.get_twocol_bool_row_true_false(
            "mixture_or_rapid_alternation", WSTRING("icd10mixed_a"))
        h += self.get_twocol_bool_row_true_false(
            "duration_at_least_2_weeks", WSTRING("icd10mixed_b"))

        h += """
            </table>
        """ + ICD10_COPYRIGHT_DIV
        return h
