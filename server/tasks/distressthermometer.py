#!/usr/bin/env python3
# distressthermometer.py

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

from ..cc_modules.cc_constants import (
    PV,
)
from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import (
    get_yes_no_none,
    subheading_spanning_two_columns,
    tr_qa,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task


# =============================================================================
# Distress Thermometer
# =============================================================================

class DistressThermometer(Task):
    NQUESTIONS = 36

    tablename = "distressthermometer"
    shortname = "Distress Thermometer"
    longname = "Distress Thermometer"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, pv=PV.BIT, comment_fmt="{n}. {s} (0 no, 1 yes)",
        comment_strings=[
            "child care",
            "housing",
            "insurance/financial",
            "transportation",
            "work/school",
            "children",
            "partner",
            "close friend/relative",
            "depression",
            "fears",
            "nervousness",
            "sadness",
            "worry",
            "loss of interest",
            "spiritual/religious",
            "appearance",
            "bathing/dressing",
            "breathing",
            "urination",
            "constipation",
            "diarrhoea",
            "eating",
            "fatigue",
            "feeling swollen",
            "fevers",
            "getting around",
            "indigestion",
            "memory/concentration",
            "mouth sores",
            "nausea",
            "nose dry/congested",
            "pain",
            "sexual",
            "skin dry/itchy",
            "sleep",
            "tingling in hands/feet",
        ]
    ) + [
        dict(name="distress", cctype="INT", min=0, max=10,
             comment="Distress (0 none - 10 extreme)"),
        dict(name="other", cctype="TEXT", comment="Other problems"),
    ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if self.distress is None:
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="Overall distress: {}/10".format(self.distress)
        )]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(repeat_fieldname(
                "q", 1, self.NQUESTIONS) + ["distress"]) and
            self.field_contents_valid()
        )

    def get_task_html(self) -> str:
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr_qa("Overall distress (0–10)", self.distress)
        h += """
                </table>
            </div>
            <div class="explanation">
                All questions relate to distress/problems “in the past week,
                including today” (yes = problem, no = no problem).
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """
        h += tr_qa("Distress (0 no distress – 10 extreme distress)",
                   self.distress)
        h += subheading_spanning_two_columns("Practical problems")
        for i in range(1, 5 + 1):
            h += tr_qa(
                "{}. {}".format(i, WSTRING("distressthermometer_q" + str(i))),
                get_yes_no_none(getattr(self, "q" + str(i)))
            )
        h += subheading_spanning_two_columns("Family problems")
        for i in range(6, 8 + 1):
            h += tr_qa(
                "{}. {}".format(i, WSTRING("distressthermometer_q" + str(i))),
                get_yes_no_none(getattr(self, "q" + str(i)))
            )
        h += subheading_spanning_two_columns("Emotional problems")
        for i in range(9, 14 + 1):
            h += tr_qa(
                "{}. {}".format(i, WSTRING("distressthermometer_q" + str(i))),
                get_yes_no_none(getattr(self, "q" + str(i)))
            )
        h += subheading_spanning_two_columns("Spiritual problems")
        for i in range(15, 15 + 1):
            h += tr_qa(
                "{}. {}".format(i, WSTRING("distressthermometer_q" + str(i))),
                get_yes_no_none(getattr(self, "q" + str(i)))
            )
        h += subheading_spanning_two_columns("Physical problems")
        for i in range(16, self.NQUESTIONS + 1):
            h += tr_qa(
                "{}. {}".format(i, WSTRING("distressthermometer_q" + str(i))),
                get_yes_no_none(getattr(self, "q" + str(i)))
            )
        h += subheading_spanning_two_columns("Other problems")
        h += tr_qa(WSTRING("distressthermometer_other_s"), self.other)
        h += """
            </table>
        """
        return h
