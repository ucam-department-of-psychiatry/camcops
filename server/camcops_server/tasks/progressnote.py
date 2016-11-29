#!/usr/bin/env python3
# progressnote.py

"""
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

from typing import List

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_html import answer
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import CtvInfo, Task


# =============================================================================
# ProgressNote
# =============================================================================

class ProgressNote(Task):
    tablename = "progressnote"
    shortname = "ProgressNote"
    longname = "Clinical progress note"
    fieldspecs = [
        dict(name="location", cctype="TEXT", comment="Location"),
        dict(name="note", cctype="TEXT", comment="Clinical note"),
    ]
    has_clinician = True

    def get_clinical_text(self) -> List[CtvInfo]:
        return [CtvInfo(content=ws.webify(self.note))]

    def is_complete(self) -> bool:
        return self.note is not None

    def get_task_html(self) -> str:
        # Avoid tables - PDF generator crashes if text is too long.
        h = """
            <div class="heading">
                {heading_location}
            </div>
            <div>
                {location}
            </div>
            <div class="heading">
                {heading_note}
            </div>
            <div>
                {note}
            </div>
        """.format(
            heading_location=WSTRING("location"),
            location=answer(ws.webify(self.location),
                            default_for_blank_strings=True),
            heading_note=WSTRING("progressnote_note"),
            note=answer(ws.webify(self.note), default_for_blank_strings=True),
        )
        return h
