// Icd10Manic.js

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
    tablename = "icd10manic",
    fieldlist = dbcommon.standardTaskFields(),
    CORE_NAMES = [
        'mood_elevated',
        'mood_irritable'
    ],
    HYPOMANIA_MANIA_NAMES = [
        'distractible',
        'activity',
        'sleep',
        'talkativeness',
        'recklessness',
        'social_disinhibition',
        'sexual'
    ],
    MANIA_NAMES = [
        'grandiosity',
        'flight_of_ideas'
    ],
    OTHER_CRITERIA_NAMES = [
        'sustained4days',
        'sustained7days',
        'admission_required',
        'some_interference_functioning',
        'severe_interference_functioning'
    ],
    PSYCHOSIS_NAMES = [
        'perceptual_alterations', // not psychotic
        'hallucinations_schizophrenic',
        'hallucinations_other',
        'delusions_schizophrenic',
        'delusions_other'
    ];

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'date_pertains_to', type: DBCONSTANTS.TYPE_DATE},
    {name: 'comments', type: DBCONSTANTS.TYPE_TEXT}
);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, CORE_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, HYPOMANIA_MANIA_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, MANIA_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, OTHER_CRITERIA_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, PSYCHOSIS_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Icd10Manic(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
    var moment = require('lib/moment');
    // Default values
    this.date_pertains_to = moment(); // Default is today
}

lang.inheritPrototype(Icd10Manic, taskcommon.BaseTask);
lang.extendPrototype(Icd10Manic, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Icd10Manic,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Meets criteria? These also return null for unknown.
    meets_criteria_mania_psychotic_schizophrenic: function () {
        var x = this.meets_criteria_mania_ignoring_psychosis();
        if (!x) {
            return x;
        }
        if (this.hallucinations_other || this.delusions_other) {
            return false; // that counts as manic psychosis
        }
        if (this.hallucinations_other === null ||
                this.delusions_other === null) {
            return null; // might be manic psychosis
        }
        if (this.hallucinations_schizophrenic ||
                this.delusions_schizophrenic) {
            return true;
        }
        if (this.hallucinations_schizophrenic === null ||
                this.delusions_schizophrenic === null) {
            return null;
        }
        return false;
    },

    meets_criteria_mania_psychotic_icd: function () {
        var x = this.meets_criteria_mania_ignoring_psychosis();
        if (!x) {
            return x;
        }
        if (this.hallucinations_other || this.delusions_other) {
            return true;
        }
        if (this.hallucinations_other === null ||
                this.delusions_other === null) {
            return null;
        }
        return false;
    },

    meets_criteria_mania_nonpsychotic: function () {
        var x = this.meets_criteria_mania_ignoring_psychosis();
        if (!x) {
            return x;
        }
        if (this.hallucinations_schizophrenic === null ||
                this.delusions_schizophrenic === null ||
                this.hallucinations_other === null ||
                this.delusions_other === null) {
            return null;
        }
        if (this.hallucinations_schizophrenic ||
                this.delusions_schizophrenic ||
                this.hallucinations_other ||
                this.delusions_other) {
            return false;
        }
        return true;
    },

    meets_criteria_mania_ignoring_psychosis: function () {
        // When can we say "definitely not"?
        if (this.mood_elevated === false && this.mood_irritable === false) {
            return false;
        }
        if (this.sustained7days === false &&
                this.admission_required === false) {
            return false;
        }
        var t = (
                taskcommon.countBooleans(
                    this,
                    HYPOMANIA_MANIA_NAMES
                ) +
                taskcommon.countBooleans(this, MANIA_NAMES)
            ),
            u = (
                taskcommon.numIncomplete(
                    this,
                    HYPOMANIA_MANIA_NAMES
                ) +
                taskcommon.numIncomplete(this, MANIA_NAMES)
            );
        if (this.mood_elevated && (t + u < 3)) {
            // With elevated mood, need at least 3 symptoms
            return false;
        }
        if (this.mood_elevated === false && (t + u < 4)) {
            // With only irritable mood, need at least 4 symptoms
            return false;
        }
        if (this.severe_interference_functioning === false) {
            return false;
        }
        // OK. When can we say "yes"?
        if ((this.mood_elevated || this.mood_irritable) &&
                (this.sustained7days || this.admission_required) &&
                ((this.mood_elevated && t >= 3) ||
                 (this.mood_irritable && t >= 4)) &&
                this.severe_interference_functioning) {
            return true;
        }
        return null;
    },

    meets_criteria_hypomania: function () {
        // When can we say "definitely not"?
        if (this.meets_criteria_mania_ignoring_psychosis() === true) {
            return false; // silly to call it hypomania if it's mania
        }
        if (this.mood_elevated === false && this.mood_irritable === false) {
            return false;
        }
        if (this.sustained4days === false) {
            return false;
        }
        var t = taskcommon.countBooleans(
                this,
                HYPOMANIA_MANIA_NAMES
            ),
            u = taskcommon.numIncomplete(
                this,
                HYPOMANIA_MANIA_NAMES
            );
        if (t + u < 3) {
            // Need at least 3 symptoms
            return false;
        }
        if (this.some_interference_functioning === false) {
            return false;
        }
        // OK. When can we say "yes"?
        if ((this.mood_elevated || this.mood_irritable) &&
                this.sustained4days &&
                t >= 3 &&
                this.some_interference_functioning) {
            return true;
        }
        return null;
    },

    meets_criteria_none: function () {
        var h = this.meets_criteria_hypomania(),
            m = this.meets_criteria_mania_ignoring_psychosis();
        if (h || m) {
            return false;
        }
        if (h === false && m === false) {
            return true;
        }
        return null;
    },

    psychosis_present: function () {
        if (this.hallucinations_other ||
                this.hallucinations_schizophrenic ||
                this.delusions_other ||
                this.delusions_schizophrenic) {
            return true;
        }
        if (this.hallucinations_other === null ||
                this.hallucinations_schizophrenic === null ||
                this.delusions_other === null ||
                this.delusions_schizophrenic === null) {
            return null;
        }
        return false;
    },

    get_description: function () {
        if (this.meets_criteria_mania_psychotic_schizophrenic()) {
            return L("icd10manic_category_manic_psychotic_schizophrenic");
        }
        if (this.meets_criteria_mania_psychotic_icd()) {
            return L("icd10manic_category_manic_psychotic");
        }
        if (this.meets_criteria_mania_nonpsychotic()) {
            return L("icd10manic_category_manic_nonpsychotic");
        }
        if (this.meets_criteria_hypomania()) {
            return L("icd10manic_category_hypomanic");
        }
        if (this.meets_criteria_none()) {
            return L("icd10manic_category_none");
        }
        return L("Unknown");
    },

    // Standard task functions
    isComplete: function () {
        return (
            this.date_pertains_to !== null &&
            this.meets_criteria_none() !== null
        );
    },

    getSummary: function () {
        return (
            taskcommon.formatDateSimple(this.date_pertains_to) + " " +
            this.get_description() + " " +
            this.isCompleteSuffix()
        );
    },

    detailgroup: function (arr) {
        var uifunc = require('lib/uifunc'),
            msg = "",
            i;
        for (i = 0; i < arr.length; ++i) {
            msg += taskcommon.descriptionValuePair(this, arr[i], arr[i],
                                                   uifunc.trueFalseUnknown);
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
        msg += this.detailgroup(CORE_NAMES) + "\n";
        msg += this.detailgroup(HYPOMANIA_MANIA_NAMES) + "\n";
        msg += this.detailgroup(MANIA_NAMES) + "\n";
        msg += this.detailgroup(OTHER_CRITERIA_NAMES) + "\n";
        msg += this.detailgroup(PSYCHOSIS_NAMES) + "\n";
        msg += this.getSummary();
        return msg;
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            true_false_options = taskcommon.OPTIONS_FALSE_TRUE_BOOLEAN,
            STEM = "icd10manic_",
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function editgroup(arr) {
            return {
                type: "QuestionMCQGrid",
                horizontal: true,
                options: true_false_options,
                questions: taskcommon.localizedStringArrayBySuffixArray(STEM,
                                                                        arr),
                fields: arr,
                mandatory: true
            };
        }

        pages = [
            {
                title: L('t_icd10_manic_episode'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionText",
                        text: L('icd10_symptomatic_disclaimer')
                    },
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
                        text: L('icd10manic_core'),
                        bold: true
                    },
                    editgroup(CORE_NAMES),
                    {
                        type: "QuestionText",
                        text: L('icd10manic_hypomania_mania'),
                        bold: true
                    },
                    editgroup(HYPOMANIA_MANIA_NAMES),
                    {
                        type: "QuestionText",
                        text: L('icd10manic_other_mania'),
                        bold: true
                    },
                    editgroup(MANIA_NAMES),
                    {
                        type: "QuestionText",
                        text: L('icd10manic_other_criteria'),
                        bold: true
                    },
                    editgroup(OTHER_CRITERIA_NAMES),
                    {
                        type: "QuestionText",
                        text: L('icd10manic_psychosis'),
                        bold: true
                    },
                    editgroup(PSYCHOSIS_NAMES),
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
            fnFinished: self.defaultFinishedFn
        });
        questionnaire.open();
    }

});

module.exports = Icd10Manic;
