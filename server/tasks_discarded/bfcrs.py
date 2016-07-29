#!/usr/bin/env python3
# bfcrs.py

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

from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import get_yes_no
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# BFCRS
# =============================================================================

class Bfcrs(Task):
    NQUESTIONS = 23
    N_CSI_QUESTIONS = 14  # the first 14

    tablename = "bfcrs"
    shortname = "BFCRS"
    longname = "Bush–Francis Catatonia Rating Scale"
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "BFCRS total score",
                "axis_label": "Total score (out of 69)",
                "axis_min": -0.5,
                "axis_max": 69.5,
            }
        ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score"),
        ]

    def is_complete(self):
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self):
        return self.sum_fields(self.TASK_FIELDS)

    def get_num_csi_symptoms(self):
        n = 0
        for i in range(1, self.N_CSI_QUESTIONS + 1):
            value = getattr(self, "q" + str(i))
            if value is not None and value > 0:
                n += 1
        return n

    def get_task_html(self):
        score = self.total_score()
        n_csi_symptoms = self.get_num_csi_symptoms()
        csi_catatonia = n_csi_symptoms >= 2
        answer_dicts_dict = {}
        for q in self.TASK_FIELDS:
            d = {None: "?"}
            for option in range(0, 5):
                if (option != 0 and option != 3) and q in ["q17", "q18", "q19",
                                                           "q20", "q21"]:
                    continue
                d[option] = WSTRING("bfcrs_" + q + "_option" + str(option))
            answer_dicts_dict[q] = d
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 69</td></tr>
                    <tr><td>{} <sup>[1]</sup></td><td><b>{}</b></td></tr>
                    <tr><td>{} <sup>[2]</sup></td><td><b>{}</b></td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="35%">Question</th>
                    <th width="65%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score,
            WSTRING("csi_num_symptoms_present"), n_csi_symptoms,
            WSTRING("csi_catatonia_present"), get_yes_no(csi_catatonia)
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                "Q" + str(q) + " — " + WSTRING("bfcrs_q" + str(q) + "_title"),
                get_from_dict(answer_dicts_dict["q" + str(q)],
                              getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Symptoms 1–14, counted as present if score >0.
                [2] Number of CSI symptoms ≥2.
            </div>
        """
        return h
