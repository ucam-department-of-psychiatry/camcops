#!/usr/bin/env python3
# qolbasic.py

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

import pythonlib.rnc_web as ws
from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
)
from cc_modules.cc_html import (
    answer,
    identity,
    tr,
)
from cc_modules.cc_lang import mean
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import Task


# =============================================================================
# QoL-Basic
# =============================================================================

DP = 3


class QolBasic(Task):
    tablename = "qolbasic"
    shortname = "QoL-Basic"
    longname = "Quality of Life: basic assessment"
    fieldspecs = [
        dict(name="tto", cctype="FLOAT", min=0, max=10,
             comment="Time trade-off (QoL * 10). Prompt: ... Indicate... the "
             "number of years in full health [0-10] that you think is of "
             "equal value to 10 years in your current health state."),
        dict(name="rs", cctype="FLOAT", min=0, max=100,
             comment="Rating scale (QoL * 100). Prompt: Mark the point on the "
             "scale [0-100] that you feel best illustrates your current "
             "quality of life."),
    ]

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self):
        return [
            {
                "value": self.get_tto_qol(),
                "plot_label": "Quality of life: time trade-off",
                "axis_label": "TTO QoL (0-1)",
                "axis_min": 0,
                "axis_max": 1,
            },
            {
                "value": self.get_rs_qol(),
                "plot_label": "Quality of life: rating scale",
                "axis_label": "RS QoL (0-1)",
                "axis_min": 0,
                "axis_max": 1,
            },
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        tto_qol = self.get_tto_qol()
        rs_qol = self.get_rs_qol()
        mean_qol = mean([tto_qol, rs_qol])
        return [{
            "content":  "Quality of life: time trade-off {}, rating scale {},"
                        " mean {}.".format(
                            ws.number_to_dp(tto_qol, DP),
                            ws.number_to_dp(rs_qol, DP),
                            ws.number_to_dp(mean_qol, DP)
                        )
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="tto_qol", cctype="FLOAT",
                 value=self.get_tto_qol(),
                 comment="Quality of life (0-1), from time trade-off method"),
            dict(name="rs_qol", cctype="FLOAT",
                 value=self.get_rs_qol(),
                 comment="Quality of life (0-1), from rating scale method"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(QolBasic.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def get_tto_qol(self):
        return self.tto / 10 if self.tto is not None else None

    def get_rs_qol(self):
        return self.rs / 100 if self.rs is not None else None

    def get_task_html(self):
        tto_qol = self.get_tto_qol()
        rs_qol = self.get_rs_qol()
        mean_qol = mean([tto_qol, rs_qol])
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr("Mean QoL", answer(ws.number_to_dp(mean_qol, DP, default=None),
                                   formatter_answer=identity))
        h += """
                </table>
            </div>
            <div class="explanation">
                Quality of life (QoL) has anchor values of 0 (none) and 1
                (perfect health), and can be asked about in several ways.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="33%">Scale</th>
                    <th width="33%">Answer</th>
                    <td width="33%">Implied QoL</th>
                </tr>
        """
        h += tr(WSTRING("qolbasic_tto_q_s"),
                answer(ws.number_to_dp(self.tto, DP, default=None)),
                answer(ws.number_to_dp(tto_qol, DP, default=None),
                       formatter_answer=identity))
        h += tr(WSTRING("qolbasic_rs_q_s"),
                answer(ws.number_to_dp(self.rs, DP, default=None)),
                answer(ws.number_to_dp(rs_qol, DP, default=None),
                       formatter_answer=identity))
        h += """
            </table>
        """
        return h
