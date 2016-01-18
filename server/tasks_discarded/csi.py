#!/usr/bin/env python3
# csi.py

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
from cc_modules.cc_html import get_yes_no, get_yes_no_unknown
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import Task


# =============================================================================
# CSI
# =============================================================================

class Csi(Task):
    NQUESTIONS = 14

    tablename = "csi"
    shortname = "CSI"
    longname = "Catatonia Screening Instrument"
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)
    has_clinician = True  # !!! not implemented on tablet; should be

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "CSI total score",
                "axis_label": "Total score (out of 14)",
                "axis_min": -0.5,
                "axis_max": 14.5,
                "horizontal_lines": [
                    1.5
                ],
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

    def get_task_html(self):
        n_csi_symptoms = self.total_score()
        csi_catatonia = n_csi_symptoms >= 2
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 14</td></tr>
                    <tr><td>{} <sup>[1]</sup></td><td><b>{}</b></td></tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Present?</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("csi_num_symptoms_present"), n_csi_symptoms,
            WSTRING("csi_catatonia_present"), get_yes_no(csi_catatonia)
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                "Q" + str(q) + " — " + WSTRING("bfcrs_q" + str(q) + "_title"),
                get_yes_no_unknown(getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Number of CSI symptoms ≥2.
            </div>
        """
        return h
