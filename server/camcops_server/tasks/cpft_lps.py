#!/usr/bin/env python
# cpft_lps.py

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

from ..cc_modules.cc_dt import format_datetime_string
from ..cc_modules.cc_constants import (
    DATEFORMAT,
    INVALID_VALUE,
    PARAM,
    PV,
)
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
from ..cc_modules.cc_pls import pls
from ..cc_modules.cc_report import Report, ReportParamSpec, REPORT_RESULT_TYPE
from ..cc_modules.cc_task import CtvInfo, Task


# =============================================================================
# CPFT_LPS_Referral
# =============================================================================

class CPFTLPSReferral(Task):
    tablename = "cpft_lps_referral"
    shortname = "CPFT_LPS_Referral"
    longname = "Referral to CPFT Liaison Psychiatry Service"
    fieldspecs = [
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
        dict(name="marital_status_code", cctype="CHAR",
             pv=PV_NHS_MARITAL_STATUS),
        dict(name="ethnic_category_code", cctype="CHAR",
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
    for d in fieldspecs:
        d["comment"] = d["name"]

    def is_complete(self) -> bool:
        return (
            self.patient_location and
            self.referral_reason and
            self.field_contents_valid()
        )

    def get_clinical_text(self) -> List[CtvInfo]:
        return [CtvInfo(
            heading=ws.webify(self.WXSTRING("f_referral_reason_t")),
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

    def get_task_html(self) -> str:
        person_marital_status = get_nhs_dd_person_marital_status()
        ethnic_category_code = get_nhs_dd_ethnic_category_code()
        if self.lps_division == "G":
            banner_class = "banner_referral_general_adult"
            division_name = self.WXSTRING("service_G")
        elif self.lps_division == "O":
            banner_class = "banner_referral_old_age"
            division_name = self.WXSTRING("service_O")
        elif self.lps_division == "S":
            banner_class = "banner_referral_substance_misuse"
            division_name = self.WXSTRING("service_S")
        else:
            banner_class = ""
            division_name = None

        if self.referral_priority == "R":
            priority_name = self.WXSTRING("priority_R")
        elif self.referral_priority == "U":
            priority_name = self.WXSTRING("priority_U")
        elif self.referral_priority == "E":
            priority_name = self.WXSTRING("priority_E")
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
                admission_reasons.append(self.WXSTRING("f_" + r))

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
            self.WXSTRING("t_about_referral"))
        h += """
            <tr>
                <td>{}</td><td>{}</td>
                <td>{}</td><td class="highlight">{}</td>
            </tr>
        """.format(
            self.WXSTRING("f_referral_method"),
            answer(self.referral_method),
            self.WXSTRING("f_referral_priority"),
            answer(self.referral_priority, default_for_blank_strings=True) +
            ": " + answer(priority_name)
        )
        h += self.four_column_row(
            self.WXSTRING("f_referrer_name"),
            self.referrer_name,
            self.WXSTRING("f_referring_specialty"),
            self.referring_specialty
        )
        h += self.four_column_row(
            self.WXSTRING("f_referrer_contact_details"),
            self.referrer_contact_details,
            self.WXSTRING("f_referring_specialty_other"),
            self.referring_specialty_other
        )
        h += self.four_column_row(
            self.WXSTRING("f_referring_consultant"),
            self.referring_consultant,
            "",
            ""
        )
        h += subheading_spanning_four_columns(
            self.WXSTRING("t_patient"))
        h += """
            <tr>
                <td>{}</td><td>{}</td>
                <td>{}</td><td class="highlight">{}</td>
            </tr>
        """.format(
            self.WXSTRING("f_admission_date"),
            answer(format_datetime_string(self.admission_date,
                                          DATEFORMAT.LONG_DATE,
                                          default=None), ""),
            self.WXSTRING("f_patient_location"),
            answer(self.patient_location)
        )
        h += self.four_column_row(
            self.WXSTRING("f_estimated_discharge_date"),
            format_datetime_string(self.estimated_discharge_date,
                                   DATEFORMAT.LONG_DATE, ""),
            self.WXSTRING("f_patient_aware_of_referral"),
            get_yes_no_none(self.patient_aware_of_referral)
        )
        h += self.four_column_row(
            self.WXSTRING("f_marital_status"),
            person_marital_status.get(self.marital_status_code, INVALID_VALUE),
            self.WXSTRING("f_interpreter_required"),
            get_yes_no_none(self.interpreter_required)
        )
        h += self.four_column_row(
            self.WXSTRING("f_ethnic_category"),
            ethnic_category_code.get(self.ethnic_category_code, INVALID_VALUE),
            self.WXSTRING("f_sensory_impairment"),
            get_yes_no_none(self.sensory_impairment)
        )
        h += subheading_spanning_four_columns(
            self.WXSTRING("t_admission_reason"))
        h += tr_span_col(answer(", ".join(admission_reasons), ""), cols=4)
        h += subheading_spanning_four_columns(
            self.WXSTRING("t_other_people"))
        h += self.tr_qa(
            self.WXSTRING("f_existing_psychiatric_teams"),
            self.existing_psychiatric_teams, "")
        h += self.tr_qa(
            self.WXSTRING("f_care_coordinator"),
            self.care_coordinator, "")
        h += self.tr_qa(
            self.WXSTRING("f_other_contact_details"),
            self.other_contact_details, "")
        h += subheading_spanning_four_columns(
            self.WXSTRING("t_referral_reason"))
        h += tr_span_col(answer(self.referral_reason, ""), cols=4)
        h += """
            </table>
        """
        return h


# =============================================================================
# CPFT_LPS_ResetResponseClock
# =============================================================================

class CPFTLPSResetResponseClock(Task):
    tablename = "cpft_lps_resetresponseclock"
    shortname = "CPFT_LPS_ResetResponseClock"
    longname = "Reset response clock (CPFT Liaison Psychiatry Service)"
    fieldspecs = [
        dict(name="reset_start_time_to", cctype="ISO8601"),
        dict(name="reason", cctype="TEXT"),
    ]
    for d in fieldspecs:
        if "comment" not in d:
            d["comment"] = d["name"]
    has_clinician = True

    def is_complete(self) -> bool:
        return (
            self.reset_start_time_to and
            self.reason and
            self.field_contents_valid()
        )

    def get_clinical_text(self) -> List[CtvInfo]:
        return [CtvInfo(content=self.reason)]

    def get_task_html(self) -> str:
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
            self.WXSTRING("to"),
            format_datetime_string(self.reset_start_time_to,
                                   DATEFORMAT.LONG_DATETIME_WITH_DAY,
                                   default=None))
        h += tr_qa(self.WXSTRING("reason"), self.reason)
        h += """
            </table>
        """
        return h


# =============================================================================
# CPFT_LPS_Discharge
# =============================================================================

class CPFTLPSDischarge(Task):
    tablename = "cpft_lps_discharge"
    shortname = "CPFT_LPS_Discharge"
    longname = "Discharge from CPFT Liaison Psychiatry Service"
    fieldspecs = [
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
    ]
    for d in fieldspecs:
        if "comment" not in d:
            d["comment"] = d["name"]
    has_clinician = True

    def is_complete(self) -> bool:
        return (
            self.discharge_date and
            self.discharge_reason_code and
            # self.outcome and  # v2.0.0
            self.field_contents_valid()
        )

    def get_discharge_reason(self) -> Optional[str]:
        if self.discharge_reason_code == "F":
            return self.WXSTRING("reason_code_F")
        elif self.discharge_reason_code == "A":
            return self.WXSTRING("reason_code_A")
        elif self.discharge_reason_code == "O":
            return self.WXSTRING("reason_code_O")
        elif self.discharge_reason_code == "C":
            return self.WXSTRING("reason_code_C")
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
                referral_reasons.append(self.WXSTRING("" + r))
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
                managements.append(self.WXSTRING("" + r))
        return managements

    def get_psychiatric_diagnoses(self) -> List[str]:
        psychiatric_diagnoses = [
            self.WXSTRING("diagnosis_no_active_mental_health_problem")
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

    def get_clinical_text(self) -> List[CtvInfo]:
        diagnoses = self.get_psychiatric_diagnoses() + \
            self.get_medical_diagnoses()
        return [
            CtvInfo(
                heading=ws.webify(self.WXSTRING("discharge_reason")),
                content=self.get_discharge_reason()
            ),
            CtvInfo(
                heading=ws.webify(
                    self.WXSTRING("referral_reason_t")),
                content=", ".join(self.get_referral_reasons())
            ),
            CtvInfo(
                heading=ws.webify(self.WXSTRING("diagnoses_t")),
                content=", ".join(diagnoses)
            ),
            CtvInfo(
                heading=ws.webify(self.WXSTRING("management_t")),
                content=", ".join(self.get_managements())
            ),
            CtvInfo(
                heading=ws.webify(self.WXSTRING("outcome_t")),
                content=self.outcome
            ),
        ]

    def get_task_html(self) -> str:
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
        h += tr_qa(self.WXSTRING("discharge_date"),
                   format_datetime_string(self.discharge_date,
                                          DATEFORMAT.LONG_DATE_WITH_DAY,
                                          default=None), "")
        h += tr_qa(self.WXSTRING("discharge_reason"),
                   self.get_discharge_reason(), "")
        h += tr_qa(self.WXSTRING("leaflet_or_discharge_card_given"),
                   get_yes_no_none(self.leaflet_or_discharge_card_given), "")
        h += tr_qa(self.WXSTRING("frequent_attender"),
                   get_yes_no_none(self.frequent_attender), "")
        h += tr_qa(self.WXSTRING("patient_wanted_copy_of_letter"),
                   self.patient_wanted_copy_of_letter, "")
        h += tr_qa(self.WXSTRING("gaf_at_first_assessment"),
                   self.gaf_at_first_assessment, "")
        h += tr_qa(self.WXSTRING("gaf_at_discharge"),
                   self.gaf_at_discharge, "")

        h += subheading_spanning_two_columns(
            self.WXSTRING("referral_reason_t"))
        h += tr_span_col(answer(", ".join(self.get_referral_reasons())),
                         cols=2)
        h += tr_qa(self.WXSTRING("referral_reason_transplant_organ"),
                   self.referral_reason_transplant_organ, "")
        h += tr_qa(self.WXSTRING("referral_reason_other_detail"),
                   self.referral_reason_other_detail, "")

        h += subheading_spanning_two_columns(
            self.WXSTRING("diagnoses_t"))
        h += tr_qa(self.WXSTRING("psychiatric_t"),
                   "<br>".join(self.get_psychiatric_diagnoses()), "")
        h += tr_qa(self.WXSTRING("medical_t"),
                   "<br>".join(self.get_medical_diagnoses()), "")

        h += subheading_spanning_two_columns(self.WXSTRING("management_t"))
        h += tr_span_col(answer(", ".join(self.get_managements())), cols=2)
        h += tr_qa(self.WXSTRING("management_other_detail"),
                   self.management_other_detail, "")

        h += subheading_spanning_two_columns(self.WXSTRING("outcome_t"))
        h += tr_qa(self.WXSTRING("outcome_t"),
                   self.outcome, "")
        h += tr_qa(self.WXSTRING("outcome_hospital_transfer_detail"),
                   self.outcome_hospital_transfer_detail, "")
        h += tr_qa(self.WXSTRING("outcome_other_detail"),
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

    @staticmethod
    def get_rows_descriptions(linking_idnum: int = None) -> REPORT_RESULT_TYPE:
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
        return pls.db.fetchall_with_fieldnames(sql)


class LPSReportReferredNotClerkedOrDischarged(Report):
    report_id = "cpft_lps_referred_not_subsequently_clerked_or_discharged"
    report_title = ("CPFT LPS – referred but not yet fully assessed or "
                    "discharged")
    param_spec_list = [ReportParamSpec(type=PARAM.WHICH_IDNUM,
                                       name="linking_idnum",
                                       label=ID_NUMBER_TO_LINK_ON_LABEL)]

    @staticmethod
    def get_rows_descriptions(linking_idnum: int = None) -> REPORT_RESULT_TYPE:
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
        return pls.db.fetchall_with_fieldnames(sql)
