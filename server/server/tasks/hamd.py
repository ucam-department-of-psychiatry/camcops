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

from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    CLINICIAN_FIELDSPECS,
    CTV_DICTLIST_INCOMPLETE,
    get_from_dict,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# HAM-D
# =============================================================================

MAX_SCORE = (
    4 * 15  # Q1-15 scored 0-5
    - (2 * 6)  # except Q4-6, 12-14 scored 0-2
    + 2 * 2  # Q16-17
)  # ... and not scored beyond Q17... total 52


class Hamd(Task):
    NSCOREDQUESTIONS = 17
    NQUESTIONS = 21
    TASK_FIELDSPECS = (
        STANDARD_TASK_FIELDSPECS +
        CLINICIAN_FIELDSPECS +
        repeat_fieldspec(
            "q", 1, 15, comment_fmt="Q{n}, {s} (scored 0-4, except 0-2 for "
            "Q4-6/12-14, higher worse)", min=0, max=4,  # amended below
            comment_strings=[
                "depressed mood", "guilt", "suicide", "early insomnia",
                "middle insomnia", "late insomnia", "work/activities",
                "psychomotor retardation", "agitation",
                "anxiety, psychological", "anxiety, somatic",
                "somatic symptoms, gastointestinal",
                "somatic symptoms, general", "genital symptoms",
                "hypochondriasis"
            ]) +
        [
            dict(name="whichq16", cctype="INT", min=0, max=1,
                 comment="Method of assessing weight loss (0 = A, by history; "
                 "1 = B, by measured change)"),
            dict(name="q16a", cctype="INT", min=0, max=3,
                 comment="Q16A, weight loss, by history (0 none - 2 definite,"
                 " or 3 not assessed [not scored])"),
            dict(name="q16b", cctype="INT", min=0, max=3,
                 comment="Q16B, weight loss, by measurement (0 none - "
                 "2 more than 2lb, or 3 not assessed [not scored])"),
            dict(name="q17", cctype="INT", min=0, max=2,
                 comment="Q17, lack of insight (0-2, higher worse)"),
            dict(name="q18a", cctype="INT", min=0, max=2,
                 comment="Q18A (not scored), diurnal variation, presence "
                 "(0 none, 1 worse AM, 2 worse PM)"),
            dict(name="q18b", cctype="INT", min=0, max=2,
                 comment="Q18B (not scored), diurnal variation, severity "
                 "(0-2, higher more severe)"),
        ] +
        repeat_fieldspec(
            "q", 19, 21, comment_fmt="Q{n} (not scored), {s} (0-4 for Q19, "
            "0-3 for Q20, 0-2 for Q21, higher worse)", min=0, max=4,  # below
            comment_strings=["depersonalization/derealization",
                             "paranoid symptoms",
                             "obsessional/compulsive symptoms"])
    )
    # Now fix the wrong bits. Hardly elegant!
    for item in TASK_FIELDSPECS:
        name = item["name"]
        if (name == "q4" or name == "q5" or name == "q6"
                or name == "q12" or name == "q13" or name == "q14"
                or name == "q21"):
            item["max"] = 2
        if name == "q20":
            item["max"] = 3

    @classmethod
    def get_tablename(cls):
        return "hamd"

    @classmethod
    def get_taskshortname(cls):
        return "HAM-D"

    @classmethod
    def get_tasklongname(cls):
        return "Hamilton Rating Scale for Depression"

    @classmethod
    def get_fieldspecs(cls):
        return Hamd.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "HAM-D total score",
                "axis_label": "Total score (out of {})".format(MAX_SCORE),
                "axis_min": -0.5,
                "axis_max": MAX_SCORE + 0.5,
                "horizontal_lines": [
                    22.5,
                    19.5,
                    14.5,
                    7.5
                ],
                "horizontal_labels": [
                    (25, WSTRING("hamd_severity_verysevere")),
                    (21, WSTRING("hamd_severity_severe")),
                    (17, WSTRING("hamd_severity_moderate")),
                    (11, WSTRING("hamd_severity_mild")),
                    (3.75, WSTRING("hamd_severity_none"))
                ]
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "HAM-D total score {}/{} ({})".format(
                self.total_score(), MAX_SCORE, self.severity())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/{})".format(MAX_SCORE)),
            dict(name="severity", cctype="TEXT", value=self.severity(),
                 comment="Severity"),
        ]

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        if self.q1 is None or self.q9 is None or self.q10 is None:
            return False
        if self.q1 == 0:
            # Special limited-information completeness
            return True
        if self.q2 is not None and self.q3 is not None \
                and (self.q2 + self.q3 == 0):
            # Special limited-information completeness
            return True
        # Otherwise, any null values cause problems
        if self.whichq16 is None:
            return False
        for i in range(1, Hamd.NSCOREDQUESTIONS + 1):
            if i == 16:
                if (self.whichq16 == 0 and self.q16a is None) \
                        or (self.whichq16 == 1 and self.q16b is None):
                    return False
            else:
                if getattr(self, "q" + str(i)) is None:
                    return False
        return True

    def total_score(self):
        total = 0
        for i in range(1, Hamd.NSCOREDQUESTIONS + 1):
            if i == 16:
                relevant_field = "q16a" if self.whichq16 == 0 else "q16b"
                score = self.sum_fields([relevant_field])
                if score != 3:  # ... a value that's ignored
                    total += score
            else:
                total += self.sum_fields(["q" + str(i)])
        return total

    def severity(self):
        score = self.total_score()
        if score >= 23:
            return WSTRING("hamd_severity_verysevere")
        elif score >= 19:
            return WSTRING("hamd_severity_severe")
        elif score >= 14:
            return WSTRING("hamd_severity_moderate")
        elif score >= 8:
            return WSTRING("hamd_severity_mild")
        else:
            return WSTRING("hamd_severity_none")

    def get_task_html(self):
        score = self.total_score()
        severity = self.severity()
        TASK_FIELD_LIST_FOR_DISPLAY = (
            repeat_fieldname("q", 1, 15) +
            [
                "whichq16",
                "q16a" if self.whichq16 == 0 else "q16b",  # funny one
                "q17",
                "q18a",
                "q18b"
            ] +
            repeat_fieldname("q", 19, 21)
        )
        ANSWER_DICTS_DICT = {}
        for q in TASK_FIELD_LIST_FOR_DISPLAY:
            d = {None: None}
            for option in range(0, 5):
                if (q == "q4" or q == "q5" or q == "q6" or q == "q12"
                        or q == "q13" or q == "q14" or q == "q17"
                        or q == "q18" or q == "q21") and option > 2:
                    continue
                d[option] = WSTRING("hamd_" + q + "_option" + str(option))
            ANSWER_DICTS_DICT[q] = d
        h = self.get_standard_clinician_block() + u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score") + " <sup>[1]</sup>",
                answer(score) + " / {}".format(MAX_SCORE))
        h += tr_qa(WSTRING("hamd_severity") + " <sup>[2]</sup>", severity)
        h += u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="40%">Question</th>
                    <th width="60%">Answer</th>
                </tr>
        """
        for q in TASK_FIELD_LIST_FOR_DISPLAY:
            if q == "whichq16":
                qstr = WSTRING("hamd_whichq16_title")
            else:
                if q == "q16a" or q == "q16b":
                    rangestr = u" <sup>range 0–2; ‘3’ not scored</sup>"
                else:
                    rangestr = next((
                        u" <sup>range {}–{}</sup>".format(
                            item.get("min"), item.get("max")
                        )
                        for item in Hamd.TASK_FIELDSPECS
                        if item["name"] == q
                    ), "")
                    # http://stackoverflow.com/questions/8653516
                qstr = WSTRING("hamd_" + q + "_s") + rangestr
            h += tr_qa(qstr, get_from_dict(ANSWER_DICTS_DICT[q],
                                           getattr(self, q)))
        h += u"""
            </table>
            <div class="footnotes">
                [1] Only Q1–Q17 scored towards the total.
                    Re Q16: values of ‘3’ (‘not assessed’) are not actively
                    scored, after e.g. Guy W (1976) <i>ECDEU Assessment Manual
                    for Psychopharmacology, revised</i>, pp. 180–192, esp.
                    pp. 187, 189
                    (https://archive.org/stream/ecdeuassessmentm1933guyw).
                [2] ≥23 very severe, ≥19 severe, ≥14 moderate,
                    ≥8 mild, &lt;8 none.
            </div>
        """
        return h
