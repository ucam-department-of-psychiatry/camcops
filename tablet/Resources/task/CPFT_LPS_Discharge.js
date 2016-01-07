// CPFT_LPS_Discharge.js

/*
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
*/

/*jslint node: true, newcap: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // TABLE
    tablename = "cpft_lps_discharge",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'discharge_date', type: DBCONSTANTS.TYPE_DATE},
    {name: 'discharge_reason_code', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'leaflet_or_discharge_card_given', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'frequent_attender', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'patient_wanted_copy_of_letter', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'gaf_at_first_assessment', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'gaf_at_discharge', type: DBCONSTANTS.TYPE_INTEGER},

    {name: 'referral_reason_self_harm_overdose', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_self_harm_other', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_suicidal_ideas', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_behavioural_disturbance', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_low_mood', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_elevated_mood', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_psychosis', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_pre_transplant', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_post_transplant', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_delirium', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_anxiety', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_somatoform_mus', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_motivation_adherence', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_capacity', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_eating_disorder', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_safeguarding', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_discharge_placement', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_cognitive_problem', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_substance_alcohol', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_substance_other', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_other', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'referral_reason_transplant_organ', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'referral_reason_other_detail', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'diagnosis_no_active_mental_health_problem', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "diagnosis_psych_1_icd10code", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_psych_1_description", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_psych_2_icd10code", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_psych_2_description", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_psych_3_icd10code", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_psych_3_description", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_psych_4_icd10code", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_psych_4_description", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_medical_1", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_medical_2", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_medical_3", type: DBCONSTANTS.TYPE_TEXT},
    {name: "diagnosis_medical_4", type: DBCONSTANTS.TYPE_TEXT},

    {name: 'management_assessment_diagnostic', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_medication', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_specialling_behavioural_disturbance', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_supportive_patient', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_supportive_carers', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_supportive_staff', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_nursing_management', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_therapy_cbt', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_therapy_cat', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_therapy_other', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_treatment_adherence', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_capacity', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_education_patient', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_education_carers', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_education_staff', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_accommodation_placement', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_signposting_external_referral', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_mha_s136', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_mha_s5_2', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_mha_s2', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_mha_s3', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_complex_case_conference', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_other', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'management_other_detail', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'outcome', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'outcome_hospital_transfer_detail', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'outcome_other_detail', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function CPFT_LPS_Discharge(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(CPFT_LPS_Discharge, taskcommon.BaseTask);
lang.extendPrototype(CPFT_LPS_Discharge, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: CPFT_LPS_Discharge,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (
            // The bare minimum:
            this.discharge_date && this.discharge_reason_code
        );
    },

    getSummary: function () {
        var UICONSTANTS = require('common/UICONSTANTS'),
            time = (this.discharge_date ?
                    this.discharge_date.format(UICONSTANTS.TASK_DATETIME_FORMAT) :
                    ""
            );
        return (
            L('cpft_lps_dis_discharge_date') + ": " +
            time + ". " +
            L('cpft_lps_dis_discharge_reason') + ": " +
            this.discharge_reason_code
        );
    },

    getDetail: function () {
        return this.getSummary() + "\n\n" + L('see_facsimile_for_more_detail');
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            i,
            s,
            discharge_reason_code_options = [
                new KeyValuePair(L('cpft_lps_discharge_reason_code_F'), 'F'),
                new KeyValuePair(L('cpft_lps_discharge_reason_code_A'), 'A'),
                new KeyValuePair(L('cpft_lps_discharge_reason_code_O'), 'O'),
                new KeyValuePair(L('cpft_lps_discharge_reason_code_C'), 'C')
            ],
            wanted_letter_text = [
                "None done",
                "Yes",
                "No",
                "Not appropriate"
            ],
            wanted_letter_options = [],
            outcome_text = [
                "Outcome achieved/no follow-up",
                "CMHT (new)",
                "CMHT (ongoing)",
                "CRHTT (new)",
                "CRHTT (ongoing)",
                "GP follow-up",
                "Liaison outpatient follow-up",
                "Transferred to general hospital",
                "Transferred to psychiatric hospital",
                "Nursing home",
                "Day hospital",
                "Treatment declined",
                "Patient died",
                "Other"
            ],
            outcome_options = [],
            yesNoOptions = taskcommon.OPTIONS_NO_YES_BOOLEAN,
            onlypage,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        for (i = 0; i < wanted_letter_text.length; ++i) {
            s = wanted_letter_text[i];
            wanted_letter_options.push(new KeyValuePair(s, s));
        }
        for (i = 0; i < outcome_text.length; ++i) {
            s = outcome_text[i];
            outcome_options.push(new KeyValuePair(s, s));
        }

        onlypage = {
            title: L('t_cpft_lps_discharge'),
            clinician: true,
            elements: [
                self.getClinicianQuestionnaireBlock(), // Clinician info 3/3

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_dis_discharge_date")
                },
                {
                    type: "QuestionDateTime",
                    field: "discharge_date",
                    showTime: false,
                    mandatory: true
                },
                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_dis_discharge_reason")
                },
                {
                    type: "QuestionMCQ",
                    options: discharge_reason_code_options,
                    field: "discharge_reason_code",
                    showInstruction: false,
                    horizontal: true,
                    mandatory: true
                },

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_dis_leaflet_or_discharge_card_given")
                },
                {
                    type: "QuestionMCQ",
                    options: yesNoOptions,
                    field: "leaflet_or_discharge_card_given",
                    showInstruction: false,
                    horizontal: true,
                    mandatory: false
                },
                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_dis_frequent_attender")
                },
                {
                    type: "QuestionMCQ",
                    options: yesNoOptions,
                    field: "frequent_attender",
                    showInstruction: false,
                    horizontal: true,
                    mandatory: false
                },
                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_dis_patient_wanted_copy_of_letter")
                },
                {
                    type: "QuestionMCQ",
                    options: wanted_letter_options,
                    field: "patient_wanted_copy_of_letter",
                    showInstruction: false,
                    horizontal: true,
                    mandatory: false
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    colWidthPrompt: "40%",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            min: 1,
                            max: 100,
                            field: "gaf_at_first_assessment",
                            prompt: L("cpft_lps_dis_gaf_at_first_assessment")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            min: 1,
                            max: 100,
                            field: "gaf_at_discharge",
                            prompt: L("cpft_lps_dis_gaf_at_discharge")
                        }
                    ]
                },

                { type: "QuestionHorizontalRule" },

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_dis_referral_reason_t")
                },
                {
                    type: "ContainerTable",
                    columns: 4,
                    populateVertically: true,
                    elements: [
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_self_harm_overdose"),
                            field: "referral_reason_self_harm_overdose",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_self_harm_other"),
                            field: "referral_reason_self_harm_other",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_suicidal_ideas"),
                            field: "referral_reason_suicidal_ideas",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_behavioural_disturbance"),
                            field: "referral_reason_behavioural_disturbance",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_low_mood"),
                            field: "referral_reason_low_mood",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_elevated_mood"),
                            field: "referral_reason_elevated_mood",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_psychosis"),
                            field: "referral_reason_psychosis",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_pre_transplant"),
                            field: "referral_reason_pre_transplant",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_post_transplant"),
                            field: "referral_reason_post_transplant",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_delirium"),
                            field: "referral_reason_delirium",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_anxiety"),
                            field: "referral_reason_anxiety",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_somatoform_mus"),
                            field: "referral_reason_somatoform_mus",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_motivation_adherence"),
                            field: "referral_reason_motivation_adherence",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_capacity"),
                            field: "referral_reason_capacity",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_eating_disorder"),
                            field: "referral_reason_eating_disorder",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_safeguarding"),
                            field: "referral_reason_safeguarding",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_discharge_placement"),
                            field: "referral_reason_discharge_placement",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_cognitive_problem"),
                            field: "referral_reason_cognitive_problem",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_substance_alcohol"),
                            field: "referral_reason_substance_alcohol",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_substance_other"),
                            field: "referral_reason_substance_other",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_referral_reason_other"),
                            field: "referral_reason_other",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        }
                    ]
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    colWidthPrompt: "40%",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "referral_reason_transplant_organ",
                            prompt: L("cpft_lps_dis_referral_reason_transplant_organ")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "referral_reason_other_detail",
                            prompt: L("cpft_lps_dis_referral_reason_other_detail")
                        }
                    ]
                },

                { type: "QuestionHorizontalRule" },

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_dis_diagnoses_t")
                },
                {
                    type: "QuestionBooleanText",
                    text: L("cpft_lps_dis_diagnosis_no_active_mental_health_problem"),
                    field: "diagnosis_no_active_mental_health_problem",
                    mandatory: false,
                    bold: false,
                    indicatorOnLeft: true
                },
                {
                    type: "ContainerTable",
                    columns: 2,
                    columnWidths: ["40%", "60%"],
                    elements: [
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_dis_diagnosis_psych") + " 1"
                        },
                        {
                            type: "QuestionDiagnosticCode",
                            code_field: "diagnosis_psych_1_icd10code",
                            description_field: "diagnosis_psych_1_description",
                            codelist_filename: "common/CODES_ICD10",
                            offerNullButton: true
                        },
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_dis_diagnosis_psych") + " 2"
                        },
                        {
                            type: "QuestionDiagnosticCode",
                            code_field: "diagnosis_psych_2_icd10code",
                            description_field: "diagnosis_psych_2_description",
                            codelist_filename: "common/CODES_ICD10",
                            offerNullButton: true
                        },
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_dis_diagnosis_psych") + " 3"
                        },
                        {
                            type: "QuestionDiagnosticCode",
                            code_field: "diagnosis_psych_3_icd10code",
                            description_field: "diagnosis_psych_3_description",
                            codelist_filename: "common/CODES_ICD10",
                            offerNullButton: true
                        },
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_dis_diagnosis_psych") + " 4"
                        },
                        {
                            type: "QuestionDiagnosticCode",
                            code_field: "diagnosis_psych_4_icd10code",
                            description_field: "diagnosis_psych_4_description",
                            codelist_filename: "common/CODES_ICD10",
                            offerNullButton: true
                        }
                    ]
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    colWidthPrompt: "40%",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "diagnosis_medical_1",
                            prompt: L("cpft_lps_dis_diagnosis_medical") + " 1"
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "diagnosis_medical_2",
                            prompt: L("cpft_lps_dis_diagnosis_medical") + " 2"
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "diagnosis_medical_3",
                            prompt: L("cpft_lps_dis_diagnosis_medical") + " 3"
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "diagnosis_medical_4",
                            prompt: L("cpft_lps_dis_diagnosis_medical") + " 4"
                        }
                    ]
                },

                { type: "QuestionHorizontalRule" },

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_dis_management_t")
                },
                {
                    type: "ContainerTable",
                    columns: 4,
                    populateVertically: true,
                    elements: [
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_assessment_diagnostic"),
                            field: "management_assessment_diagnostic",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_medication"),
                            field: "management_medication",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_specialling_behavioural_disturbance"),
                            field: "management_specialling_behavioural_disturbance",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_supportive_patient"),
                            field: "management_supportive_patient",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_supportive_carers"),
                            field: "management_supportive_carers",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_supportive_staff"),
                            field: "management_supportive_staff",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_nursing_management"),
                            field: "management_nursing_management",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_therapy_cbt"),
                            field: "management_therapy_cbt",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_therapy_cat"),
                            field: "management_therapy_cat",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_therapy_other"),
                            field: "management_therapy_other",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_treatment_adherence"),
                            field: "management_treatment_adherence",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_capacity"),
                            field: "management_capacity",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_education_patient"),
                            field: "management_education_patient",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_education_carers"),
                            field: "management_education_carers",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_education_staff"),
                            field: "management_education_staff",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_accommodation_placement"),
                            field: "management_accommodation_placement",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_signposting_external_referral"),
                            field: "management_signposting_external_referral",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_mha_s136"),
                            field: "management_mha_s136",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_mha_s5_2"),
                            field: "management_mha_s5_2",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_mha_s2"),
                            field: "management_mha_s2",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_mha_s3"),
                            field: "management_mha_s3",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_complex_case_conference"),
                            field: "management_complex_case_conference",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_dis_management_other"),
                            field: "management_other",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        }
                    ]
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    colWidthPrompt: "40%",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "management_other_detail",
                            prompt: L("cpft_lps_dis_management_other_detail")
                        }
                    ]
                },

                { type: "QuestionHorizontalRule" },

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_dis_outcome_t")
                },
                {
                    type: "QuestionMCQ",
                    options: outcome_options,
                    field: "outcome",
                    showInstruction: false,
                    horizontal: true,
                    mandatory: true
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    colWidthPrompt: "40%",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "outcome_hospital_transfer_detail",
                            prompt: L("cpft_lps_dis_outcome_hospital_transfer_detail")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "outcome_other_detail",
                            prompt: L("cpft_lps_dis_outcome_other_detail")
                        }
                    ]
                }

            ]
        };

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: [ onlypage ],
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn
        });
        questionnaire.open();
    }

});

module.exports = CPFT_LPS_Discharge;
