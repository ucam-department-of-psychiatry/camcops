"""
camcops_server/tasks/psychiatricclerking.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

"""

from typing import Dict, List, Optional

import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_ctvinfo import CtvInfo
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_snomed import (
    SnomedConcept,
    SnomedExpression,
    SnomedLookup,
)
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)


# =============================================================================
# PsychiatricClerking
# =============================================================================


class PsychiatricClerking(  # type: ignore[misc]
    TaskHasPatientMixin, TaskHasClinicianMixin, Task, Base
):
    """
    Server implementation of the Clerking task.
    """

    __tablename__ = "psychiatricclerking"
    shortname = "Clerking"
    info_filename_stem = "clinical"

    # FIELDSPEC_A = CLINICIAN_FIELDSPECS  # replaced by has_clinician, then by TaskHasClinicianMixin  # noqa

    location: Mapped[Optional[str]] = mapped_column("location", UnicodeText)
    contact_type: Mapped[Optional[str]] = mapped_column(UnicodeText)
    reason_for_contact: Mapped[Optional[str]] = mapped_column(UnicodeText)
    presenting_issue: Mapped[Optional[str]] = mapped_column(UnicodeText)
    systems_review: Mapped[Optional[str]] = mapped_column(UnicodeText)
    collateral_history: Mapped[Optional[str]] = mapped_column(UnicodeText)

    diagnoses_psychiatric: Mapped[Optional[str]] = mapped_column(UnicodeText)
    diagnoses_medical: Mapped[Optional[str]] = mapped_column(UnicodeText)
    operations_procedures: Mapped[Optional[str]] = mapped_column(UnicodeText)
    allergies_adverse_reactions: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )
    medications: Mapped[Optional[str]] = mapped_column(UnicodeText)
    recreational_drug_use: Mapped[Optional[str]] = mapped_column(UnicodeText)
    family_history: Mapped[Optional[str]] = mapped_column(UnicodeText)
    developmental_history: Mapped[Optional[str]] = mapped_column(UnicodeText)
    personal_history: Mapped[Optional[str]] = mapped_column(UnicodeText)
    premorbid_personality: Mapped[Optional[str]] = mapped_column(UnicodeText)
    forensic_history: Mapped[Optional[str]] = mapped_column(UnicodeText)
    current_social_situation: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )

    mse_appearance_behaviour: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )
    mse_speech: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mse_mood_subjective: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mse_mood_objective: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mse_thought_form: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mse_thought_content: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mse_perception: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mse_cognition: Mapped[Optional[str]] = mapped_column(UnicodeText)
    mse_insight: Mapped[Optional[str]] = mapped_column(UnicodeText)

    physical_examination_general: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )
    physical_examination_cardiovascular: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )
    physical_examination_respiratory: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )
    physical_examination_abdominal: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )
    physical_examination_neurological: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )

    assessment_scales: Mapped[Optional[str]] = mapped_column(UnicodeText)
    investigations_results: Mapped[Optional[str]] = mapped_column(UnicodeText)

    safety_alerts: Mapped[Optional[str]] = mapped_column(UnicodeText)
    risk_assessment: Mapped[Optional[str]] = mapped_column(UnicodeText)
    relevant_legal_information: Mapped[Optional[str]] = mapped_column(
        UnicodeText
    )

    current_problems: Mapped[Optional[str]] = mapped_column(UnicodeText)
    patient_carer_concerns: Mapped[Optional[str]] = mapped_column(UnicodeText)
    impression: Mapped[Optional[str]] = mapped_column(UnicodeText)
    management_plan: Mapped[Optional[str]] = mapped_column(UnicodeText)
    information_given: Mapped[Optional[str]] = mapped_column(UnicodeText)

    FIELDS_B = [
        "location",
        "contact_type",
        "reason_for_contact",
        "presenting_issue",
        "systems_review",
        "collateral_history",
    ]
    FIELDS_C = [
        "diagnoses_psychiatric",
        "diagnoses_medical",
        "operations_procedures",
        "allergies_adverse_reactions",
        "medications",
        "recreational_drug_use",
        "family_history",
        "developmental_history",
        "personal_history",
        "premorbid_personality",
        "forensic_history",
        "current_social_situation",
    ]
    FIELDS_MSE = [
        "mse_appearance_behaviour",
        "mse_speech",
        "mse_mood_subjective",
        "mse_mood_objective",
        "mse_thought_form",
        "mse_thought_content",
        "mse_perception",
        "mse_cognition",
        "mse_insight",
    ]
    FIELDS_PE = [
        "physical_examination_general",
        "physical_examination_cardiovascular",
        "physical_examination_respiratory",
        "physical_examination_abdominal",
        "physical_examination_neurological",
    ]
    FIELDS_D = ["assessment_scales", "investigations_results"]
    FIELDS_E = [
        "safety_alerts",
        "risk_assessment",
        "relevant_legal_information",
    ]
    FIELDS_F = [
        "current_problems",
        "patient_carer_concerns",
        "impression",
        "management_plan",
        "information_given",
    ]

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Psychiatric clerking")

    def get_ctv_heading(
        self, req: CamcopsRequest, wstringname: str
    ) -> CtvInfo:
        return CtvInfo(
            heading=self.wxstring(req, wstringname), skip_if_no_content=False
        )

    def get_ctv_subheading(
        self, req: CamcopsRequest, wstringname: str
    ) -> CtvInfo:
        return CtvInfo(
            subheading=self.wxstring(req, wstringname),
            skip_if_no_content=False,
        )

    def get_ctv_description_content(
        self, req: CamcopsRequest, x: str
    ) -> CtvInfo:
        return CtvInfo(
            description=self.wxstring(req, x),
            content=ws.webify(getattr(self, x)),
        )

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        infolist = [self.get_ctv_heading(req, "heading_current_contact")]
        for x in self.FIELDS_B:
            infolist.append(self.get_ctv_description_content(req, x))
        infolist.append(self.get_ctv_heading(req, "heading_background"))
        for x in self.FIELDS_C:
            infolist.append(self.get_ctv_description_content(req, x))
        infolist.append(
            self.get_ctv_heading(req, "heading_examination_investigations")
        )
        infolist.append(
            self.get_ctv_subheading(req, "mental_state_examination")
        )
        for x in self.FIELDS_MSE:
            infolist.append(self.get_ctv_description_content(req, x))
        infolist.append(self.get_ctv_subheading(req, "physical_examination"))
        for x in self.FIELDS_PE:
            infolist.append(self.get_ctv_description_content(req, x))
        infolist.append(
            self.get_ctv_subheading(req, "assessments_and_investigations")
        )
        for x in self.FIELDS_D:
            infolist.append(self.get_ctv_description_content(req, x))
        infolist.append(self.get_ctv_heading(req, "heading_risk_legal"))
        for x in self.FIELDS_E:
            infolist.append(self.get_ctv_description_content(req, x))
        infolist.append(self.get_ctv_heading(req, "heading_summary_plan"))
        for x in self.FIELDS_F:
            infolist.append(self.get_ctv_description_content(req, x))
        return infolist

    # noinspection PyMethodOverriding
    @staticmethod
    def is_complete() -> bool:
        return True

    def heading(self, req: CamcopsRequest, wstringname: str) -> str:
        return '<div class="{CssClass.HEADING}">{s}</div>'.format(
            CssClass=CssClass, s=self.wxstring(req, wstringname)
        )

    def subheading(self, req: CamcopsRequest, wstringname: str) -> str:
        return '<div class="{CssClass.SUBHEADING}">{s}</div>'.format(
            CssClass=CssClass, s=self.wxstring(req, wstringname)
        )

    def subsubheading(self, req: CamcopsRequest, wstringname: str) -> str:
        return '<div class="{CssClass.SUBSUBHEADING}">{s}</div>'.format(
            CssClass=CssClass, s=self.wxstring(req, wstringname)
        )

    def subhead_text(self, req: CamcopsRequest, fieldname: str) -> str:
        return self.subheading(req, fieldname) + "<div><b>{}</b></div>".format(
            ws.webify(getattr(self, fieldname))
        )

    def subsubhead_text(self, req: CamcopsRequest, fieldname: str) -> str:
        return (
            self.subsubheading(req, fieldname)
            + f"<div><b>{ws.webify(getattr(self, fieldname))}</b></div>"
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        # Avoid tables - PDF generator crashes if text is too long.
        html = ""
        html += self.heading(req, "heading_current_contact")
        for x in self.FIELDS_B:
            html += self.subhead_text(req, x)
        html += self.heading(req, "heading_background")
        for x in self.FIELDS_C:
            html += self.subhead_text(req, x)
        html += self.heading(req, "heading_examination_investigations")
        html += self.subheading(req, "mental_state_examination")
        for x in self.FIELDS_MSE:
            html += self.subsubhead_text(req, x)
        html += self.subheading(req, "physical_examination")
        for x in self.FIELDS_PE:
            html += self.subsubhead_text(req, x)
        for x in self.FIELDS_D:
            html += self.subhead_text(req, x)
        html += self.heading(req, "heading_risk_legal")
        for x in self.FIELDS_E:
            html += self.subhead_text(req, x)
        html += self.heading(req, "heading_summary_plan")
        for x in self.FIELDS_F:
            html += self.subhead_text(req, x)
        return html

    def get_snomed_codes(self, req: CamcopsRequest) -> List[SnomedExpression]:
        refinement = {}  # type: Dict[SnomedConcept, str]

        def add(snomed_lookup: str, contents: Optional[str]) -> None:
            if not contents:
                return
            nonlocal refinement
            concept = req.snomed(snomed_lookup)
            refinement[concept] = contents

        # not location
        # not contact type
        add(SnomedLookup.PSYCLERK_REASON_FOR_REFERRAL, self.reason_for_contact)
        add(SnomedLookup.PSYCLERK_PRESENTING_ISSUE, self.presenting_issue)
        add(SnomedLookup.PSYCLERK_SYSTEMS_REVIEW, self.systems_review)
        add(SnomedLookup.PSYCLERK_COLLATERAL_HISTORY, self.collateral_history)

        add(
            SnomedLookup.PSYCLERK_PAST_MEDICAL_SURGICAL_MENTAL_HEALTH_HISTORY,
            self.diagnoses_medical,
        )
        add(
            SnomedLookup.PSYCLERK_PAST_MEDICAL_SURGICAL_MENTAL_HEALTH_HISTORY,
            self.diagnoses_psychiatric,
        )
        add(SnomedLookup.PSYCLERK_PROCEDURES, self.operations_procedures)
        add(
            SnomedLookup.PSYCLERK_ALLERGIES_ADVERSE_REACTIONS,
            self.allergies_adverse_reactions,
        )
        add(
            SnomedLookup.PSYCLERK_MEDICATIONS_MEDICAL_DEVICES, self.medications
        )
        add(
            SnomedLookup.PSYCLERK_DRUG_SUBSTANCE_USE,
            self.recreational_drug_use,
        )
        add(SnomedLookup.PSYCLERK_FAMILY_HISTORY, self.family_history)
        add(
            SnomedLookup.PSYCLERK_DEVELOPMENTAL_HISTORY,
            self.developmental_history,
        )
        add(
            SnomedLookup.PSYCLERK_SOCIAL_PERSONAL_HISTORY,
            self.personal_history,
        )
        add(SnomedLookup.PSYCLERK_PERSONALITY, self.premorbid_personality)
        add(
            SnomedLookup.PSYCLERK_PRISON_RECORD_CRIMINAL_ACTIVITY,
            self.forensic_history,
        )
        add(
            SnomedLookup.PSYCLERK_SOCIAL_HISTORY_BASELINE,
            self.current_social_situation,
        )

        add(
            SnomedLookup.PSYCLERK_MSE_APPEARANCE, self.mse_appearance_behaviour
        )  # duplication
        add(
            SnomedLookup.PSYCLERK_MSE_BEHAVIOUR, self.mse_appearance_behaviour
        )  # duplication
        add(SnomedLookup.PSYCLERK_MSE_MOOD, self.mse_mood_subjective)  # close
        add(SnomedLookup.PSYCLERK_MSE_AFFECT, self.mse_mood_objective)
        # ... Logic here: "objective mood" is certainly affect (emotional
        # weather). "Subjective mood" is both mood (emotional climate) and
        # affect. Not perfect, but reasonable.
        add(SnomedLookup.PSYCLERK_MSE_THOUGHT, self.mse_thought_form)
        add(SnomedLookup.PSYCLERK_MSE_THOUGHT, self.mse_thought_content)
        # ... No way of disambiguating the two in SNOMED-CT.
        add(SnomedLookup.PSYCLERK_MSE_PERCEPTION, self.mse_perception)
        add(SnomedLookup.PSYCLERK_MSE_COGNITION, self.mse_cognition)
        add(SnomedLookup.PSYCLERK_MSE_INSIGHT, self.mse_insight)

        add(
            SnomedLookup.PSYCLERK_PHYSEXAM_GENERAL,
            self.physical_examination_general,
        )
        add(
            SnomedLookup.PSYCLERK_PHYSEXAM_CARDIOVASCULAR,
            self.physical_examination_cardiovascular,
        )
        add(
            SnomedLookup.PSYCLERK_PHYSEXAM_RESPIRATORY,
            self.physical_examination_respiratory,
        )
        add(
            SnomedLookup.PSYCLERK_PHYSEXAM_ABDOMINAL,
            self.physical_examination_abdominal,
        )
        add(
            SnomedLookup.PSYCLERK_PHYSEXAM_NEUROLOGICAL,
            self.physical_examination_neurological,
        )

        add(SnomedLookup.PSYCLERK_ASSESSMENT_SCALES, self.assessment_scales)
        add(
            SnomedLookup.PSYCLERK_INVESTIGATIONS_RESULTS,
            self.investigations_results,
        )

        add(SnomedLookup.PSYCLERK_SAFETY_ALERTS, self.safety_alerts)
        add(SnomedLookup.PSYCLERK_RISK_ASSESSMENT, self.risk_assessment)
        add(
            SnomedLookup.PSYCLERK_RELEVANT_LEGAL_INFORMATION,
            self.relevant_legal_information,
        )

        add(SnomedLookup.PSYCLERK_CURRENT_PROBLEMS, self.current_problems)
        add(
            SnomedLookup.PSYCLERK_PATIENT_CARER_CONCERNS,
            self.patient_carer_concerns,
        )
        add(SnomedLookup.PSYCLERK_CLINICAL_NARRATIVE, self.impression)
        add(SnomedLookup.PSYCLERK_MANAGEMENT_PLAN, self.management_plan)
        add(SnomedLookup.PSYCLERK_INFORMATION_GIVEN, self.information_given)

        codes = [
            SnomedExpression(
                req.snomed(
                    SnomedLookup.DIAGNOSTIC_PSYCHIATRIC_INTERVIEW_PROCEDURE
                ),
                refinement=refinement or None,  # type: ignore[arg-type]
            )
        ]
        return codes
