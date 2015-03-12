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

import rnc_web as ws
from cc_html import tr
from cc_string import WSTRING
from cc_task import (
    CLINICIAN_FIELDSPECS,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# ProgressNote
# =============================================================================

class ProgressNote(Task):
    @classmethod
    def get_tablename(cls):
        return "progressnote"

    @classmethod
    def get_taskshortname(cls):
        return "ProgressNote"

    @classmethod
    def get_tasklongname(cls):
        return "Clinical progress note"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + [
            dict(name="location", cctype="TEXT", comment="Location"),
            dict(name="note", cctype="TEXT", comment="Clinical note"),
        ]

    def get_clinical_text(self):
        return [{"content": ws.webify(self.note)}]

    def is_complete(self):
        return (self.note is not None)

    def get_task_html(self):
        # Avoid tables - PDF generator crashes if text is too long.
        h = self.get_standard_clinician_block() + u"""
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
