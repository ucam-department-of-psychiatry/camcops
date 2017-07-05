// PsychiatricClerking.js

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
/*global L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "psychiatricclerking",
    fieldlist = dbcommon.standardTaskFields(),
    extrafields_a = dbcommon.CLINICIAN_FIELDSPECS, // Clinician info 1/3
    extrafields_b = [
        {name: "location", type: DBCONSTANTS.TYPE_TEXT},
        {name: "contact_type", type: DBCONSTANTS.TYPE_TEXT},
        {name: "reason_for_contact", type: DBCONSTANTS.TYPE_TEXT},
        {name: "presenting_issue", type: DBCONSTANTS.TYPE_TEXT},
        {name: "systems_review", type: DBCONSTANTS.TYPE_TEXT},
        {name: "collateral_history", type: DBCONSTANTS.TYPE_TEXT}
    ],
    extrafields_c = [
        {name: "diagnoses_psychiatric", type: DBCONSTANTS.TYPE_TEXT},
        {name: "diagnoses_medical", type: DBCONSTANTS.TYPE_TEXT},
        {name: "operations_procedures", type: DBCONSTANTS.TYPE_TEXT},
        {name: "allergies_adverse_reactions", type: DBCONSTANTS.TYPE_TEXT},
        {name: "medications", type: DBCONSTANTS.TYPE_TEXT},
        {name: "recreational_drug_use", type: DBCONSTANTS.TYPE_TEXT},
        {name: "family_history", type: DBCONSTANTS.TYPE_TEXT},
        {name: "developmental_history", type: DBCONSTANTS.TYPE_TEXT},
        {name: "personal_history", type: DBCONSTANTS.TYPE_TEXT},
        {name: "premorbid_personality", type: DBCONSTANTS.TYPE_TEXT},
        {name: "forensic_history", type: DBCONSTANTS.TYPE_TEXT},
        {name: "current_social_situation", type: DBCONSTANTS.TYPE_TEXT}
    ],
    extrafields_mse = [
        {name: "mse_appearance_behaviour", type: DBCONSTANTS.TYPE_TEXT},
        {name: "mse_speech", type: DBCONSTANTS.TYPE_TEXT},
        {name: "mse_mood_subjective", type: DBCONSTANTS.TYPE_TEXT},
        {name: "mse_mood_objective", type: DBCONSTANTS.TYPE_TEXT},
        {name: "mse_thought_form", type: DBCONSTANTS.TYPE_TEXT},
        {name: "mse_thought_content", type: DBCONSTANTS.TYPE_TEXT},
        {name: "mse_perception", type: DBCONSTANTS.TYPE_TEXT},
        {name: "mse_cognition", type: DBCONSTANTS.TYPE_TEXT},
        {name: "mse_insight", type: DBCONSTANTS.TYPE_TEXT}
    ],
    extrafields_pe = [
        {name: "physical_examination_general", type: DBCONSTANTS.TYPE_TEXT},
        {name: "physical_examination_cardiovascular", type: DBCONSTANTS.TYPE_TEXT},
        {name: "physical_examination_respiratory", type: DBCONSTANTS.TYPE_TEXT},
        {name: "physical_examination_abdominal", type: DBCONSTANTS.TYPE_TEXT},
        {name: "physical_examination_neurological", type: DBCONSTANTS.TYPE_TEXT}
    ],
    extrafields_d = [
        {name: "assessment_scales", type: DBCONSTANTS.TYPE_TEXT},
        {name: "investigations_results", type: DBCONSTANTS.TYPE_TEXT}
    ],
    extrafields_e = [
        {name: "safety_alerts", type: DBCONSTANTS.TYPE_TEXT},
        {name: "risk_assessment", type: DBCONSTANTS.TYPE_TEXT},
        {name: "relevant_legal_information", type: DBCONSTANTS.TYPE_TEXT}
    ],
    extrafields_f = [
        {name: "current_problems", type: DBCONSTANTS.TYPE_TEXT},
        {name: "patient_carer_concerns", type: DBCONSTANTS.TYPE_TEXT},
        {name: "impression", type: DBCONSTANTS.TYPE_TEXT},
        {name: "management_plan", type: DBCONSTANTS.TYPE_TEXT},
        {name: "information_given", type: DBCONSTANTS.TYPE_TEXT}
    ];

fieldlist.push.apply(fieldlist, extrafields_a);
fieldlist.push.apply(fieldlist, extrafields_b);
fieldlist.push.apply(fieldlist, extrafields_c);
fieldlist.push.apply(fieldlist, extrafields_mse);
fieldlist.push.apply(fieldlist, extrafields_pe);
fieldlist.push.apply(fieldlist, extrafields_d);
fieldlist.push.apply(fieldlist, extrafields_e);
fieldlist.push.apply(fieldlist, extrafields_f);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function PsychiatricClerking(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(PsychiatricClerking, taskcommon.BaseTask);
lang.extendPrototype(PsychiatricClerking, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: PsychiatricClerking,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return true;
    },

    getSummary: function () {
        return L('location') + ": " + this.location;
    },

    getDetail: function () {
        var s = "",
            i;
        for (i = 0; i < extrafields_a.length; ++i) {
            if (i > 0) { s += "\n"; }
            s += (L(extrafields_a[i].name) + ": " +
                  this[extrafields_a[i].name]);
        }
        for (i = 0; i < extrafields_b.length; ++i) {
            s += ("\n" + L(extrafields_b[i].name) + ": " +
                  this[extrafields_b[i].name]);
        }
        for (i = 0; i < extrafields_c.length; ++i) {
            s += ("\n" + L(extrafields_c[i].name) + ": " +
                  this[extrafields_c[i].name]);
        }
        for (i = 0; i < extrafields_mse.length; ++i) {
            s += ("\n" + L(extrafields_mse[i].name) + ": " +
                  this[extrafields_mse[i].name]);
        }
        for (i = 0; i < extrafields_pe.length; ++i) {
            s += ("\n" + L(extrafields_pe[i].name) + ": " +
                  this[extrafields_pe[i].name]);
        }
        for (i = 0; i < extrafields_d.length; ++i) {
            s += ("\n" + L(extrafields_d[i].name) + ": " +
                  this[extrafields_d[i].name]);
        }
        for (i = 0; i < extrafields_e.length; ++i) {
            s += ("\n" + L(extrafields_e[i].name) + ": " +
                  this[extrafields_e[i].name]);
        }
        for (i = 0; i < extrafields_f.length; ++i) {
            s += ("\n" + L(extrafields_f[i].name) + ": " +
                  this[extrafields_f[i].name]);
        }
        return s;
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
        //  variables_a = [],
            variables_b = [],
            variables_mse = [],
            variables_pe = [],
            variables_c = [],
            variables_d = [],
            variables_e = [],
            variables_f = [],
            i,
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3
        /*
        for (i = 0; i < extrafields_a.length; ++i) {
            variables_a.push({
                type: UICONSTANTS.TYPEDVAR_TEXT,
                field: extrafields_a[i].name,
                prompt: L(extrafields_a[i].name),
            });
        }
        */
        for (i = 0; i < extrafields_b.length; ++i) {
            variables_b.push({
                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                field: extrafields_b[i].name,
                prompt: L(extrafields_b[i].name)
            });
        }
        for (i = 0; i < extrafields_mse.length; ++i) {
            variables_mse.push({
                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                field: extrafields_mse[i].name,
                prompt: L(extrafields_mse[i].name)
            });
        }
        for (i = 0; i < extrafields_c.length; ++i) {
            variables_c.push({
                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                field: extrafields_c[i].name,
                prompt: L(extrafields_c[i].name)
            });
        }
        for (i = 0; i < extrafields_pe.length; ++i) {
            variables_pe.push({
                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                field: extrafields_pe[i].name,
                prompt: L(extrafields_pe[i].name)
            });
        }
        for (i = 0; i < extrafields_d.length; ++i) {
            variables_d.push({
                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                field: extrafields_d[i].name,
                prompt: L(extrafields_d[i].name)
            });
        }
        for (i = 0; i < extrafields_e.length; ++i) {
            variables_e.push({
                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                field: extrafields_e[i].name,
                prompt: L(extrafields_e[i].name)
            });
        }
        for (i = 0; i < extrafields_f.length; ++i) {
            variables_f.push({
                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                field: extrafields_f[i].name,
                prompt: L(extrafields_f[i].name)
            });
        }

        pages = [
            {
                title: L('psychiatricclerking_title'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    /*
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: true,
                        variables: variables_a,
                    },
                    */
                    {
                        type: "QuestionHeading",
                        bold: true,
                        text: L("psychiatricclerking_heading_current_contact")
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: variables_b
                    },
                    {
                        type: "QuestionHeading",
                        bold: true,
                        text: L("psychiatricclerking_heading_background")
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: variables_c
                    },
                    {
                        type: "QuestionHeading",
                        bold: true,
                        text: L("psychiatricclerking_heading_examination_investigations")
                    },
                    {
                        type: "QuestionText",
                        text: L('mental_state_examination')
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: true,
                        variables: variables_mse
                    },
                    {
                        type: "QuestionText",
                        text: L('physical_examination')
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: true,
                        variables: variables_pe
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: variables_d
                    },
                    {
                        type: "QuestionHeading",
                        bold: true,
                        text: L("psychiatricclerking_heading_risk_legal")
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: variables_e
                    },
                    {
                        type: "QuestionHeading",
                        bold: true,
                        text: L("psychiatricclerking_heading_summary_plan")
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: variables_f
                    }
                ]
            }
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn
        });
        questionnaire.open();
    }

});

module.exports = PsychiatricClerking;
