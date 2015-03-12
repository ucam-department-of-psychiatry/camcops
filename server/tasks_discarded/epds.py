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

from cc_task import *

#==============================================================================
# EPDS
#==============================================================================

class Epds(Task):
    NQUESTIONS = 10
    TASK_FIELDSPECS = repeat_fieldspec("q", 1, NQUESTIONS)
    TASK_FIELDS = [ x["name"] for x in TASK_FIELDSPECS ]
    
    @classmethod
    def get_tablename(cls):
        return "epds"
    @classmethod
    def get_taskshortname(cls):
        return "EPDS"
    @classmethod
    def get_tasklongname(cls):
        return "Edinburgh Postnatal Depression Scale"
    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + Epds.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True
    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "EPDS total score (rating depressive symptoms)",
                "axis_label": "Total score (out of 30)",
                "axis_min": -0.5,
                "axis_max": 30.5,
                "horizontal_lines": [
                    12.5,
                     9.5,
                ],
                "horizontal_labels": [
                    (13, "likely depression"),
                    (10, "possible depression"),
                ]
            }
        ]
    
    def get_summaries(self):
        return [
            dict(name="is_complete", cctype="BOOL", value=self.is_complete() ),
            dict(name="total", cctype="INT", value=self.total_score() ),
        ]
    
    def is_complete(self):
        return self.are_all_fields_complete(Epds.TASK_FIELDS)
        
    def total_score(self):
        return self.sum_fields(Epds.TASK_FIELDS)
    
    def get_task_html(self):
        score = self.total_score()
        above_cutoff_1 = score >= 10
        above_cutoff_2 = score >= 13
        ANSWER_DICTS = []
        for q in range(1, Epds.NQUESTIONS + 1):
            d = { None: "?" }
            for option in range(0, 4):
                d[option] = str(option) + u" — " + WSTRING("epds_q" + str(q) + "_option" + str(option))
            ANSWER_DICTS.append(d)
        h = u"""
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 30</td></tr>
                    <tr><td>{} <sup>[1]</sup></td><td><b>{}</b></td></tr>
                    <tr><td>{} <sup>[2]</sup></td><td><b>{}</b></td></tr>
                </table>
            </div>
            <div class="explanation">
                Ratings are over the last week.
                <b>{}</b>
            </div>
            <table class="taskdetail">
                <tr><th width="50%">Question</th><th width="50%">Answer</th></tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score,
            WSTRING("epds_above_cutoff_1"), get_yes_no(above_cutoff_1),
            WSTRING("epds_above_cutoff_2"), get_yes_no(above_cutoff_2),
            WSTRING("epds_always_look_at_suicide")
        )
        for q in range(1, Epds.NQUESTIONS + 1):
            h += u"""<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("epds_q" + str(q) + "_question"),
                get_from_dict( ANSWER_DICTS[q - 1], getattr(self, "q" + str(q)) )
            )
        h += u"""
            </table>
            <div class="footnotes">
                [1] &ge;10.
                [2] &ge;13.
                (Cox et al. 1987, PubMed ID 3651732.)
            </div>
        """
        return h