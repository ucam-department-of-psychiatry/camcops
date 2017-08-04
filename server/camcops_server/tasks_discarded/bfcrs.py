#!/usr/bin/env python
# camcops_server/tasks_discarded/bfcrs.py

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
from ..cc_modules.cc_html import get_yes_no
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import get_from_dict, Task
from ..cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# BFCRS
# =============================================================================

class Bfcrs(Task):
    tablename = "bfcrs"
    shortname = "BFCRS"
    longname = "Bush–Francis Catatonia Rating Scale"
    provides_trackers = True

    NQUESTIONS = 23
    N_CSI_QUESTIONS = 14  # the first 14
    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="BFCRS total score",
            axis_label="Total score (out of 69)",
            axis_min=-0.5,
            axis_max=69.5
        )]

    def get_summaries(self) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(name="total", coltype=Integer(),
                           value=self.total_score(), comment="Total score"),
        ]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.TASK_FIELDS)

    def get_num_csi_symptoms(self) -> int:
        n = 0
        for i in range(1, self.N_CSI_QUESTIONS + 1):
            value = getattr(self, "q" + str(i))
            if value is not None and value > 0:
                n += 1
        return n

    def get_task_html(self) -> str:
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
                d[option] = self.wxstring(q + "_option" + str(option))
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
            wappstring("total_score"), score,
            self.wxstring("num_symptoms_present"), n_csi_symptoms,
            self.wxstring("catatonia_present"), get_yes_no(csi_catatonia)
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
