#!/usr/bin/env python
# camcops_server/tasks_discarded/csi.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================
"""

from typing import List

from sqlalchemy.sql.sqltypes import Integer

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import get_yes_no, get_yes_no_unknown
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import Task
from ..cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# CSI
# =============================================================================

class Csi(Task):
    tablename = "csi"
    shortname = "CSI"
    longname = "Catatonia Screening Instrument"
    has_clinician = True  # !!! not implemented on tablet; should be
    provides_trackers = True
    extrastring_taskname = "bfcrs"  # shares with BFCRS

    NQUESTIONS = 14
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)
    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="CSI total score",
            axis_label="Total score (out of 14)",
            axis_min=-0.5,
            axis_max=14.5,
            horizontal_lines=[1.5]
        )]

    def get_summaries(self) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(name="total",
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score"),
        ]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_task_html(self) -> str:
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
            self.wxstring("num_symptoms_present"), n_csi_symptoms,
            self.wxstring("catatonia_present"), get_yes_no(csi_catatonia)
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                "Q" + str(q) + " — " + self.wxstring("q" + str(q) + "_title"),
                get_yes_no_unknown(getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Number of CSI symptoms ≥2.
            </div>
        """
        return h
