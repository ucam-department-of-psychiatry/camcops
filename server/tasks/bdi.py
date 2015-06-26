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

import pythonlib.rnc_web as ws
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    CTV_DICTLIST_INCOMPLETE,
    DATA_COLLECTION_ONLY_DIV,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# BDI (crippled)
# =============================================================================

class Bdi(Task):
    NQUESTIONS = 21
    TASK_SCORED_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=0, max=3,
        comment_fmt="Q{n} [in BDI-II: {s}] (0-3, higher worse)",
        comment_strings=["sadness", "pessimism", "past failure",
                         "loss of pleasure", "guilt", "punishment",
                         "self-dislike", "self-criticality", "suicidality",
                         "crying", "agitation", "loss of interest",
                         "indecisive", "worthless", "energy", "sleep",
                         "irritability", "appetite", "concentration",
                         "fatigue", "libido"])
    TASK_FIELDSPECS = [
        dict(name="bdi_scale", cctype="TEXT",
             comment="Which BDI scale (BDI-I, BDI-IA, BDI-II)?"),
    ] + TASK_SCORED_FIELDSPECS
    TASK_SCORED_FIELDS = [x["name"] for x in TASK_SCORED_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "bdi"

    @classmethod
    def get_taskshortname(cls):
        return "BDI"

    @classmethod
    def get_tasklongname(cls):
        return "Beck Depression Inventory (data collection only)"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + Bdi.TASK_FIELDSPECS

    def is_complete(self):
        return (
            self.field_contents_valid()
            and self.bdi_scale is not None
            and self.are_all_fields_complete(
                repeat_fieldname("q", 1, Bdi.NQUESTIONS)
            )
        )

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [{
            "value": self.total_score(),
            "plot_label": "BDI total score (rating depressive symptoms)",
            "axis_label": "Score for Q1-21 (out of 63)",
            "axis_min": -0.5,
            "axis_max": 63.5,
        }]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": u"{} total score {}/63".format(
                       ws.webify(self.bdi_scale), self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score (/63)"),
        ]

    def total_score(self):
        return self.sum_fields(Bdi.TASK_SCORED_FIELDS)

    def get_task_html(self):
        score = self.total_score()
        h = u"""
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 63")
        h += u"""
                </table>
            </div>
            <div class="explanation">
                All questions are scored from 0–3
                (0 free of symptoms, 3 most symptomatic).
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """
        h += tr_qa(WSTRING("bdi_which_scale"), ws.webify(self.bdi_scale))

        for q in xrange(1, Bdi.NQUESTIONS + 1):
            h += tr_qa(u"{} {}".format(WSTRING("question"), q),
                       getattr(self, "q" + str(q)))
        h += u"""
            </table>
        """ + DATA_COLLECTION_ONLY_DIV
        return h
