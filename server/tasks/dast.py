#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

from cc_db import repeat_fieldspec
from cc_html import (
    answer,
    get_yes_no,
    tr,
    tr_qa,
)
from cc_string import WSTRING
from cc_task import (
    CTV_DICTLIST_INCOMPLETE,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# DAST
# =============================================================================

class Dast(Task):
    NQUESTIONS = 28
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, "CHAR", pv=['Y', 'N'],
        comment_fmt='Q{n}. {s} ("+" = Y scores 1, "-" = N scores 1)',
        comment_strings=[
            "non-medical drug use (+)",
            "abused prescription drugs (+)",
            "abused >1 drug at a time (+)",
            "get through week without drugs (-)",
            "stop when want to (-)",
            "abuse drugs continuously (+)",
            "try to limit to certain situations (-)",
            "blackouts/flashbacks (+)",
            "feel bad about drug abuse (-)",
            "spouse/parents complain (+)",
            "friends/relative know/suspect (+)",
            "caused problems with spouse (+)",
            "family sought help (+)",
            "lost friends (+)",
            "neglected family/missed work (+)",
            "trouble at work (+)",
            "lost job (+)",
            "fights under influence (+)",
            "arrested for unusual behaviour under influence (+)",
            "arrested for driving under influence (+)",
            "illegal activities to obtain (+)",
            "arrested for possession (+)",
            "withdrawal symptoms (+)",
            "medical problems (+)",
            "sought help (+)",
            "hospital for medical problems (+)",
            "drug treatment program (+)",
            "outpatient treatment for drug abuse (+)",
        ])
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "dast"

    @classmethod
    def get_taskshortname(cls):
        return "DAST"

    @classmethod
    def get_tasklongname(cls):
        return "Drug Abuse Screening Test"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + Dast.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "DAST total score",
                "axis_label": "Total score (out of 28)",
                "axis_min": -0.5,
                "axis_max": 28.5,
                "horizontal_lines": [
                    10.5,
                    5.5,
                ],
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "DAST total score {}/28".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score()),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(Dast.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def get_score(self, q):
        yes = "Y"
        value = getattr(self, "q" + str(q))
        if value is None:
            return 0
        if q == 4 or q == 5 or q == 7:
            return 0 if value == yes else 1
        else:
            return 1 if value == yes else 0

    def total_score(self):
        total = 0
        for q in range(1, Dast.NQUESTIONS + 1):
            total += self.get_score(q)
        return total

    def get_task_html(self):
        score = self.total_score()
        exceeds_cutoff_1 = score >= 6
        exceeds_cutoff_2 = score >= 11
        MAIN_DICT = {
            None: None,
            "Y": WSTRING("Yes"),
            "N": WSTRING("No")
        }
        h = u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 28")
        h += tr_qa(WSTRING("dast_exceeds_standard_cutoff_1"),
                   get_yes_no(exceeds_cutoff_1))
        h += tr_qa(WSTRING("dast_exceeds_standard_cutoff_2"),
                   get_yes_no(exceeds_cutoff_2))
        h += u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """
        for q in range(1, Dast.NQUESTIONS + 1):
            h += tr(
                WSTRING("dast_q" + str(q)),
                answer(get_from_dict(MAIN_DICT, getattr(self, "q" + str(q))))
                + u" — " + answer(str(self.get_score(q)))
            )
        h += u"""
            </table>
            <div class="copyright">
                DAST: Copyright © Harvey A. Skinner and the Centre for
                Addiction and Mental Health, Toronto, Canada.
                Reproduced here under the permissions granted for
                NON-COMMERCIAL use only. You must obtain permission from the
                copyright holder for any other use.
            </div>
        """
        return h
