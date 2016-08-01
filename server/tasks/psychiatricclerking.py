#!/usr/bin/env python3
# psychiatricclerking.py

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

from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import CtvInfo, Task


# =============================================================================
# PsychiatricClerking
# =============================================================================

class PsychiatricClerking(Task):
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

    tablename = "psychiatricclerking"
    shortname = "Clerking"
    longname = "Psychiatric clerking"
    fieldspecs = (
        FIELDSPEC_B +
        FIELDSPEC_C +
        FIELDSPEC_MSE +
        FIELDSPEC_PE +
        FIELDSPEC_D +
        FIELDSPEC_E +
        FIELDSPEC_F
    )
    has_clinician = True

    @staticmethod
    def get_ctv_heading(wstringname) -> CtvInfo:
        return CtvInfo(
            heading=ws.webify(WSTRING(wstringname)),
            skip_if_no_content=False
        )

    @staticmethod
    def get_ctv_subheading(wstringname) -> CtvInfo:
        return CtvInfo(
            subheading=ws.webify(WSTRING(wstringname)),
            skip_if_no_content=False
        )

    def get_ctv_description_content(self, x: str) -> CtvInfo:
        return CtvInfo(
            description=ws.webify(WSTRING(x)),
            content=ws.webify(getattr(self, x))
        )

    def get_clinical_text(self) -> List[CtvInfo]:
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

    @staticmethod
    def heading(wstringname: str) -> str:
        return '<div class="heading">{}</div>'.format(WSTRING(wstringname))

    @staticmethod
    def subheading(wstringname: str) -> str:
        return '<div class="subheading">{}</div>'.format(WSTRING(wstringname))

    @staticmethod
    def subsubheading(wstringname: str) -> str:
        return '<div class="subsubheading">{}</div>'.format(
            WSTRING(wstringname))

    def subhead_text(self, fieldname: str) -> str:
        return self.subheading(fieldname) + '<div><b>{}</b></div>'.format(
            ws.webify(getattr(self, fieldname))
        )

    def subsubhead_text(self, fieldname: str) -> str:
        return self.subsubheading(fieldname) + '<div><b>{}</b></div>'.format(
            ws.webify(getattr(self, fieldname))
        )

    def get_task_html(self) -> str:
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
