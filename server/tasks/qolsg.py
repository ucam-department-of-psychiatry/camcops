#!/usr/bin/env python3
# qolsg.py

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
    PV,
)
from cc_modules.cc_html import (
    get_yes_no_none,
    tr_qa,
)
from cc_modules.cc_task import Task


# =============================================================================
# QoL-SG
# =============================================================================

DP = 3


class QolSG(Task):
    tablename = "qolsg"
    shortname = "QoL-SG"
    longname = "Quality of Life: Standard Gamble"
    fieldspecs = [
        dict(name="category_start_time", cctype="TEXT",
             comment="Time categories were offered (ISO-8601)"),
        dict(name="category_responded", cctype="INT", pv=PV.BIT,
             comment="Responded to category choice? (0 no, 1 yes)"),
        dict(name="category_response_time", cctype="TEXT",
             comment="Time category was chosen (ISO-8601)"),
        dict(name="category_chosen", cctype="TEXT",
             comment="Category chosen: high (QoL > 1), "
             "medium (0 <= QoL <= 1), low (QoL < 0)"),
        dict(name="gamble_fixed_option", cctype="TEXT",
             comment="Fixed option in gamble (current, healthy, dead)"),
        dict(name="gamble_lottery_option_p", cctype="TEXT",
             comment="Gamble: option corresponding to p  "
             "(current, healthy, dead)"),
        dict(name="gamble_lottery_option_q", cctype="TEXT",
             comment="Gamble: option corresponding to q  "
             "(current, healthy, dead) (q = 1 - p)"),
        dict(name="gamble_lottery_on_left", cctype="INT", pv=PV.BIT,
             comment="Gamble: lottery shown on the left (0 no, 1 yes)"),
        dict(name="gamble_starting_p", cctype="FLOAT", min=0, max=1,
             comment="Gamble: starting value of p"),
        dict(name="gamble_start_time", cctype="TEXT",
             comment="Time gamble was offered (ISO-8601)"),
        dict(name="gamble_responded", cctype="INT", pv=PV.BIT,
             comment="Gamble was responded to? (0 no, 1 yes)"),
        dict(name="gamble_response_time", cctype="TEXT",
             comment="Time subject responded to gamble (ISO-8601)"),
        dict(name="gamble_p", cctype="FLOAT", min=0, max=1,
             comment="Final value of p"),
        dict(name="utility", cctype="FLOAT",
             comment="Calculated utility, h"),
    ]

    def get_trackers(self):
        return [
            {
                "value": self.utility,
                "plot_label": "Quality of life: standard gamble",
                "axis_label": "QoL (0-1)",
                "axis_min": 0,
                "axis_max": 1,
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content":  "Quality of life: {}".format(
                        ws.number_to_dp(self.utility, DP))
        }]

    def is_complete(self):
        return (
            self.utility is not None and
            self.field_contents_valid()
        )

    def get_task_html(self):
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa("Utility", ws.number_to_dp(self.utility, DP, default=None))
        h += """
                </table>
            </div>
            <div class="explanation">
                Quality of life (QoL) has anchor values of 0 (none) and 1
                (perfect health). The Standard Gamble offers a trade-off to
                determine utility (QoL).
                Values &lt;0 and &gt;1 are possible with some gambles.
            </div>
            <table class="taskdetail">
                <tr><th width="50%">Measure</th><th width="50%">Value</th></tr>
        """
        h += tr_qa("Category choice: start time", self.category_start_time)
        h += tr_qa("Category choice: responded?",
                   get_yes_no_none(self.category_responded))
        h += tr_qa("Category choice: response time",
                   self.category_response_time)
        h += tr_qa("Category choice: category chosen", self.category_chosen)
        h += tr_qa("Gamble: fixed option", self.gamble_fixed_option)
        h += tr_qa("Gamble: lottery option for <i>p</i>",
                   self.gamble_lottery_option_p)
        h += tr_qa("Gamble: lottery option for <i>q</i> = 1 – <i>p</i>",
                   self.gamble_lottery_option_q)
        h += tr_qa("Gamble: lottery on left?",
                   get_yes_no_none(self.gamble_lottery_on_left))
        h += tr_qa("Gamble: starting <i>p</i>", self.gamble_starting_p)
        h += tr_qa("Gamble: start time", self.gamble_start_time)
        h += tr_qa("Gamble: responded?",
                   get_yes_no_none(self.gamble_responded))
        h += tr_qa("Gamble: response time", self.gamble_response_time)
        h += tr_qa("Gamble: <i>p</i>",
                   ws.number_to_dp(self.gamble_p, DP, default=None))
        h += tr_qa("Calculated utility",
                   ws.number_to_dp(self.utility, DP, default=None))
        h += """
            </table>
        """
        return h
