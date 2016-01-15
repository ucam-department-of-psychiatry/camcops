#!/usr/bin/env python3
# cgisch.py

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
    CLINICIAN_FIELDSPECS,
    CTV_DICTLIST_INCOMPLETE,
    STANDARD_TASK_FIELDSPECS,
)
from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import (
    subheading_spanning_two_columns,
    tr_qa,
    tr_span_col,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# CGI-SCH
# =============================================================================

QUESTION_FRAGMENTS = ["positive", "negative", "depressive", "cognitive",
                      "overall"]


class CgiSch(Task):
    TASK_FIELDSPECS = (
        repeat_fieldspec(
            "severity", 1, 5, min=1, max=7,
            comment_fmt="Severity Q{n}, {s} (1-7, higher worse)",
            comment_strings=QUESTION_FRAGMENTS) +
        repeat_fieldspec(
            "change", 1, 5, pv=list(range(1, 7 + 1)) + [9],
            comment_fmt="Change Q{n}, {s} (1-7, higher worse, or 9 N/A)",
            comment_strings=QUESTION_FRAGMENTS)
    )
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "cgisch"

    @classmethod
    def get_taskshortname(cls):
        return "CGI-SCH"

    @classmethod
    def get_tasklongname(cls):
        return "Clinical Global Impression – Schizophrenia"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + \
            CgiSch.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        prefix = "CGI-SCH severity: "
        ylabel = "Score (1-7)"
        return [
            {
                "value": self.severity1,
                "plot_label": prefix + "positive symptoms",
                "axis_label": ylabel,
                "axis_min": 0.5,
                "axis_max": 7.5,
            },
            {
                "value": self.severity2,
                "plot_label": prefix + "negative symptoms",
                "axis_label": ylabel,
                "axis_min": 0.5,
                "axis_max": 7.5,
            },
            {
                "value": self.severity3,
                "plot_label": prefix + "depressive symptoms",
                "axis_label": ylabel,
                "axis_min": 0.5,
                "axis_max": 7.5,
            },
            {
                "value": self.severity4,
                "plot_label": prefix + "cognitive symptoms",
                "axis_label": ylabel,
                "axis_min": 0.5,
                "axis_max": 7.5,
            },
            {
                "value": self.severity5,
                "plot_label": prefix + "overall severity",
                "axis_label": ylabel,
                "axis_min": 0.5,
                "axis_max": 7.5,
            },
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": ("CGI-SCH. Severity: positive {}, negative {}, "
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
                        ))
        }]

    def get_summaries(self):
        return [self.is_complete_summary_field()]

    def is_complete(self):
        return (
            self.are_all_fields_complete(CgiSch.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def get_task_html(self):
        SEVERITY_DICT = {
            None: None,
            1: WSTRING("cgisch_i_option1"),
            2: WSTRING("cgisch_i_option2"),
            3: WSTRING("cgisch_i_option3"),
            4: WSTRING("cgisch_i_option4"),
            5: WSTRING("cgisch_i_option5"),
            6: WSTRING("cgisch_i_option6"),
            7: WSTRING("cgisch_i_option7"),
        }
        CHANGE_DICT = {
            None: None,
            1: WSTRING("cgisch_ii_option1"),
            2: WSTRING("cgisch_ii_option2"),
            3: WSTRING("cgisch_ii_option3"),
            4: WSTRING("cgisch_ii_option4"),
            5: WSTRING("cgisch_ii_option5"),
            6: WSTRING("cgisch_ii_option6"),
            7: WSTRING("cgisch_ii_option7"),
            9: WSTRING("cgisch_ii_option9"),
        }
        h = self.get_standard_clinician_block() + """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer <sup>[1]</sup></th>
                </tr>
        """.format(self.get_is_complete_tr())
        h += subheading_spanning_two_columns(WSTRING("cgisch_i_title"))
        h += tr_span_col(WSTRING("cgisch_i_question"), cols=2)
        h += tr_qa(WSTRING("cgisch_q1"),
                   get_from_dict(SEVERITY_DICT, self.severity1))
        h += tr_qa(WSTRING("cgisch_q2"),
                   get_from_dict(SEVERITY_DICT, self.severity2))
        h += tr_qa(WSTRING("cgisch_q3"),
                   get_from_dict(SEVERITY_DICT, self.severity3))
        h += tr_qa(WSTRING("cgisch_q4"),
                   get_from_dict(SEVERITY_DICT, self.severity4))
        h += tr_qa(WSTRING("cgisch_q5"),
                   get_from_dict(SEVERITY_DICT, self.severity5))
        h += subheading_spanning_two_columns(WSTRING("cgisch_ii_title"))
        h += tr_span_col(WSTRING("cgisch_ii_question"), cols=2)
        h += tr_qa(WSTRING("cgisch_q1"),
                   get_from_dict(CHANGE_DICT, self.change1))
        h += tr_qa(WSTRING("cgisch_q2"),
                   get_from_dict(CHANGE_DICT, self.change2))
        h += tr_qa(WSTRING("cgisch_q3"),
                   get_from_dict(CHANGE_DICT, self.change3))
        h += tr_qa(WSTRING("cgisch_q4"),
                   get_from_dict(CHANGE_DICT, self.change4))
        h += tr_qa(WSTRING("cgisch_q5"),
                   get_from_dict(CHANGE_DICT, self.change5))
        h += """
            </table>
            <div class="footnotes">
                [1] All questions are scored 1–7, or 9 (not applicable, for
                change questions).
                {postscript}
            </div>
        """.format(
            postscript=WSTRING("cgisch_ii_postscript"),
        )
        return h
