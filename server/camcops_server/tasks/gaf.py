#!/usr/bin/env python
# gaf.py

"""
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
"""

from typing import List, Optional

from ..cc_modules.cc_constants import DATA_COLLECTION_ONLY_DIV
from ..cc_modules.cc_html import answer, tr
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task, TrackerInfo


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

    def is_complete(self) -> bool:
        return (
            self.score is not None and
            self.field_contents_valid() and
            self.score != 0
        )

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="GAF score (rating overall functioning)",
            axis_label="Score (1-100)",
            axis_min=0.5,
            axis_max=100.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(content="GAF score {}".format(self.total_score()))]

    def get_summaries(self):
        return [self.is_complete_summary_field()]

    def total_score(self) -> Optional[int]:
        if self.score == 0:
            return None
        return self.score

    def get_task_html(self) -> str:
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
