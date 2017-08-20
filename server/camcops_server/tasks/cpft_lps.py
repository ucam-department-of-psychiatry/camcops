#!/usr/bin/env python
# camcops_server/tasks/cpft_lps.py

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

from typing import Any, List, Optional

import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.sqlalchemy.core_query import get_rows_fieldnames_from_raw_sql  # noqa
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text

from ..cc_modules.cc_dt import format_datetime_string
from ..cc_modules.cc_constants import (
    DATEFORMAT,
    INVALID_VALUE,
    PARAM,
    PV,
)
from ..cc_modules.cc_ctvinfo import CtvInfo
from ..cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    subheading_spanning_four_columns,
    subheading_spanning_two_columns,
    tr_qa,
    tr_span_col,
)
from ..cc_modules.cc_nhs import (
    get_nhs_dd_ethnic_category_code,
    get_nhs_dd_person_marital_status,
    PV_NHS_ETHNIC_CATEGORY,
    PV_NHS_MARITAL_STATUS
)
from ..cc_modules.cc_report import Report, ReportParamSpec, REPORT_RESULT_TYPE
from ..cc_modules.cc_request import CamcopsRequest
from ..cc_modules.cc_sqla_coltypes import (
    BoolColumn,
    CamcopsColumn,
    CharColType,
    DateTimeAsIsoTextColType,
    PermittedValueChecker,
)
from ..cc_modules.cc_sqlalchemy import Base
from ..cc_modules.cc_task import (
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)


# =============================================================================
# CPFT_LPS_Referral
# =============================================================================

class CPFTLPSReferral(TaskHasPatientMixin, Task, Base):
    __tablename__ = "cpft_lps_referral"
    shortname = "CPFT_LPS_Referral"
    longname = "Referral to CPFT Liaison Psychiatry Service"

    referral_date_time = Column("referral_date_time", DateTimeAsIsoTextColType)
    lps_division = Column("lps_division", Text)
    referral_priority = Column("referral_priority", Text)
    referral_method = Column("referral_method", Text)
    referrer_name = Column("referrer_name", Text)
    referrer_contact_details = Column("referrer_contact_details", Text)
    referring_consultant = Column("referring_consultant", Text)
    referring_specialty = Column("referring_specialty", Text)
    referring_specialty_other = Column("referring_specialty_other", Text)
    patient_location = Column("patient_location", Text)
    admission_date = Column("admission_date", DateTimeAsIsoTextColType)
    estimated_discharge_date = Column(
        "estimated_discharge_date", DateTimeAsIsoTextColType
    )
    patient_aware_of_referral = BoolColumn("patient_aware_of_referral")
    interpreter_required = BoolColumn("interpreter_required")
    sensory_impairment = BoolColumn("sensory_impairment")
    marital_status_code = CamcopsColumn(
        "marital_status_code", CharColType,
        permitted_value_checker=PermittedValueChecker(
            permitted_values=PV_NHS_MARITAL_STATUS)
    )
    ethnic_category_code = CamcopsColumn(
        "ethnic_category_code", CharColType,
        permitted_value_checker=PermittedValueChecker(
            permitted_values=PV_NHS_ETHNIC_CATEGORY)
    )
    admission_reason_overdose = BoolColumn("admission_reason_overdose")
    admission_reason_self_harm_not_overdose = BoolColumn(
        "admission_reason_self_harm_not_overdose"
    )
    admission_reason_confusion = BoolColumn("admission_reason_confusion")
    admission_reason_trauma = BoolColumn("admission_reason_trauma")
    admission_reason_falls = BoolColumn("admission_reason_falls")
    admission_reason_infection = BoolColumn("admission_reason_infection")
    admission_reason_poor_adherence = BoolColumn(
        "admission_reason_poor_adherence"
    )
    admission_reason_other = BoolColumn("admission_reason_other")
    existing_psychiatric_teams = Column("existing_psychiatric_teams", Text)
    care_coordinator = Column("care_coordinator", Text)
    other_contact_details = Column("other_contact_details", Text)
    referral_reason = Column("referral_reason", Text)

    def is_complete(self) -> bool:
        return (
            self.patient_location and
            self.referral_reason and
            self.field_contents_valid()
        )

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        return [CtvInfo(
            heading=ws.webify(self.wxstring(req, "f_referral_reason_t")),
            content=self.referral_reason
        )]

    @staticmethod
    def four_column_row(q1: str, a1: Any,
                        q2: str, a2: Any,
                        default: str = "") -> str:
        return """
            <tr>
                <td>{}</td><td>{}</td>
                <td>{}</td><td>{}</td>
            </tr>
        """.format(
            q1,
            answer(a1, default=default),
            q2,
            answer(a2, default=default),
        )

    @staticmethod
    def tr_qa(q: str, a: Any, default: str = "") -> str:
        return """
            <tr><td colspan="2">{}</td><td colspan="2"><b>{}</b></td></tr>
        """.format(q, default if a is None else a)

    def get_task_html(self, req: CamcopsRequest) -> str:
        person_marital_status = get_nhs_dd_person_marital_status(req)
        ethnic_category_code = get_nhs_dd_ethnic_category_code(req)
        if self.lps_division == "G":
            banner_class = "banner_referral_general_adult"
            division_name = self.wxstring(req, "service_G")
        elif self.lps_division == "O":
            banner_class = "banner_referral_old_age"
            division_name = self.wxstring(req, "service_O")
        elif self.lps_division == "S":
            banner_class = "banner_referral_substance_misuse"
            division_name = self.wxstring(req, "service_S")
        else:
            banner_class = ""
            division_name = None

        if self.referral_priority == "R":
            priority_name = self.wxstring(req, "priority_R")
        elif self.referral_priority == "U":
            priority_name = self.wxstring(req, "priority_U")
        elif self.referral_priority == "E":
            priority_name = self.wxstring(req, "priority_E")
        else:
            priority_name = None

        potential_admission_reasons = [
            "admission_reason_overdose",
            "admission_reason_self_harm_not_overdose",
            "admission_reason_confusion",
            "admission_reason_trauma",
            "admission_reason_falls",
            "admission_reason_infection",
            "admission_reason_poor_adherence",
            "admission_reason_other",
        ]
        admission_reasons = []
        for r in potential_admission_reasons:
            if getattr(self, r):
                admission_reasons.append(self.wxstring(req, "f_" + r))

        h = """
            <div class="banner {}">{} referral at {}</div>
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <table class="taskdetail">
                <col width="25%">
                <col width="25%">
                <col width="25%">
                <col width="25%">
        """.format(
            banner_class,
            answer(division_name, default_for_blank_strings=True),
            answer(format_datetime_string(
                self.referral_date_time,
                DATEFORMAT.SHORT_DATETIME_WITH_DAY_NO_TZ,
                default=None)),
            self.get_is_complete_tr(),
        )
        h += subheading_spanning_four_columns(
            self.wxstring(req, "t_about_referral"))
        h += """
            <tr>
                <td>{}</td><td>{}</td>
                <td>{}</td><td class="highlight">{}</td>
            </tr>
        """.format(
            self.wxstring(req, "f_referral_method"),
            answer(self.referral_method),
            self.wxstring(req, "f_referral_priority"),
            answer(self.referral_priority, default_for_blank_strings=True) +
            ": " + answer(priority_name)
        )
        h += self.four_column_row(
            self.wxstring(req, "f_referrer_name"),
            self.referrer_name,
            self.wxstring(req, "f_referring_specialty"),
            self.referring_specialty
        )
        h += self.four_column_row(
            self.wxstring(req, "f_referrer_contact_details"),
            self.referrer_contact_details,
            self.wxstring(req, "f_referring_specialty_other"),
            self.referring_specialty_other
        )
        h += self.four_column_row(
            self.wxstring(req, "f_referring_consultant"),
            self.referring_consultant,
            "",
            ""
        )
        h += subheading_spanning_four_columns(
            self.wxstring(req, "t_patient"))
        h += """
            <tr>
                <td>{}</td><td>{}</td>
                <td>{}</td><td class="highlight">{}</td>
            </tr>
        """.format(
            self.wxstring(req, "f_admission_date"),
            answer(format_datetime_string(self.admission_date,
                                          DATEFORMAT.LONG_DATE,
                                          default=None), ""),
            self.wxstring(req, "f_patient_location"),
            answer(self.patient_location)
        )
        h += self.four_column_row(
            self.wxstring(req, "f_estimated_discharge_date"),
            format_datetime_string(self.estimated_discharge_date,
                                   DATEFORMAT.LONG_DATE, ""),
            self.wxstring(req, "f_patient_aware_of_referral"),
            get_yes_no_none(self.patient_aware_of_referral)
        )
        h += self.four_column_row(
            self.wxstring(req, "f_marital_status"),
            person_marital_status.get(self.marital_status_code, INVALID_VALUE),
            self.wxstring(req, "f_interpreter_required"),
            get_yes_no_none(self.interpreter_required)
        )
        h += self.four_column_row(
            self.wxstring(req, "f_ethnic_category"),
            ethnic_category_code.get(self.ethnic_category_code, INVALID_VALUE),
            self.wxstring(req, "f_sensory_impairment"),
            get_yes_no_none(self.sensory_impairment)
        )
        h += subheading_spanning_four_columns(
            self.wxstring(req, "t_admission_reason"))
        h += tr_span_col(answer(", ".join(admission_reasons), ""), cols=4)
        h += subheading_spanning_four_columns(
            self.wxstring(req, "t_other_people"))
        h += self.tr_qa(
            self.wxstring(req, "f_existing_psychiatric_teams"),
            self.existing_psychiatric_teams, "")
        h += self.tr_qa(
            self.wxstring(req, "f_care_coordinator"),
            self.care_coordinator, "")
        h += self.tr_qa(
            self.wxstring(req, "f_other_contact_details"),
            self.other_contact_details, "")
        h += subheading_spanning_four_columns(
            self.wxstring(req, "t_referral_reason"))
        h += tr_span_col(answer(self.referral_reason, ""), cols=4)
        h += """
            </table>
        """
        return h


# =============================================================================
# CPFT_LPS_ResetResponseClock
# =============================================================================

class CPFTLPSResetResponseClock(TaskHasPatientMixin, TaskHasClinicianMixin, 
                                Task, Base):
    __tablename__ = "cpft_lps_resetresponseclock"
    shortname = "CPFT_LPS_ResetResponseClock"
    longname = "Reset response clock (CPFT Liaison Psychiatry Service)"

    reset_start_time_to = Column(
        "reset_start_time_to", DateTimeAsIsoTextColType
    )
    reason = Column("reason", Text)

    def is_complete(self) -> bool:
        return (
            self.reset_start_time_to and
            self.reason and
            self.field_contents_valid()
        )

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        return [CtvInfo(content=self.reason)]

    def get_task_html(self, req: CamcopsRequest) -> str:
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <table class="taskdetail">
                <col width="25%">
                <col width="75%">
        """.format(
            self.get_is_complete_tr(),
        )
        h += tr_qa(
            self.wxstring(req, "to"),
            format_datetime_string(self.reset_start_time_to,
                                   DATEFORMAT.LONG_DATETIME_WITH_DAY,
                                   default=None))
        h += tr_qa(self.wxstring(req, "reason"), self.reason)
        h += """
            </table>
        """
        return h


# =============================================================================
# CPFT_LPS_Discharge
# =============================================================================

class CPFTLPSDischarge(TaskHasPatientMixin, TaskHasClinicianMixin, Task, Base):
    __tablename__ = "cpft_lps_discharge"
    shortname = "CPFT_LPS_Discharge"
    longname = "Discharge from CPFT Liaison Psychiatry Service"

    discharge_date = Column("discharge_date", DateTimeAsIsoTextColType)
    discharge_reason_code = Column("discharge_reason_code", Text)

    leaflet_or_discharge_card_given = BoolColumn(
        "leaflet_or_discharge_card_given"
    )
    frequent_attender = BoolColumn("frequent_attender")
    patient_wanted_copy_of_letter = Column(
        # *** It's odd that this is text. Fix it. Tablet now using bool.
        # *** ONCE ALEMBIC UP, change from Text to Bool.
        "patient_wanted_copy_of_letter", Text
    )
    gaf_at_first_assessment = CamcopsColumn(
        "gaf_at_first_assessment", Integer,
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=100)
    )
    gaf_at_discharge = CamcopsColumn(
        "gaf_at_discharge", Integer,
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=100)
    )

    referral_reason_self_harm_overdose = BoolColumn(
        "referral_reason_self_harm_overdose"
    )
    referral_reason_self_harm_other = BoolColumn(
        "referral_reason_self_harm_other"
    )
    referral_reason_suicidal_ideas = BoolColumn(
        "referral_reason_suicidal_ideas"
    )
    referral_reason_behavioural_disturbance = BoolColumn(
        "referral_reason_behavioural_disturbance"
    )
    referral_reason_low_mood = BoolColumn("referral_reason_low_mood")
    referral_reason_elevated_mood = BoolColumn("referral_reason_elevated_mood")
    referral_reason_psychosis = BoolColumn("referral_reason_psychosis")
    referral_reason_pre_transplant = BoolColumn(
        "referral_reason_pre_transplant"
    )
    referral_reason_post_transplant = BoolColumn(
        "referral_reason_post_transplant"
    )
    referral_reason_delirium = BoolColumn("referral_reason_delirium")
    referral_reason_anxiety = BoolColumn("referral_reason_anxiety")
    referral_reason_somatoform_mus = BoolColumn(
        "referral_reason_somatoform_mus"
    )
    referral_reason_motivation_adherence = BoolColumn(
        "referral_reason_motivation_adherence"
    )
    referral_reason_capacity = BoolColumn("referral_reason_capacity")
    referral_reason_eating_disorder = BoolColumn(
        "referral_reason_eating_disorder"
    )
    referral_reason_safeguarding = BoolColumn("referral_reason_safeguarding")
    referral_reason_discharge_placement = BoolColumn(
        "referral_reason_discharge_placement"
    )
    referral_reason_cognitive_problem = BoolColumn(
        "referral_reason_cognitive_problem"
    )
    referral_reason_substance_alcohol = BoolColumn(
        "referral_reason_substance_alcohol"
    )
    referral_reason_substance_other = BoolColumn(
        "referral_reason_substance_other"
    )
    referral_reason_other = BoolColumn("referral_reason_other")
    referral_reason_transplant_organ = Column(
        "referral_reason_transplant_organ", Text
    )
    referral_reason_other_detail = Column("referral_reason_other_detail", Text)

    diagnosis_no_active_mental_health_problem = BoolColumn(
        "diagnosis_no_active_mental_health_problem"
    )
    diagnosis_psych_1_icd10code = Column("diagnosis_psych_1_icd10code", Text)
    diagnosis_psych_1_description = Column(
        "diagnosis_psych_1_description", Text
    )
    diagnosis_psych_2_icd10code = Column("diagnosis_psych_2_icd10code", Text)
    diagnosis_psych_2_description = Column(
        "diagnosis_psych_2_description", Text
    )
    diagnosis_psych_3_icd10code = Column("diagnosis_psych_3_icd10code", Text)
    diagnosis_psych_3_description = Column(
        "diagnosis_psych_3_description", Text
    )
    diagnosis_psych_4_icd10code = Column("diagnosis_psych_4_icd10code", Text)
    diagnosis_psych_4_description = Column(
        "diagnosis_psych_4_description", Text
    )
    diagnosis_medical_1 = Column("diagnosis_medical_1", Text)
    diagnosis_medical_2 = Column("diagnosis_medical_2", Text)
    diagnosis_medical_3 = Column("diagnosis_medical_3", Text)
    diagnosis_medical_4 = Column("diagnosis_medical_4", Text)

    management_assessment_diagnostic = BoolColumn(
        "management_assessment_diagnostic"
    )
    management_medication = BoolColumn("management_medication")
    management_specialling_behavioural_disturbance = BoolColumn(
        "management_specialling_behavioural_disturbance"
    )
    management_supportive_patient = BoolColumn("management_supportive_patient")
    management_supportive_carers = BoolColumn("management_supportive_carers")
    management_supportive_staff = BoolColumn("management_supportive_staff")
    management_nursing_management = BoolColumn("management_nursing_management")
    management_therapy_cbt = BoolColumn("management_therapy_cbt")
    management_therapy_cat = BoolColumn("management_therapy_cat")
    management_therapy_other = BoolColumn("management_therapy_other")
    management_treatment_adherence = BoolColumn(
        "management_treatment_adherence"
    )
    management_capacity = BoolColumn("management_capacity")
    management_education_patient = BoolColumn("management_education_patient")
    management_education_carers = BoolColumn("management_education_carers")
    management_education_staff = BoolColumn("management_education_staff")
    management_accommodation_placement = BoolColumn(
        "management_accommodation_placement")
    management_signposting_external_referral = BoolColumn(
        "management_signposting_external_referral")
    management_mha_s136 = BoolColumn("management_mha_s136")
    management_mha_s5_2 = BoolColumn("management_mha_s5_2")
    management_mha_s2 = BoolColumn("management_mha_s2")
    management_mha_s3 = BoolColumn("management_mha_s3")
    management_complex_case_conference = BoolColumn(
        "management_complex_case_conference"
    )
    management_other = BoolColumn("management_other")
    management_other_detail = Column("management_other_detail", Text)

    outcome = Column("outcome", Text)
    outcome_hospital_transfer_detail = Column(
        "outcome_hospital_transfer_detail", Text
    )
    outcome_other_detail = Column("outcome_other_detail", Text)

    def is_complete(self) -> bool:
        return (
            self.discharge_date and
            self.discharge_reason_code and
            # self.outcome and  # v2.0.0
            self.field_contents_valid()
        )

    def get_discharge_reason(self) -> Optional[str]:
        if self.discharge_reason_code == "F":
            return self.wxstring(req, "reason_code_F")
        elif self.discharge_reason_code == "A":
            return self.wxstring(req, "reason_code_A")
        elif self.discharge_reason_code == "O":
            return self.wxstring(req, "reason_code_O")
        elif self.discharge_reason_code == "C":
            return self.wxstring(req, "reason_code_C")
        else:
            return None

    def get_referral_reasons(self) -> List[str]:
        potential_referral_reasons = [
            "referral_reason_self_harm_overdose",
            "referral_reason_self_harm_other",
            "referral_reason_suicidal_ideas",
            "referral_reason_behavioural_disturbance",
            "referral_reason_low_mood",
            "referral_reason_elevated_mood",
            "referral_reason_psychosis",
            "referral_reason_pre_transplant",
            "referral_reason_post_transplant",
            "referral_reason_delirium",
            "referral_reason_anxiety",
            "referral_reason_somatoform_mus",
            "referral_reason_motivation_adherence",
            "referral_reason_capacity",
            "referral_reason_eating_disorder",
            "referral_reason_safeguarding",
            "referral_reason_discharge_placement",
            "referral_reason_cognitive_problem",
            "referral_reason_substance_alcohol",
            "referral_reason_substance_other",
            "referral_reason_other",
        ]
        referral_reasons = []
        for r in potential_referral_reasons:
            if getattr(self, r):
                referral_reasons.append(self.wxstring(req, "" + r))
        return referral_reasons

    def get_managements(self) -> List[str]:
        potential_managements = [
            "management_assessment_diagnostic",
            "management_medication",
            "management_specialling_behavioural_disturbance",
            "management_supportive_patient",
            "management_supportive_carers",
            "management_supportive_staff",
            "management_nursing_management",
            "management_therapy_cbt",
            "management_therapy_cat",
            "management_therapy_other",
            "management_treatment_adherence",
            "management_capacity",
            "management_education_patient",
            "management_education_carers",
            "management_education_staff",
            "management_accommodation_placement",
            "management_signposting_external_referral",
            "management_mha_s136",
            "management_mha_s5_2",
            "management_mha_s2",
            "management_mha_s3",
            "management_complex_case_conference",
            "management_other",
        ]
        managements = []
        for r in potential_managements:
            if getattr(self, r):
                managements.append(self.wxstring(req, "" + r))
        return managements

    def get_psychiatric_diagnoses(self) -> List[str]:
        psychiatric_diagnoses = [
            self.wxstring(req, "diagnosis_no_active_mental_health_problem")
        ] if self.diagnosis_no_active_mental_health_problem else []
        for i in range(1, 4 + 1):  # magic number
            if getattr(self, "diagnosis_psych_" + str(i) + "_icd10code"):
                psychiatric_diagnoses.append(
                    ws.webify(getattr(self, "diagnosis_psych_" +
                                      str(i) + "_icd10code")) +
                    " – " +
                    ws.webify(getattr(self, "diagnosis_psych_" +
                                      str(i) + "_description"))
                )
        return psychiatric_diagnoses

    def get_medical_diagnoses(self) -> List[str]:
        medical_diagnoses = []
        for i in range(1, 4 + 1):  # magic number
            if getattr(self, "diagnosis_medical_" + str(i)):
                medical_diagnoses.append(
                    ws.webify(getattr(self, "diagnosis_medical_" + str(i))))
        return medical_diagnoses

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        diagnoses = self.get_psychiatric_diagnoses() + \
            self.get_medical_diagnoses()
        return [
            CtvInfo(
                heading=ws.webify(self.wxstring(req, "discharge_reason")),
                content=self.get_discharge_reason()
            ),
            CtvInfo(
                heading=ws.webify(
                    self.wxstring(req, "referral_reason_t")),
                content=", ".join(self.get_referral_reasons())
            ),
            CtvInfo(
                heading=ws.webify(self.wxstring(req, "diagnoses_t")),
                content=", ".join(diagnoses)
            ),
            CtvInfo(
                heading=ws.webify(self.wxstring(req, "management_t")),
                content=", ".join(self.get_managements())
            ),
            CtvInfo(
                heading=ws.webify(self.wxstring(req, "outcome_t")),
                content=self.outcome
            ),
        ]

    def get_task_html(self, req: CamcopsRequest) -> str:
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <table class="taskdetail">
                <col width="40%">
                <col width="60%">
        """.format(
            self.get_is_complete_tr(),
        )
        h += tr_qa(self.wxstring(req, "discharge_date"),
                   format_datetime_string(self.discharge_date,
                                          DATEFORMAT.LONG_DATE_WITH_DAY,
                                          default=None), "")
        h += tr_qa(self.wxstring(req, "discharge_reason"),
                   self.get_discharge_reason(), "")
        h += tr_qa(self.wxstring(req, "leaflet_or_discharge_card_given"),
                   get_yes_no_none(self.leaflet_or_discharge_card_given), "")
        h += tr_qa(self.wxstring(req, "frequent_attender"),
                   get_yes_no_none(self.frequent_attender), "")
        h += tr_qa(self.wxstring(req, "patient_wanted_copy_of_letter"),
                   self.patient_wanted_copy_of_letter, "")
        h += tr_qa(self.wxstring(req, "gaf_at_first_assessment"),
                   self.gaf_at_first_assessment, "")
        h += tr_qa(self.wxstring(req, "gaf_at_discharge"),
                   self.gaf_at_discharge, "")

        h += subheading_spanning_two_columns(
            self.wxstring(req, "referral_reason_t"))
        h += tr_span_col(answer(", ".join(self.get_referral_reasons())),
                         cols=2)
        h += tr_qa(self.wxstring(req, "referral_reason_transplant_organ"),
                   self.referral_reason_transplant_organ, "")
        h += tr_qa(self.wxstring(req, "referral_reason_other_detail"),
                   self.referral_reason_other_detail, "")

        h += subheading_spanning_two_columns(
            self.wxstring(req, "diagnoses_t"))
        h += tr_qa(self.wxstring(req, "psychiatric_t"),
                   "<br>".join(self.get_psychiatric_diagnoses()), "")
        h += tr_qa(self.wxstring(req, "medical_t"),
                   "<br>".join(self.get_medical_diagnoses()), "")

        h += subheading_spanning_two_columns(self.wxstring(req, "management_t"))
        h += tr_span_col(answer(", ".join(self.get_managements())), cols=2)
        h += tr_qa(self.wxstring(req, "management_other_detail"),
                   self.management_other_detail, "")

        h += subheading_spanning_two_columns(self.wxstring(req, "outcome_t"))
        h += tr_qa(self.wxstring(req, "outcome_t"),
                   self.outcome, "")
        h += tr_qa(self.wxstring(req, "outcome_hospital_transfer_detail"),
                   self.outcome_hospital_transfer_detail, "")
        h += tr_qa(self.wxstring(req, "outcome_other_detail"),
                   self.outcome_other_detail, "")

        h += """
            </table>
        """
        return h

# =============================================================================
# Reports
# =============================================================================

ID_NUMBER_TO_LINK_ON_LABEL = "ID number to link on?"


class LPSReportReferredNotDischarged(Report):
    report_id = "cpft_lps_referred_not_subsequently_discharged"
    report_title = "CPFT LPS – referred but not yet discharged"
    param_spec_list = [ReportParamSpec(type=PARAM.WHICH_IDNUM,
                                       name="linking_idnum",
                                       label=ID_NUMBER_TO_LINK_ON_LABEL)]

    def get_rows_descriptions(self,
                              req: CamcopsRequest,
                              **kwargs: Any) -> REPORT_RESULT_TYPE:
        linking_idnum = kwargs.pop("linking_idnum", None)  # type: int
        if linking_idnum is None:
            return [], []
        sql = """
            SELECT
                r.lps_division,
                r.referral_date_time,
                r.referral_priority,
                p1.surname,
                p1.forename,
                p1.dob,
                r.patient_location
            FROM
                patient p1,
                cpft_lps_referral r
            WHERE
                /* standard criteria */
                p1._current
                AND r._current
                AND r.patient_id = p1.id
                AND r._device_id = p1._device_id
                AND r._era = p1._era
                /* not yet discharged */
                AND NOT EXISTS (
                    SELECT *
                    FROM
                        patient p2,
                        cpft_lps_discharge d
                    WHERE
                        /* link on ID */
                        p2.idnum{0} = p1.idnum{0}
                        /* discharge later than referral */
                        AND LEFT(d.discharge_date, 10) >=
                            LEFT(r.referral_date_time, 10)
                        /* standard criteria */
                        AND p2._current
                        AND d._current
                        AND d.patient_id = p2.id
                        AND d._device_id = p2._device_id
                        AND d._era = p2._era
                )
            ORDER BY
                r.lps_division,
                r.referral_date_time,
                r.referral_priority
        """.format(linking_idnum)
        dbsession = req.dbsession
        rows, fieldnames = get_rows_fieldnames_from_raw_sql(dbsession, sql)
        return rows, fieldnames


class LPSReportReferredNotClerkedOrDischarged(Report):
    report_id = "cpft_lps_referred_not_subsequently_clerked_or_discharged"
    report_title = ("CPFT LPS – referred but not yet fully assessed or "
                    "discharged")
    param_spec_list = [ReportParamSpec(type=PARAM.WHICH_IDNUM,
                                       name="linking_idnum",
                                       label=ID_NUMBER_TO_LINK_ON_LABEL)]

    def get_rows_descriptions(self,
                              req: CamcopsRequest,
                              **kwargs: Any) -> REPORT_RESULT_TYPE:
        linking_idnum = kwargs.pop("linking_idnum", None)  # type: int
        if linking_idnum is None:
            return [], []
        sql = """
            SELECT
                r.lps_division,
                r.referral_date_time,
                r.referral_priority,
                p1.surname,
                p1.forename,
                p1.dob,
                r.patient_location
            FROM
                patient p1,
                cpft_lps_referral r
            WHERE
                /* standard criteria */
                p1._current
                AND r._current
                AND r.patient_id = p1.id
                AND r._device_id = p1._device_id
                AND r._era = p1._era
                /* not yet discharged */
                AND NOT EXISTS (
                    SELECT *
                    FROM
                        patient p2,
                        cpft_lps_discharge d
                    WHERE
                        /* link on ID */
                        p2.idnum{0} = p1.idnum{0}
                        /* discharge later than referral */
                        AND LEFT(d.discharge_date, 10) >=
                            LEFT(r.referral_date_time, 10)
                        /* standard criteria */
                        AND p2._current
                        AND d._current
                        AND d.patient_id = p2.id
                        AND d._device_id = p2._device_id
                        AND d._era = p2._era
                )
                /* not yet clerked */
                AND NOT EXISTS (
                    SELECT *
                    FROM
                        patient p2,
                        psychiatricclerking c
                    WHERE
                        /* link on ID */
                        p2.idnum{0} = p1.idnum{0}
                        /* clerking later than referral */
                        AND LEFT(c.when_created, 10) >=
                            LEFT(r.referral_date_time, 10)
                        /* standard criteria */
                        AND p2._current
                        AND c._current
                        AND c.patient_id = p2.id
                        AND c._device_id = p2._device_id
                        AND c._era = p2._era
                )
            ORDER BY
                r.lps_division,
                r.referral_date_time,
                r.referral_priority
        """.format(linking_idnum)
        dbsession = req.dbsession
        rows, fieldnames = get_rows_fieldnames_from_raw_sql(dbsession, sql)
        return rows, fieldnames
