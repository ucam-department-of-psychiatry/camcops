// Icd10Schizophrenia.js

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
    tablename = "icd10schizophrenia",
    fieldlist = dbcommon.standardTaskFields(),
    A_NAMES = [
        'passivity_bodily',
        'passivity_mental',
        'hv_commentary',
        'hv_discussing',
        'hv_from_body',
        'delusions',
        'delusional_perception',
        'thought_echo',
        'thought_withdrawal',
        'thought_insertion',
        'thought_broadcasting'
    ],
    B_NAMES = [
        'hallucinations_other',
        'thought_disorder',
        'catatonia'
    ],
    C_NAMES = [
        'negative'
    ],
    D_NAMES = [
        'present_one_month'
    ],
    E_NAMES = [
        'also_manic',
        'also_depressive',
        'if_mood_psychosis_first'
    ],
    F_NAMES = [
        'not_organic_or_substance'
    ],
    G_NAMES = [
        'behaviour_change',
        'performance_decline'
    ],
    H_NAMES = [
        'subtype_paranoid',
        'subtype_hebephrenic',
        'subtype_catatonic',
        'subtype_undifferentiated',
        'subtype_postschizophrenic_depression',
        'subtype_residual',
        'subtype_simple',
        'subtype_cenesthopathic'
    ],
    TAG_ALL_RELEVANT = "tag";

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'date_pertains_to', type: DBCONSTANTS.TYPE_DATE},
    {name: 'comments', type: DBCONSTANTS.TYPE_TEXT}
);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, A_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, B_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, C_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, D_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, E_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, F_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, G_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, H_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Icd10Schizophrenia(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
    var moment = require('lib/moment');
    // Default values
    this.date_pertains_to = moment(); // Default is today
}

lang.inheritPrototype(Icd10Schizophrenia, taskcommon.BaseTask);
lang.extendPrototype(Icd10Schizophrenia, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Icd10Schizophrenia,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Meets criteria? These also return null for unknown.
    meetsGeneralCriteria: function () {
        var t_1 = taskcommon.countBooleansByFieldnameArray(this, A_NAMES),
            u_1 = taskcommon.numIncompleteByFieldnameArray(this, A_NAMES),
            t_2 = (
                taskcommon.countBooleansByFieldnameArray(this, B_NAMES) +
                taskcommon.countBooleansByFieldnameArray(this, C_NAMES)
            ),
            u_2 = (
                taskcommon.numIncompleteByFieldnameArray(this, B_NAMES) +
                taskcommon.numIncompleteByFieldnameArray(this, C_NAMES)
            );
        if (t_1 + u_1 < 1 && t_2 + u_2 < 2) {
            return false;
        }
        if (this.present_one_month === false) {
            return false;
        }
        if ((this.also_manic || this.also_depressive) &&
                this.if_mood_psychosis_first === false) {
            return false;
        }
        if (this.not_organic_or_substance === false) {
            return false;
        }
        if ((t_1 >= 1 || t_2 >= 2) &&
                this.present_one_month && (
                    (
                        this.also_manic === false &&
                        this.also_depressive === false
                    ) || this.if_mood_psychosis_first
                ) && this.not_organic_or_substance) {
            return true;
        }
        return null;
    },

    // Standard task functions
    isComplete: function () {
        return (
            this.date_pertains_to !== null &&
            this.meetsGeneralCriteria() !== null
        );
    },

    getSummary: function () {
        var uifunc = require('lib/uifunc');
        return (
            taskcommon.formatDateSimple(this.date_pertains_to) + " " +
            L('icd10sz_meets_general_criteria') + ": " +
            uifunc.yesNoUnknown(this.meetsGeneralCriteria()) +
            this.isCompleteSuffix()
        );
    },

    detailgroup: function (arr, pa) {
        var uifunc = require('lib/uifunc'),
            msg = "",
            i;
        for (i = 0; i < arr.length; ++i) {
            msg += taskcommon.descriptionValuePair(
                this,
                arr[i],
                arr[i],
                pa ? uifunc.presentAbsentUnknown : uifunc.trueFalseUnknown
            );
        }
        return msg;
    },

    getDetail: function () {
        var msg = (
            taskcommon.descriptionValuePair(this, "date_pertains_to",
                                            "date_pertains_to",
                                            taskcommon.formatDateSimple) +
            taskcommon.descriptionValuePair(this, "examiners_comments",
                                            "comments")
        );
        msg += this.detailgroup(A_NAMES) + "\n";
        msg += this.detailgroup(B_NAMES) + "\n";
        msg += this.detailgroup(C_NAMES) + "\n";
        msg += this.detailgroup(D_NAMES) + "\n";
        msg += this.detailgroup(E_NAMES) + "\n";
        msg += this.detailgroup(F_NAMES) + "\n";
        msg += this.detailgroup(G_NAMES) + "\n";
        msg += this.detailgroup(H_NAMES) + "\n";
        msg += this.getSummary();
        return msg;
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            true_false_options = taskcommon.OPTIONS_FALSE_TRUE_BOOLEAN,
            present_absent_options = taskcommon.OPTIONS_ABSENT_PRESENT_BOOLEAN,
            STEM = "icd10sz_",
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function editgroup(arr, pa, mayBeRelevant) {
            return {
                elementTag: mayBeRelevant ? TAG_ALL_RELEVANT : null,
                type: "QuestionMCQGrid",
                horizontal: true,
                options: pa ? present_absent_options : true_false_options,
                questions: taskcommon.localizedStringArrayBySuffixArray(STEM,
                                                                        arr),
                fields: arr,
                mandatory: mayBeRelevant
            };
        }

        pages = [
            {
                title: L('t_icd10_schizophrenia'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionText",
                        text: L('date_pertains_to'),
                        bold: true
                    },
                    {
                        type: "QuestionDateTime",
                        field: "date_pertains_to",
                        showTime: false
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10sz_comments')
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10sz_core'),
                        bold: true
                    },
                    editgroup(A_NAMES, true, true),
                    {
                        type: "QuestionText",
                        text: L('icd10sz_other_positive'),
                        bold: true
                    },
                    editgroup(B_NAMES, true, true),
                    {
                        type: "QuestionText",
                        text: L('icd10sz_negative_title'),
                        bold: true
                    },
                    editgroup(C_NAMES, true, true),
                    {
                        type: "QuestionText",
                        text: L('icd10sz_other_criteria'),
                        bold: true
                    },
                    editgroup(D_NAMES, false, true),
                    {
                        type: "QuestionText",
                        text: L('icd10sz_duration_comment')
                    },
                    editgroup(E_NAMES, false, true),
                    {
                        type: "QuestionText",
                        text: L('icd10sz_affective_comment')
                    },
                    editgroup(F_NAMES, false, true),
                    {
                        type: "QuestionText",
                        text: L('icd10sz_simple_title'),
                        bold: true
                    },
                    editgroup(G_NAMES, true, true),
                    {
                        type: "QuestionText",
                        text: L('icd10sz_subtypes'),
                        bold: true
                    },
                    editgroup(H_NAMES, true, false),
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "comments",
                                prompt: L("comments")
                            }
                        ]
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
            fnFinished: self.defaultFinishedFn,
            fnShowNext: function () {
                var known = (self.meetsGeneralCriteria() !== null);
                questionnaire.setMandatoryByTag(TAG_ALL_RELEVANT, !known);
                return { care: false };
            }
        });
        questionnaire.open();
    }

});

module.exports = Icd10Schizophrenia;
