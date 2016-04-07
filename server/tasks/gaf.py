#!/usr/bin/env python3
# gaf.py

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

from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
    DATA_COLLECTION_ONLY_DIV,
)
from cc_modules.cc_html import (
    answer,
    tr,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import Task


# =============================================================================
# GAF (crippled)
# =============================================================================

class Gaf(Task):
    tablename = "gaf"
    shortname = "GAF"
    longname = "Global Assessment of Functioning (data collection only)"
    fieldspecs = [
        dict(name="score", cctype="INT", min=0, max=100,
             comment="GAF score (1-100 or 0 for insufficient information)"),
    ]
    has_clinician = True

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def is_complete(self):
        return (
            self.score is not None and
            self.field_contents_valid() and
            self.score != 0
        )

    def get_trackers(self):
        return [{
            "value": self.total_score(),
            "plot_label": "GAF score (rating overall functioning)",
            "axis_label": "Score (1-100)",
            "axis_min": 0.5,
            "axis_max": 100.5,
        }]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{"content": "GAF score {}".format(self.total_score())}]

    def get_summaries(self):
        return [self.is_complete_summary_field()]

    def total_score(self):
        if self.score == 0:
            return None
        return self.score

    def get_task_html(self):
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("gaf_score"), answer(self.score))
        h += """
                </table>
            </div>
        """ + DATA_COLLECTION_ONLY_DIV
        return h
