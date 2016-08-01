#!/usr/bin/env python3
# gass.py

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

from typing import Dict, List

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import get_yes_no
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import get_from_dict, Task, TrackerInfo


# =============================================================================
# GASS
# =============================================================================

class Gass(Task):
    NQUESTIONS = 22
    list_sedation = [1, 2]
    list_cardiovascular = [3, 4]
    list_epse = [5, 6, 7, 8, 9, 10]
    list_anticholinergic = [11, 12, 13]
    list_gastrointestinal = [14]
    list_genitourinary = [15]
    list_prolactinaemic_female = [17, 18, 19, 21]
    list_prolactinaemic_male = [17, 18, 19, 20]
    list_weightgain = [22]

    tablename = "gass"
    shortname = "GASS"
    longname = "Glasgow Antipsychotic Side-effect Scale"
    fieldspecs = (
        [dict(name="medication", cctype="TEXT")] +
        repeat_fieldspec("q", 1, NQUESTIONS) +
        repeat_fieldspec("d", 1, NQUESTIONS)
    )

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="GASS total score",
            axis_label="Total score (out of 63)",
            axis_min=-0.5,
            axis_max=63.5
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score"),
        ]

    @staticmethod
    def get_q_fieldlist(group) -> List[str]:
        return ["q" + str(q) for q in group]

    @staticmethod
    def get_d_fieldlist(group) -> List[str]:
        return ["d" + str(q) for q in group]

    def get_relevant_q_fieldlist(self) -> List[str]:
        qnums = range(1, self.NQUESTIONS + 1)
        if self.is_female():
            qnums.remove(20)
        else:
            qnums.remove(21)
        return ["q" + str(q) for q in qnums]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.get_relevant_q_fieldlist())

    def total_score(self) -> int:
        return self.sum_fields(self.get_relevant_q_fieldlist())

    def group_score(self, qnums: List[int]) -> int:
        return self.sum_fields(self.get_q_fieldlist(qnums))

    @staticmethod
    def get_subheading(subtitle: str, score: int, max_score: int) -> str:
        return """
            <tr class="subheading">
                <td>{}</td>
                <td colspan="2"><i><b>{}</b> / {}</i></td>
            </tr>
        """.format(
            subtitle,
            score,
            max_score
        )

    def get_row(self, q: int, answer_dict: Dict) -> str:
        return """<tr><td>{}</td><td><b>{}</b></td><td>{}</td></tr>""".format(
            WSTRING("gass_q" + str(q)),
            get_from_dict(answer_dict, getattr(self, "q" + str(q))),
            get_yes_no(getattr(self, "d" + str(q)))
        )

    def get_group_html(self,
                       qnums: List[int],
                       subtitle: str,
                       answer_dict: Dict) -> str:
        h = self.get_subheading(
            subtitle,
            self.group_score(qnums),
            len(qnums) * 3
        )
        for q in qnums:
            h += self.get_row(q, answer_dict)
        return h

    def get_task_html(self) -> str:
        score = self.total_score()
        answer_dict = {None: "?"}
        for option in range(0, 4):
            answer_dict[option] = (
                str(option) + " — " + WSTRING("gass_option" + str(option)))
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 63</td></tr>
                </table>
            </div>
            <div class="explanation">
                Ratings pertain to the past week.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="65%">Question</th>
                    <th width="20%">Answer</th>
                    <th width="15%">Distressing?</th><
                /tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score
        )
        h += self.get_group_html(self.list_sedation,
                                 WSTRING("gass_group_sedation"),
                                 answer_dict)
        h += self.get_group_html(self.list_cardiovascular,
                                 WSTRING("gass_group_cardiovascular"),
                                 answer_dict)
        h += self.get_group_html(self.list_epse,
                                 WSTRING("gass_group_epse"),
                                 answer_dict)
        h += self.get_group_html(self.list_anticholinergic,
                                 WSTRING("gass_group_anticholinergic"),
                                 answer_dict)
        h += self.get_group_html(self.list_gastrointestinal,
                                 WSTRING("gass_group_gastrointestinal"),
                                 answer_dict)
        h += self.get_group_html(self.list_genitourinary,
                                 WSTRING("gass_group_genitourinary"),
                                 answer_dict)
        if self.is_female():
            h += self.get_group_html(self.list_prolactinaemic_female,
                                     WSTRING("gass_group_prolactinaemic") +
                                     " (" + WSTRING("female") + ")",
                                     answer_dict)
        else:
            h += self.get_group_html(self.list_prolactinaemic_male,
                                     WSTRING("gass_group_prolactinaemic") +
                                     " (" + WSTRING("male") + ")",
                                     answer_dict)
        h += self.get_group_html(self.list_weightgain,
                                 WSTRING("gass_group_weightgain"),
                                 answer_dict)
        h += """
                <tr class="subheading"><td colspan="3">{}</td></tr>
                <tr><td colspan="3">{}</td></tr>
            </table>
        """.format(
            WSTRING("gass_medication_hint"),
            ws.webify(self.medication)
        )
        return h
