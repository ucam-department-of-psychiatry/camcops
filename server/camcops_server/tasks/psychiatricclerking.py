#!/usr/bin/env python
# camcops_server/tasks/psychiatricclerking.py

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

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_ctvinfo import CtvInfo
from ..cc_modules.cc_task import Task


# =============================================================================
# PsychiatricClerking
# =============================================================================

class PsychiatricClerking(Task):
    tablename = "psychiatricclerking"
    shortname = "Clerking"
    longname = "Psychiatric clerking"
    has_clinician = True

    # FIELDSPEC_A = CLINICIAN_FIELDSPECS  # replaced by has_clinician
    FIELDSPEC_B = [
        dict(name="location", cctype="TEXT"),
        dict(name="contact_type", cctype="TEXT"),
        dict(name="reason_for_contact", cctype="TEXT"),
        dict(name="presenting_issue", cctype="TEXT"),
        dict(name="systems_review", cctype="TEXT"),
        dict(name="collateral_history", cctype="TEXT"),
    ]
    FIELDSPEC_C = [
        dict(name="diagnoses_psychiatric", cctype="TEXT"),
        dict(name="diagnoses_medical", cctype="TEXT"),
        dict(name="operations_procedures", cctype="TEXT"),
        dict(name="allergies_adverse_reactions", cctype="TEXT"),
        dict(name="medications", cctype="TEXT"),
        dict(name="recreational_drug_use", cctype="TEXT"),
        dict(name="family_history", cctype="TEXT"),
        dict(name="developmental_history", cctype="TEXT"),
        dict(name="personal_history", cctype="TEXT"),
        dict(name="premorbid_personality", cctype="TEXT"),
        dict(name="forensic_history", cctype="TEXT"),
        dict(name="current_social_situation", cctype="TEXT"),
    ]
    FIELDSPEC_MSE = [
        dict(name="mse_appearance_behaviour", cctype="TEXT"),
        dict(name="mse_speech", cctype="TEXT"),
        dict(name="mse_mood_subjective", cctype="TEXT"),
        dict(name="mse_mood_objective", cctype="TEXT"),
        dict(name="mse_thought_form", cctype="TEXT"),
        dict(name="mse_thought_content", cctype="TEXT"),
        dict(name="mse_perception", cctype="TEXT"),
        dict(name="mse_cognition", cctype="TEXT"),
        dict(name="mse_insight", cctype="TEXT"),
    ]
    FIELDSPEC_PE = [
        dict(name="physical_examination_general", cctype="TEXT"),
        dict(name="physical_examination_cardiovascular", cctype="TEXT"),
        dict(name="physical_examination_respiratory", cctype="TEXT"),
        dict(name="physical_examination_abdominal", cctype="TEXT"),
        dict(name="physical_examination_neurological", cctype="TEXT"),
    ]
    FIELDSPEC_D = [
        dict(name="assessment_scales", cctype="TEXT"),
        dict(name="investigations_results", cctype="TEXT"),
    ]
    FIELDSPEC_E = [
        dict(name="safety_alerts", cctype="TEXT"),
        dict(name="risk_assessment", cctype="TEXT"),
        dict(name="relevant_legal_information", cctype="TEXT"),
    ]
    FIELDSPEC_F = [
        dict(name="current_problems", cctype="TEXT"),
        dict(name="patient_carer_concerns", cctype="TEXT"),
        dict(name="impression", cctype="TEXT"),
        dict(name="management_plan", cctype="TEXT"),
        dict(name="information_given", cctype="TEXT"),
    ]
    for fslist in [FIELDSPEC_B, FIELDSPEC_C,
                   FIELDSPEC_MSE, FIELDSPEC_PE,
                   FIELDSPEC_D, FIELDSPEC_E, FIELDSPEC_F]:
        for d in fslist:
            d["comment"] = d["name"]
        # DO NOT write to FIELDSPEC_A like this, because that overwrite
        # CLINICIAN_FIELDSPECS.

    fieldspecs = (
        FIELDSPEC_B +
        FIELDSPEC_C +
        FIELDSPEC_MSE +
        FIELDSPEC_PE +
        FIELDSPEC_D +
        FIELDSPEC_E +
        FIELDSPEC_F
    )

    def get_ctv_heading(self, wstringname) -> CtvInfo:
        return CtvInfo(
            heading=self.wxstring(req, wstringname),
            skip_if_no_content=False
        )

    def get_ctv_subheading(self, wstringname) -> CtvInfo:
        return CtvInfo(
            subheading=self.wxstring(req, wstringname),
            skip_if_no_content=False
        )

    def get_ctv_description_content(self, x: str) -> CtvInfo:
        return CtvInfo(
            description=self.wxstring(req, x),
            content=ws.webify(getattr(self, x))
        )

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        fields_b = [x["name"] for x in self.FIELDSPEC_B]
        fields_c = [x["name"] for x in self.FIELDSPEC_C]
        fields_mse = [x["name"] for x in self.FIELDSPEC_MSE]
        fields_pe = [x["name"] for x in self.FIELDSPEC_PE]
        fields_d = [x["name"] for x in self.FIELDSPEC_D]
        fields_e = [x["name"] for x in self.FIELDSPEC_E]
        fields_f = [x["name"] for x in self.FIELDSPEC_F]
        infolist = [self.get_ctv_heading(
            "psychiatricclerking_heading_current_contact")]
        for x in fields_b:
            infolist.append(self.get_ctv_description_content(x))
        infolist.append(self.get_ctv_heading(
            "psychiatricclerking_heading_background"))
        for x in fields_c:
            infolist.append(self.get_ctv_description_content(x))
        infolist.append(self.get_ctv_heading(
            "psychiatricclerking_heading_examination_investigations"))
        infolist.append(self.get_ctv_subheading("mental_state_examination"))
        for x in fields_mse:
            infolist.append(self.get_ctv_description_content(x))
        infolist.append(self.get_ctv_subheading("physical_examination"))
        for x in fields_pe:
            infolist.append(self.get_ctv_description_content(x))
        infolist.append(self.get_ctv_subheading(
            "assessments_and_investigations"))
        for x in fields_d:
            infolist.append(self.get_ctv_description_content(x))
        infolist.append(self.get_ctv_heading(
            "psychiatricclerking_heading_risk_legal"))
        for x in fields_e:
            infolist.append(self.get_ctv_description_content(x))
        infolist.append(self.get_ctv_heading(
            "psychiatricclerking_heading_summary_plan"))
        for x in fields_f:
            infolist.append(self.get_ctv_description_content(x))
        return infolist

    # noinspection PyMethodOverriding
    @staticmethod
    def is_complete() -> bool:
        return True

    def heading(self, wstringname: str) -> str:
        return '<div class="heading">{}</div>'.format(
            self.wxstring(req, wstringname))

    def subheading(self, wstringname: str) -> str:
        return '<div class="subheading">{}</div>'.format(
            self.wxstring(req, wstringname))

    def subsubheading(self, wstringname: str) -> str:
        return '<div class="subsubheading">{}</div>'.format(
            self.wxstring(req, wstringname))

    def subhead_text(self, fieldname: str) -> str:
        return self.subheading(fieldname) + '<div><b>{}</b></div>'.format(
            ws.webify(getattr(self, fieldname))
        )

    def subsubhead_text(self, fieldname: str) -> str:
        return self.subsubheading(fieldname) + '<div><b>{}</b></div>'.format(
            ws.webify(getattr(self, fieldname))
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        # Avoid tables - PDF generator crashes if text is too long.
        fields_b = [x["name"] for x in self.FIELDSPEC_B]
        fields_c = [x["name"] for x in self.FIELDSPEC_C]
        fields_mse = [x["name"] for x in self.FIELDSPEC_MSE]
        fields_pe = [x["name"] for x in self.FIELDSPEC_PE]
        fields_d = [x["name"] for x in self.FIELDSPEC_D]
        fields_e = [x["name"] for x in self.FIELDSPEC_E]
        fields_f = [x["name"] for x in self.FIELDSPEC_F]
        html = ""
        html += self.heading("psychiatricclerking_heading_current_contact")
        for x in fields_b:
            html += self.subhead_text(x)
        html += self.heading("psychiatricclerking_heading_background")
        for x in fields_c:
            html += self.subhead_text(x)
        html += self.heading(
            "psychiatricclerking_heading_examination_investigations")
        html += self.subheading("mental_state_examination")
        for x in fields_mse:
            html += self.subsubhead_text(x)
        html += self.subheading("physical_examination")
        for x in fields_pe:
            html += self.subsubhead_text(x)
        for x in fields_d:
            html += self.subhead_text(x)
        html += self.heading("psychiatricclerking_heading_risk_legal")
        for x in fields_e:
            html += self.subhead_text(x)
        html += self.heading("psychiatricclerking_heading_summary_plan")
        for x in fields_f:
            html += self.subhead_text(x)
        return html
