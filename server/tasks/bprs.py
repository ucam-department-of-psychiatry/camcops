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

from cc_modules.cc_db import repeat_fieldspec
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
# BPRS
# =============================================================================

class Bprs(Task):
    NQUESTIONS = 20
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=7,
        comment_fmt="Q{n}, {s} (1-7, higher worse, 0 for unable to rate)",
        comment_strings=[
            "somatic concern", "anxiety", "emotional withdrawal",
            "conceptual disorganisation", "guilt", "tension",
            "mannerisms/posturing", "grandiosity", "depressive mood",
            "hostility", "suspiciousness", "hallucinatory behaviour",
            "motor retardation", "uncooperativeness",
            "unusual thought content", "blunted affect", "excitement",
            "disorientation", "severity of illness", "global improvement"])
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]
    SCORED_FIELDS = [x for x in TASK_FIELDS if (x != "q19" and x != "q20")]

    @classmethod
    def get_tablename(cls):
        return "bprs"

    @classmethod
    def get_taskshortname(cls):
        return "BPRS"

    @classmethod
    def get_tasklongname(cls):
        return "Brief Psychiatric Rating Scale"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + \
            Bprs.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "BPRS total score",
                "axis_label": "Total score (out of 126)",
                "axis_min": -0.5,
                "axis_max": 126.5,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "BPRS total score {}/126".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/126)"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(Bprs.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def total_score(self):
        return self.sum_fields(Bprs.SCORED_FIELDS, ignorevalue=0)
        # "0" means "not rated"

    def get_task_html(self):
        MAIN_DICT = {
            None: None,
            0: u"0 — " + WSTRING("bprsold_option0"),
            1: u"1 — " + WSTRING("bprsold_option1"),
            2: u"2 — " + WSTRING("bprsold_option2"),
            3: u"3 — " + WSTRING("bprsold_option3"),
            4: u"4 — " + WSTRING("bprsold_option4"),
            5: u"5 — " + WSTRING("bprsold_option5"),
            6: u"6 — " + WSTRING("bprsold_option6"),
            7: u"7 — " + WSTRING("bprsold_option7")
        }
        Q19_DICT = {
            None: None,
            1: WSTRING("bprs_q19_option1"),
            2: WSTRING("bprs_q19_option2"),
            3: WSTRING("bprs_q19_option3"),
            4: WSTRING("bprs_q19_option4"),
            5: WSTRING("bprs_q19_option5"),
            6: WSTRING("bprs_q19_option6"),
            7: WSTRING("bprs_q19_option7")
        }
        Q20_DICT = {
            None: None,
            0: WSTRING("bprs_q20_option0"),
            1: WSTRING("bprs_q20_option1"),
            2: WSTRING("bprs_q20_option2"),
            3: WSTRING("bprs_q20_option3"),
            4: WSTRING("bprs_q20_option4"),
            5: WSTRING("bprs_q20_option5"),
            6: WSTRING("bprs_q20_option6"),
            7: WSTRING("bprs_q20_option7")
        }
        h = self.get_standard_clinician_block() + u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score") +
                u" (0–126; 18–126 if all rated) <sup>[1]</sup>",
                answer(self.total_score()))
        h += u"""
                </table>
            </div>
            <div class="explanation">
                Ratings pertain to the past week, or behaviour during
                interview. Each question has specific answer definitions (see
                e.g. tablet app).
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer <sup>[2]</sup></th>
                </tr>
        """
        for i in range(1, Bprs.NQUESTIONS - 1):  # only does 1-18
            h += tr_qa(
                WSTRING("bprs_q" + str(i) + "_title"),
                get_from_dict(MAIN_DICT, getattr(self, "q" + str(i)))
            )
        h += tr_qa(WSTRING("bprs_q19_title"),
                   get_from_dict(Q19_DICT, self.q19))
        h += tr_qa(WSTRING("bprs_q20_title"),
                   get_from_dict(Q20_DICT, self.q20))
        h += u"""
            </table>
            <div class="footnotes">
                [1] Only questions 1–18 are scored.
                [2] All answers are in the range 1–7, or 0 (not assessed, for
                    some).
            </div>
        """
        return h
