#!/usr/bin/env python3
# contactlog.py

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

from typing import List

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_constants import (
    DATEFORMAT,
    PV,
)
from ..cc_modules.cc_dt import format_datetime_string, get_duration_h_m
from ..cc_modules.cc_html import (
    italic,
    get_yes_no_none,
    tr,
    tr_qa,
)
from ..cc_modules.cc_task import CtvInfo, CTV_INCOMPLETE, Task


# =============================================================================
# ContactLog
# =============================================================================

class ContactLog(Task):
    tablename = "contactlog"
    shortname = "ContactLog"
    longname = "Clinical contact log"
    fieldspecs = [
        dict(name="location", cctype="TEXT", comment="Location"),
        dict(name="start", cctype="TEXT",
             comment="Date/time that contact started"),
        dict(name="end", cctype="TEXT",
             comment="Date/time that contact ended"),
        dict(name="patient_contact", cctype="INT", pv=PV.BIT,
             comment="Patient contact involved (0 no, 1 yes)?"),
        dict(name="staff_liaison", cctype="INT", pv=PV.BIT,
             comment="Liaison with staff involved (0 no, 1 yes)?"),
        dict(name="other_liaison", cctype="INT", pv=PV.BIT,
             comment="Liaison with others (e.g. family) involved "
             "(0 no, 1 yes)?"),
        dict(name="comment", cctype="TEXT", comment="Comment"),
    ]
    has_clinician = True

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        contact_type = "Patient" if self.patient_contact else "Non-patient"
        return [CtvInfo(
            content="{} contact. Duration (hours:minutes) {}.".format(
                contact_type, get_duration_h_m(self.start, self.end))
        )]

    def is_complete(self) -> bool:
        return (
            self.start is not None and
            self.end is not None and
            self.field_contents_valid()
        )

    def get_task_html(self) -> str:
        h = """
            <table class="taskdetail">
                <tr>
                    <td width="33%">Location:</td>
                    <td width="67%"><b>{}</b></td>
                </tr>
        """.format(
            ws.webify(self.location),
        )
        h += tr_qa("Start:", format_datetime_string(self.start,
                                                    DATEFORMAT.SHORT_DATETIME,
                                                    None))
        h += tr_qa("End:", format_datetime_string(self.end,
                                                  DATEFORMAT.SHORT_DATETIME,
                                                  None))
        h += tr(italic("Calculated duration (hours:minutes)"),
                italic(get_duration_h_m(self.start, self.end)))
        h += tr_qa("Patient contact?", get_yes_no_none(self.patient_contact))
        h += tr_qa("Staff liaison?", get_yes_no_none(self.staff_liaison))
        h += tr_qa("Other liaison?", get_yes_no_none(self.other_liaison))
        h += tr_qa("Comment:", ws.webify(self.comment))
        return h
