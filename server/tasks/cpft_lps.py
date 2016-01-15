#!/usr/bin/env python3
# cpft_lps.py

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

import pythonlib.rnc_web as ws
from cc_modules.cc_constants import (
    CLINICIAN_FIELDSPECS,
    DATEFORMAT,
    INVALID_VALUE,
    PARAM,
    PV,
    STANDARD_TASK_FIELDSPECS,
)
from cc_modules.cc_dt import format_datetime_string
from cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    subheading_spanning_four_columns,
    subheading_spanning_two_columns,
    tr_qa,
    tr_span_col,
)
from cc_modules.cc_nhs import (
    get_nhs_dd_ethnic_category_code,
    get_nhs_dd_person_marital_status,
    PV_NHS_ETHNIC_CATEGORY,
    PV_NHS_MARITAL_STATUS
)
from cc_modules.cc_pls import pls
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import Task
from cc_modules.cc_report import Report


# =============================================================================
# CPFT_LPS_Referral
# =============================================================================

class CPFT_LPS_Referral(Task):
    TASK_FIELDSPECS = [
        dict(name="referral_date_time", cctype="ISO8601"),
        dict(name="lps_division", cctype="TEXT"),
        dict(name="referral_priority", cctype="TEXT"),
        dict(name="referral_method", cctype="TEXT"),
        dict(name="referrer_name", cctype="TEXT"),
        dict(name="referrer_contact_details", cctype="TEXT"),
        dict(name="referring_consultant", cctype="TEXT"),
        dict(name="referring_specialty", cctype="TEXT"),
        dict(name="referring_specialty_other", cctype="TEXT"),

        dict(name="patient_location", cctype="TEXT"),
        dict(name="admission_date", cctype="ISO8601"),
        dict(name="estimated_discharge_date", cctype="ISO8601"),
        dict(name="patient_aware_of_referral", cctype="BOOL",
             pv=PV.BIT),
        dict(name="interpreter_required", cctype="BOOL", pv=PV.BIT),
        dict(name="sensory_impairment", cctype="BOOL", pv=PV.BIT),
        dict(name="marital_status_code", cctype="INT",
             pv=PV_NHS_MARITAL_STATUS),
        dict(name="ethnic_category_code", cctype="INT",
             pv=PV_NHS_ETHNIC_CATEGORY),

        dict(name="admission_reason_overdose", cctype="BOOL",
             pv=PV.BIT),
        dict(name="admission_reason_self_harm_not_overdose",
             cctype="BOOL", pv=PV.BIT),
        dict(name="admission_reason_confusion", cctype="BOOL",
             pv=PV.BIT),
        dict(name="admission_reason_trauma", cctype="BOOL", pv=PV.BIT),
        dict(name="admission_reason_falls", cctype="BOOL", pv=PV.BIT),
        dict(name="admission_reason_infection", cctype="BOOL",
             pv=PV.BIT),
        dict(name="admission_reason_poor_adherence", cctype="BOOL",
             pv=PV.BIT),
        dict(name="admission_reason_other", cctype="BOOL", pv=PV.BIT),

        dict(name="existing_psychiatric_teams", cctype="TEXT"),
        dict(name="care_coordinator", cctype="TEXT"),
        dict(name="other_contact_details", cctype="TEXT"),

        dict(name="referral_reason", cctype="TEXT"),
    ]
    for d in TASK_FIELDSPECS:
        d["comment"] = d["name"]

    @classmethod
    def get_tablename(cls):
        return "cpft_lps_referral"

    @classmethod
    def get_taskshortname(cls):
        return "CPFT_LPS_Referral"

    @classmethod
    def get_tasklongname(cls):
        return "Referral to CPFT Liaison Psychiatry Service"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CPFT_LPS_Referral.TASK_FIELDSPECS

    def is_complete(self):
        return (
            self.patient_location
            and self.referral_reason
            and self.field_contents_valid()
        )

    def get_clinical_text(self):
        return [{
            "heading": ws.webify(WSTRING(
                "cpft_lps_referral_f_referral_reason")),
            "content": self.referral_reason
        }]

    def four_column_row(self, q1, a1, q2, a2, default=""):
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

    def tr_qa(self, q, a, default=""):
        return """
            <tr><td colspan="2">{}</td><td colspan="2"><b>{}</b></td></tr>
        """.format(q, default if a is None else a)

    def get_task_html(self):
        PERSON_MARITAL_STATUS = get_nhs_dd_person_marital_status()
        ETHNIC_CATEGORY_CODE = get_nhs_dd_ethnic_category_code()
        if self.lps_division == "G":
            banner_class = "banner_referral_general_adult"
            division_name = WSTRING("cpft_lps_service_G")
        elif self.lps_division == "O":
            banner_class = "banner_referral_old_age"
            division_name = WSTRING("cpft_lps_service_O")
        elif self.lps_division == "S":
            banner_class = "banner_referral_substance_misuse"
            division_name = WSTRING("cpft_lps_service_S")
        else:
            banner_class = ""
            division_name = None

        if self.referral_priority == "R":
            priority_name = WSTRING("cpft_lps_referral_priority_R")
        elif self.referral_priority == "U":
            priority_name = WSTRING("cpft_lps_referral_priority_U")
        elif self.referral_priority == "E":
            priority_name = WSTRING("cpft_lps_referral_priority_E")
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
                admission_reasons.append(WSTRING("cpft_lps_referral_f_" + r))

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
            WSTRING("cpft_lps_referral_t_about_referral"))
        h += """
            <tr>
                <td>{}</td><td>{}</td>
                <td>{}</td><td class="highlight">{}</td>
            </tr>
        """.format(
            WSTRING("cpft_lps_referral_f_referral_method"),
            answer(self.referral_method),
            WSTRING("cpft_lps_referral_f_referral_priority"),
            answer(self.referral_priority, default_for_blank_strings=True)
            + ": " + answer(priority_name)
        )
        h += self.four_column_row(
            WSTRING("cpft_lps_referral_f_referrer_name"),
            self.referrer_name,
            WSTRING("cpft_lps_referral_f_referring_specialty"),
            self.referring_specialty
        )
        h += self.four_column_row(
            WSTRING("cpft_lps_referral_f_referrer_contact_details"),
            self.referrer_contact_details,
            WSTRING("cpft_lps_referral_f_referring_specialty_other"),
            self.referring_specialty_other
        )
        h += self.four_column_row(
            WSTRING("cpft_lps_referral_f_referring_consultant"),
            self.referring_consultant,
            "",
            ""
        )
        h += subheading_spanning_four_columns(
            WSTRING("cpft_lps_referral_t_patient"))
        h += """
            <tr>
                <td>{}</td><td>{}</td>
                <td>{}</td><td class="highlight">{}</td>
            </tr>
        """.format(
            WSTRING("cpft_lps_referral_f_admission_date"),
            answer(format_datetime_string(self.admission_date,
                                          DATEFORMAT.LONG_DATE,
                                          default=None), ""),
            WSTRING("cpft_lps_referral_f_patient_location"),
            answer(self.patient_location)
        )
        h += self.four_column_row(
            WSTRING("cpft_lps_referral_f_estimated_discharge_date"),
            format_datetime_string(self.estimated_discharge_date,
                                   DATEFORMAT.LONG_DATE, ""),
            WSTRING("cpft_lps_referral_f_patient_aware_of_referral"),
            get_yes_no_none(self.patient_aware_of_referral)
        )
        h += self.four_column_row(
            WSTRING("cpft_lps_referral_f_marital_status"),
            PERSON_MARITAL_STATUS.get(self.marital_status_code, INVALID_VALUE),
            WSTRING("cpft_lps_referral_f_interpreter_required"),
            get_yes_no_none(self.interpreter_required)
        )
        h += self.four_column_row(
            WSTRING("cpft_lps_referral_f_ethnic_category"),
            ETHNIC_CATEGORY_CODE.get(self.ethnic_category_code, INVALID_VALUE),
            WSTRING("cpft_lps_referral_f_sensory_impairment"),
            get_yes_no_none(self.sensory_impairment)
        )
        h += subheading_spanning_four_columns(
            WSTRING("cpft_lps_referral_t_admission_reason"))
        h += tr_span_col(answer(", ".join(admission_reasons), ""), cols=4)
        h += subheading_spanning_four_columns(
            WSTRING("cpft_lps_referral_t_other_people"))
        h += self.tr_qa(
            WSTRING("cpft_lps_referral_f_existing_psychiatric_teams"),
            self.existing_psychiatric_teams, "")
        h += self.tr_qa(
            WSTRING("cpft_lps_referral_f_care_coordinator"),
            self.care_coordinator, "")
        h += self.tr_qa(
            WSTRING("cpft_lps_referral_f_other_contact_details"),
            self.other_contact_details, "")
        h += subheading_spanning_four_columns(
            WSTRING("cpft_lps_referral_t_referral_reason"))
        h += tr_span_col(answer(self.referral_reason, ""), cols=4)
        h += """
            </table>
        """
        return h


# =============================================================================
# CPFT_LPS_ResetResponseClock
# =============================================================================

class CPFT_LPS_ResetResponseClock(Task):
    TASK_FIELDSPECS = (CLINICIAN_FIELDSPECS + [
        dict(name="reset_start_time_to", cctype="ISO8601"),
        dict(name="reason", cctype="TEXT"),
    ])
    for d in TASK_FIELDSPECS:
        if "comment" not in d:
            d["comment"] = d["name"]

    @classmethod
    def get_tablename(cls):
        return "cpft_lps_resetresponseclock"

    @classmethod
    def get_taskshortname(cls):
        return "CPFT_LPS_ResetResponseClock"

    @classmethod
    def get_tasklongname(cls):
        return "Reset response clock (CPFT Liaison Psychiatry Service)"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + \
            CPFT_LPS_ResetResponseClock.TASK_FIELDSPECS

    def is_complete(self):
        return (
            self.reset_start_time_to
            and self.reason
            and self.field_contents_valid()
        )

    def get_clinical_text(self):
        return [{"content": self.reason}]

    def get_task_html(self):
        h = self.get_standard_clinician_block() + """
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
            WSTRING("cpft_lps_rc_to"),
            format_datetime_string(self.reset_start_time_to,
                                   DATEFORMAT.LONG_DATETIME_WITH_DAY,
                                   default=None))
        h += tr_qa(WSTRING("cpft_lps_rc_reason"), self.reason)
        h += """
            </table>
        """
        return h


# =============================================================================
# CPFT_LPS_Discharge
# =============================================================================

class CPFT_LPS_Discharge(Task):
    TASK_FIELDSPECS = (CLINICIAN_FIELDSPECS + [
        dict(name="discharge_date", cctype="ISO8601"),
        dict(name="discharge_reason_code", cctype="TEXT"),

        dict(name="leaflet_or_discharge_card_given", cctype="BOOL",
             pv=PV.BIT),
        dict(name="frequent_attender", cctype="BOOL", pv=PV.BIT),
        dict(name="patient_wanted_copy_of_letter", cctype="TEXT"),
        dict(name="gaf_at_first_assessment", cctype="INT",
             min=0, max=100),
        dict(name="gaf_at_discharge", cctype="INT",
             min=0, max=100),

        dict(name="referral_reason_self_harm_overdose", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_self_harm_other", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_suicidal_ideas", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_behavioural_disturbance",
             cctype="BOOL", pv=PV.BIT),
        dict(name="referral_reason_low_mood", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_elevated_mood", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_psychosis", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_pre_transplant", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_post_transplant", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_delirium", cctype="BOOL", pv=PV.BIT),
        dict(name="referral_reason_anxiety", cctype="BOOL", pv=PV.BIT),
        dict(name="referral_reason_somatoform_mus", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_motivation_adherence",
             cctype="BOOL", pv=PV.BIT),
        dict(name="referral_reason_capacity", cctype="BOOL", pv=PV.BIT),
        dict(name="referral_reason_eating_disorder", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_safeguarding", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_discharge_placement", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_cognitive_problem", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_substance_alcohol", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_substance_other", cctype="BOOL",
             pv=PV.BIT),
        dict(name="referral_reason_other", cctype="BOOL", pv=PV.BIT),
        dict(name="referral_reason_transplant_organ", cctype="TEXT"),
        dict(name="referral_reason_other_detail", cctype="TEXT"),

        dict(name="diagnosis_no_active_mental_health_problem",
             cctype="BOOL", pv=PV.BIT),
        dict(name="diagnosis_psych_1_icd10code", cctype="TEXT"),
        dict(name="diagnosis_psych_1_description", cctype="TEXT"),
        dict(name="diagnosis_psych_2_icd10code", cctype="TEXT"),
        dict(name="diagnosis_psych_2_description", cctype="TEXT"),
        dict(name="diagnosis_psych_3_icd10code", cctype="TEXT"),
        dict(name="diagnosis_psych_3_description", cctype="TEXT"),
        dict(name="diagnosis_psych_4_icd10code", cctype="TEXT"),
        dict(name="diagnosis_psych_4_description", cctype="TEXT"),
        dict(name="diagnosis_medical_1", cctype="TEXT"),
        dict(name="diagnosis_medical_2", cctype="TEXT"),
        dict(name="diagnosis_medical_3", cctype="TEXT"),
        dict(name="diagnosis_medical_4", cctype="TEXT"),

        dict(name="management_assessment_diagnostic", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_medication", cctype="BOOL", pv=PV.BIT),
        dict(name="management_specialling_behavioural_disturbance",
             cctype="BOOL", pv=PV.BIT),
        dict(name="management_supportive_patient", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_supportive_carers", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_supportive_staff", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_nursing_management", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_therapy_cbt", cctype="BOOL", pv=PV.BIT),
        dict(name="management_therapy_cat", cctype="BOOL", pv=PV.BIT),
        dict(name="management_therapy_other", cctype="BOOL", pv=PV.BIT),
        dict(name="management_treatment_adherence", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_capacity", cctype="BOOL", pv=PV.BIT),
        dict(name="management_education_patient", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_education_carers", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_education_staff", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_accommodation_placement", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_signposting_external_referral",
             cctype="BOOL", pv=PV.BIT),
        dict(name="management_mha_s136", cctype="BOOL", pv=PV.BIT),
        dict(name="management_mha_s5_2", cctype="BOOL", pv=PV.BIT),
        dict(name="management_mha_s2", cctype="BOOL", pv=PV.BIT),
        dict(name="management_mha_s3", cctype="BOOL", pv=PV.BIT),
        dict(name="management_complex_case_conference", cctype="BOOL",
             pv=PV.BIT),
        dict(name="management_other", cctype="BOOL", pv=PV.BIT),
        dict(name="management_other_detail", cctype="TEXT"),

        dict(name="outcome", cctype="TEXT"),
        dict(name="outcome_hospital_transfer_detail", cctype="TEXT"),
        dict(name="outcome_other_detail", cctype="TEXT"),
    ])
    for d in TASK_FIELDSPECS:
        if "comment" not in d:
            d["comment"] = d["name"]

    @classmethod
    def get_tablename(cls):
        return "cpft_lps_discharge"

    @classmethod
    def get_taskshortname(cls):
        return "CPFT_LPS_Discharge"

    @classmethod
    def get_tasklongname(cls):
        return "Discharge from CPFT Liaison Psychiatry Service"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CPFT_LPS_Discharge.TASK_FIELDSPECS

    def is_complete(self):
        return (
            self.discharge_date
            and self.discharge_reason_code
            and self.outcome
            and self.field_contents_valid()
        )

    def get_discharge_reason(self):
        if self.discharge_reason_code == "F":
            return WSTRING("cpft_lps_discharge_reason_code_F")
        elif self.discharge_reason_code == "A":
            return WSTRING("cpft_lps_discharge_reason_code_A")
        elif self.discharge_reason_code == "O":
            return WSTRING("cpft_lps_discharge_reason_code_O")
        elif self.discharge_reason_code == "C":
            return WSTRING("cpft_lps_discharge_reason_code_C")
        else:
            return None

    def get_referral_reasons(self):
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
                referral_reasons.append(WSTRING("cpft_lps_dis_" + r))
        return referral_reasons

    def get_managements(self):
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
                managements.append(WSTRING("cpft_lps_dis_" + r))
        return managements

    def get_psychiatric_diagnoses(self):
        psychiatric_diagnoses = [
            WSTRING("cpft_lps_dis_diagnosis_no_active_mental_health_problem")
        ] if self.diagnosis_no_active_mental_health_problem else []
        for i in range(1, 4 + 1):  # magic number
            if getattr(self, "diagnosis_psych_" + str(i) + "_icd10code"):
                psychiatric_diagnoses.append(
                    ws.webify(getattr(self, "diagnosis_psych_" +
                                      str(i) + "_icd10code"))
                    + " – "
                    + ws.webify(getattr(self, "diagnosis_psych_" +
                                        str(i) + "_description"))
                )
        return psychiatric_diagnoses

    def get_medical_diagnoses(self):
        medical_diagnoses = []
        for i in range(1, 4 + 1):  # magic number
            if getattr(self, "diagnosis_medical_" + str(i)):
                medical_diagnoses.append(
                    ws.webify(getattr(self, "diagnosis_medical_" + str(i))))
        return medical_diagnoses

    def get_clinical_text(self):
        diagnoses = self.get_psychiatric_diagnoses() + \
            self.get_medical_diagnoses()
        return [
            {
                "heading": ws.webify(WSTRING("cpft_lps_dis_discharge_reason")),
                "content": self.get_discharge_reason()
            },
            {
                "heading": ws.webify(
                    WSTRING("cpft_lps_dis_referral_reason_t")),
                "content": ", ".join(self.get_referral_reasons())
            },
            {
                "heading": ws.webify(WSTRING("cpft_lps_dis_diagnoses_t")),
                "content": ", ".join(diagnoses)
            },
            {
                "heading": ws.webify(WSTRING("cpft_lps_dis_management_t")),
                "content": ", ".join(self.get_managements())
            },
            {
                "heading": ws.webify(WSTRING("cpft_lps_dis_outcome_t")),
                "content": self.outcome
            },
        ]

    def get_task_html(self):
        h = self.get_standard_clinician_block() + """
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
        h += tr_qa(WSTRING("cpft_lps_dis_discharge_date"),
                   format_datetime_string(self.discharge_date,
                                          DATEFORMAT.LONG_DATE_WITH_DAY,
                                          default=None), "")
        h += tr_qa(WSTRING("cpft_lps_dis_discharge_reason"),
                   self.get_discharge_reason(), "")
        h += tr_qa(
            WSTRING("cpft_lps_dis_leaflet_or_discharge_card_given"),
            get_yes_no_none(self.leaflet_or_discharge_card_given), "")
        h += tr_qa(WSTRING("cpft_lps_dis_frequent_attender"),
                   get_yes_no_none(self.frequent_attender), "")
        h += tr_qa(
            WSTRING("cpft_lps_dis_patient_wanted_copy_of_letter"),
            self.patient_wanted_copy_of_letter, "")
        h += tr_qa(WSTRING("cpft_lps_dis_gaf_at_first_assessment"),
                   self.gaf_at_first_assessment, "")
        h += tr_qa(WSTRING("cpft_lps_dis_gaf_at_discharge"),
                   self.gaf_at_discharge, "")

        h += subheading_spanning_two_columns(
            WSTRING("cpft_lps_dis_referral_reason_t"))
        h += tr_span_col(answer(", ".join(self.get_referral_reasons())),
                         cols=2)
        h += tr_qa(
            WSTRING("cpft_lps_dis_referral_reason_transplant_organ"),
            self.referral_reason_transplant_organ, "")
        h += tr_qa(
            WSTRING("cpft_lps_dis_referral_reason_other_detail"),
            self.referral_reason_other_detail, "")

        h += subheading_spanning_two_columns(
            WSTRING("cpft_lps_dis_diagnoses_t"))
        h += tr_qa(WSTRING("cpft_lps_dis_psychiatric_t"),
                   "<br>".join(self.get_psychiatric_diagnoses()), "")
        h += tr_qa(WSTRING("cpft_lps_dis_medical_t"),
                   "<br>".join(self.get_medical_diagnoses()), "")

        h += subheading_spanning_two_columns(
            WSTRING("cpft_lps_dis_management_t"))
        h += tr_span_col(answer(", ".join(self.get_managements())), cols=2)
        h += tr_qa(WSTRING("cpft_lps_dis_management_other_detail"),
                   self.management_other_detail, "")

        h += subheading_spanning_two_columns(WSTRING("cpft_lps_dis_outcome_t"))
        h += tr_qa(WSTRING("cpft_lps_dis_outcome_t"),
                   self.outcome, "")
        h += tr_qa(
            WSTRING("cpft_lps_dis_outcome_hospital_transfer_detail"),
            self.outcome_hospital_transfer_detail, "")
        h += tr_qa(WSTRING("cpft_lps_dis_outcome_other_detail"),
                   self.outcome_other_detail, "")

        h += """
            </table>
        """
        return h

# =============================================================================
# Reports
# =============================================================================

ID_NUMBER_TO_LINK_ON_LABEL = "ID number to link on?"


class LPS_Report_Referred_Not_Discharged(Report):

    @classmethod
    def get_report_id(cls):
        return "cpft_lps_referred_not_subsequently_discharged"

    @classmethod
    def get_report_title(cls):
        return "CPFT LPS – referred but not yet discharged"

    @classmethod
    def get_param_spec_list(cls):
        return [
            {
                "type": PARAM.WHICH_IDNUM,
                "name": "linking_idnum",
                "label": ID_NUMBER_TO_LINK_ON_LABEL,
            },
        ]

    def get_rows_descriptions(self, linking_idnum=None):
        if not linking_idnum:
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
                AND r._device = p1._device
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
                        AND d._device = p2._device
                        AND d._era = p2._era
                )
            ORDER BY
                r.lps_division,
                r.referral_date_time,
                r.referral_priority
        """.format(linking_idnum)
        return pls.db.fetchall_with_fieldnames(sql)


class LPS_Report_Referred_Not_Clerked_Or_Discharged(Report):

    @classmethod
    def get_report_id(cls):
        return "cpft_lps_referred_not_subsequently_clerked_or_discharged"

    @classmethod
    def get_report_title(cls):
        return "CPFT LPS – referred but not yet fully assessed or discharged"

    @classmethod
    def get_param_spec_list(cls):
        return [
            {
                "type": PARAM.WHICH_IDNUM,
                "name": "linking_idnum",
                "label": ID_NUMBER_TO_LINK_ON_LABEL,
            },
        ]

    def get_rows_descriptions(self, linking_idnum=None):
        if not linking_idnum:
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
                AND r._device = p1._device
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
                        AND d._device = p2._device
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
                        AND c._device = p2._device
                        AND c._era = p2._era
                )
            ORDER BY
                r.lps_division,
                r.referral_date_time,
                r.referral_priority
        """.format(linking_idnum)
        return pls.db.fetchall_with_fieldnames(sql)
