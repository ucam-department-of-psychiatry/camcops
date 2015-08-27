// CPFT_LPS_Referral.js

/*
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
*/

/*jslint node: true, newcap: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // TABLE
    tablename = "cpft_lps_referral",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push(
    {name: 'referral_date_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'lps_division', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'referral_priority', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'referral_method', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'referrer_name', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'referrer_contact_details', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'referring_consultant', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'referring_specialty', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'referring_specialty_other', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'patient_location', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'admission_date', type: DBCONSTANTS.TYPE_DATE},
    {name: 'estimated_discharge_date', type: DBCONSTANTS.TYPE_DATE},
    {name: 'patient_aware_of_referral', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'interpreter_required', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'sensory_impairment', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'marital_status_code', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'ethnic_category_code', type: DBCONSTANTS.TYPE_INTEGER},

    {name: 'admission_reason_overdose', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'admission_reason_self_harm_not_overdose', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'admission_reason_confusion', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'admission_reason_trauma', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'admission_reason_falls', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'admission_reason_infection', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'admission_reason_poor_adherence', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'admission_reason_other', type: DBCONSTANTS.TYPE_BOOLEAN},

    {name: 'existing_psychiatric_teams', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'care_coordinator', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'other_contact_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'referral_reason', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function CPFT_LPS_Referral(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(CPFT_LPS_Referral, taskcommon.BaseTask);
lang.extendPrototype(CPFT_LPS_Referral, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: CPFT_LPS_Referral,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (
            // The bare minimum:
            this.referral_date_time &&
            this.patient_location &&
            this.referral_reason
        );
    },

    getSummary: function () {
        return (L('location') + ": " + this.patient_location + ". " +
                this.referral_reason);
    },

    getDetail: function () {
        return this.getSummary() + "\n\n" + L('see_facsimile_for_more_detail');
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            NHS_DD = require('common/NHS_DD'),
            i,
            s,
            referral_pickup_text = [
                "Direct",
                "Morning Report",
                "Ops centre",
                "Other"
            ],
            referral_pickup_options = [],
            specialty_text = [
                "ED",
                "Acute medicine",
                "DME",
                "Trauma",
                "Transplant",
                "Surgery",
                "Hepatology",
                "Gastroenterology",
                "Renal",
                "Oncology",
                "Cardiology",
                "Neurology",
                "Endocrinology",
                "Perinatal/obstetric",
                "Respiratory"
            ],
            specialty_options = [],
            priority_options = [
                new KeyValuePair(L('cpft_lps_referral_priority_R'), 'R'),
                new KeyValuePair(L('cpft_lps_referral_priority_U'), 'U'),
                new KeyValuePair(L('cpft_lps_referral_priority_E'), 'E')
            ],
            lps_division_options = [
                new KeyValuePair(L('cpft_lps_service_G'), 'G'),
                new KeyValuePair(L('cpft_lps_service_O'), 'O'),
                new KeyValuePair(L('cpft_lps_service_S'), 'S')
            ],
            yesNoOptions = taskcommon.OPTIONS_NO_YES_BOOLEAN,
            onlypage,
            questionnaire;

        for (i = 0; i < referral_pickup_text.length; ++i) {
            s = referral_pickup_text[i];
            referral_pickup_options.push(new KeyValuePair(s, s));
        }
        specialty_text.sort();
        specialty_text.push("Other"); // goes at the end
        for (i = 0; i < specialty_text.length; ++i) {
            s = specialty_text[i];
            specialty_options.push(new KeyValuePair(s, s));
        }

        onlypage = {
            title: L('t_cpft_lps_referral'),
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_referral_t_about_referral")
                },

                {
                    type: "QuestionText",
                    text: L("cpft_lps_referral_f_referral_date_time")
                },
                {
                    type: "QuestionDateTime",
                    field: "referral_date_time",
                    showTime: true,
                    mandatory: true
                },
                {
                    type: "QuestionText",
                    text: L("cpft_lps_referral_f_lps_division")
                },
                {
                    type: "QuestionMCQ",
                    options: lps_division_options,
                    field: "lps_division",
                    showInstruction: false,
                    horizontal: true,
                    mandatory: true
                },
                {
                    type: "QuestionText",
                    text: L("cpft_lps_referral_f_referral_priority")
                },
                {
                    type: "QuestionMCQ",
                    options: priority_options,
                    field: "referral_priority",
                    showInstruction: false,
                    horizontal: true,
                    mandatory: true
                },
                {
                    type: "QuestionText",
                    text: L("cpft_lps_referral_f_referral_method")
                },
                {
                    type: "QuestionMCQ",
                    options: referral_pickup_options,
                    field: "referral_method",
                    showInstruction: false,
                    horizontal: true,
                    mandatory: true
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: true,
                    useColumns: true,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "referrer_name",
                            prompt: L("cpft_lps_referral_f_referrer_name")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "referrer_contact_details",
                            prompt: L("cpft_lps_referral_f_referrer_contact_details")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "referring_consultant",
                            prompt: L("cpft_lps_referral_f_referring_consultant")
                        }
                    ]
                },
                {
                    type: "QuestionText",
                    text: L("cpft_lps_referral_f_referring_specialty")
                },
                {
                    type: "QuestionPickerPopup",
                    options: specialty_options,
                    field: "referring_specialty",
                    mandatory: true
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "referring_specialty_other",
                            prompt: L("cpft_lps_referral_f_referring_specialty_other")
                        }
                    ]
                },
                { type: "QuestionHorizontalRule" },

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_referral_t_patient")
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: true,
                    useColumns: true,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "patient_location",
                            prompt: L("cpft_lps_referral_f_patient_location")
                        }
                    ]
                },
                {
                    type: "ContainerTable",
                    columns: 2,
                    columnWidths: ["30%", "70%"],
                    elements: [
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_referral_f_admission_date")
                        },
                        {
                            type: "QuestionDateTime",
                            field: "admission_date",
                            showTime: false,
                            mandatory: false,
                            offerNullButton: true
                        },
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_referral_f_estimated_discharge_date")
                        },
                        {
                            type: "QuestionDateTime",
                            field: "estimated_discharge_date",
                            showTime: false,
                            mandatory: false,
                            offerNullButton: true
                        },
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_referral_f_patient_aware_of_referral")
                        },
                        {
                            type: "QuestionMCQ",
                            options: yesNoOptions,
                            field: "patient_aware_of_referral",
                            showInstruction: false,
                            horizontal: true,
                            mandatory: false
                        },
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_referral_f_interpreter_required")
                        },
                        {
                            type: "QuestionMCQ",
                            options: yesNoOptions,
                            field: "interpreter_required",
                            showInstruction: false,
                            horizontal: true,
                            mandatory: false
                        },
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_referral_f_sensory_impairment")
                        },
                        {
                            type: "QuestionMCQ",
                            options: yesNoOptions,
                            field: "sensory_impairment",
                            showInstruction: false,
                            horizontal: true,
                            mandatory: false
                        },
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_referral_f_marital_status")
                        },
                        {
                            type: "QuestionPickerPopup",
                            options: NHS_DD.PERSON_MARITAL_STATUS_CODE_OPTIONS,
                            field: "marital_status_code",
                            mandatory: false
                        },
                        {
                            type: "QuestionText",
                            text: L("cpft_lps_referral_f_ethnic_category")
                        },
                        {
                            type: "QuestionPickerPopup",
                            options: NHS_DD.ETHNIC_CATEGORY_CODE_OPTIONS,
                            field: "ethnic_category_code",
                            mandatory: false
                        }
                    ]
                },
                { type: "QuestionHorizontalRule" },

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_referral_t_admission_reason")
                },
                {
                    type: "ContainerHorizontal",
                    elements: [
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_referral_f_admission_reason_overdose"),
                            field: "admission_reason_overdose",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_referral_f_admission_reason_self_harm_not_overdose"),
                            field: "admission_reason_self_harm_not_overdose",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_referral_f_admission_reason_confusion"),
                            field: "admission_reason_confusion",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_referral_f_admission_reason_trauma"),
                            field: "admission_reason_trauma",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_referral_f_admission_reason_falls"),
                            field: "admission_reason_falls",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_referral_f_admission_reason_infection"),
                            field: "admission_reason_infection",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_referral_f_admission_reason_poor_adherence"),
                            field: "admission_reason_poor_adherence",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        },
                        {
                            type: "QuestionBooleanText",
                            text: L("cpft_lps_referral_f_admission_reason_other"),
                            field: "admission_reason_other",
                            mandatory: false,
                            bold: false,
                            indicatorOnLeft: true
                        }
                    ]
                },
                { type: "QuestionHorizontalRule" },

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_referral_t_other_people")
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "existing_psychiatric_teams",
                            prompt: L("cpft_lps_referral_f_existing_psychiatric_teams")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "care_coordinator",
                            prompt: L("cpft_lps_referral_f_care_coordinator")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "other_contact_details",
                            prompt: L("cpft_lps_referral_f_other_contact_details")
                        }
                    ]
                },
                { type: "QuestionHorizontalRule" },

                {
                    type: "QuestionText",
                    bold: true,
                    text: L("cpft_lps_referral_t_referral_reason")
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: true,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "referral_reason",
                            prompt: L("cpft_lps_referral_f_referral_reason")
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

module.exports = CPFT_LPS_Referral;
