#!/usr/bin/env python3
# progressnote.py

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
from ..cc_modules.cc_html import answer
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import Task


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

    def get_clinical_text(self):
        return [{"content": ws.webify(self.note)}]

    def is_complete(self):
        return self.note is not None

    def get_task_html(self):
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
