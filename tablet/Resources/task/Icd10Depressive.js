// Icd10Depressive.js

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
    tablename = "icd10depressive",
    fieldlist = dbcommon.standardTaskFields(),
    CORE_NAMES = [
        'mood',
        'anhedonia',
        'energy'
    ],
    ADDITIONAL_NAMES = [
        'sleep',
        'worth',
        'appetite',
        'guilt',
        'concentration',
        'activity',
        'death'
    ],
    SOMATIC_NAMES = [
        'somatic_anhedonia',
        'somatic_emotional_unreactivity',
        'somatic_early_morning_waking',
        'somatic_mood_worse_morning',
        'somatic_psychomotor',
        'somatic_appetite',
        'somatic_weight',
        'somatic_libido'
    ],
    PSYCHOSIS_NAMES = [
        'hallucinations_schizophrenic',
        'hallucinations_other',
        'delusions_schizophrenic',
        'delusions_other',
        'stupor'
    ];

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'date_pertains_to', type: DBCONSTANTS.TYPE_DATE},
    {name: 'comments', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'duration_at_least_2_weeks', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'severe_clinically', type: DBCONSTANTS.TYPE_BOOLEAN}
);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, CORE_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, ADDITIONAL_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, SOMATIC_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendBasicFieldsFromNameArray(fieldlist, PSYCHOSIS_NAMES,
                                        DBCONSTANTS.TYPE_BOOLEAN);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Icd10Depressive(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
    var moment = require('lib/moment');
    // Default values
    this.date_pertains_to = moment(); // Default is today
}

lang.inheritPrototype(Icd10Depressive, taskcommon.BaseTask);
lang.extendPrototype(Icd10Depressive, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Icd10Depressive,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    n_core: function () {
        return taskcommon.countBooleansByFieldnameArray(this, CORE_NAMES);
    },

    n_additional: function () {
        return taskcommon.countBooleansByFieldnameArray(this, ADDITIONAL_NAMES);
    },

    n_total: function () {
        return this.n_core() + this.n_additional();
    },

    n_somatic: function () {
        return taskcommon.countBooleansByFieldnameArray(this, SOMATIC_NAMES);
    },

    main_complete: function () {
        return (
            this.duration_at_least_2_weeks !== null &&
            taskcommon.isCompleteByFieldnameArray(this, CORE_NAMES) &&
            taskcommon.isCompleteByFieldnameArray(this, ADDITIONAL_NAMES)
        ) || (
            this.severe_clinically
        );
    },

    // Meets criteria? These also return null for unknown.
    meets_criteria_severe_psychotic_schizophrenic: function () {
        var x = this.meets_criteria_severe_ignoring_psychosis();
        if (!x) {
            return x;
        }
        if (this.stupor || this.hallucinations_other || this.delusions_other) {
            return false; // that counts as F32.3
        }
        if (this.stupor === null || this.hallucinations_other === null ||
                this.delusions_other === null) {
            return null; // might be F32.3
        }
        if (this.hallucinations_schizophrenic || this.delusions_schizophrenic) {
            return true;
        }
        if (this.hallucinations_schizophrenic === null ||
                this.delusions_schizophrenic === null) {
            return null;
        }
        return false;
    },

    meets_criteria_severe_psychotic_icd: function () {
        var x = this.meets_criteria_severe_ignoring_psychosis();
        if (!x) {
            return x;
        }
        if (this.stupor || this.hallucinations_other || this.delusions_other) {
            return true;
        }
        if (this.stupor === null || this.hallucinations_other === null ||
                this.delusions_other === null) {
            return null;
        }
        return false;
    },

    meets_criteria_severe_nonpsychotic: function () {
        var x = this.meets_criteria_severe_ignoring_psychosis();
        if (!x) {
            return x;
        }
        if (!taskcommon.isCompleteByFieldnameArray(this, PSYCHOSIS_NAMES)) {
            return null;
        }
        return (
            taskcommon.countBooleansByFieldnameArray(this,
                                                     PSYCHOSIS_NAMES) === 0
        );
    },

    meets_criteria_severe_ignoring_psychosis: function () {
        if (this.severe_clinically) {
            return true;
        }
        if (this.duration_at_least_2_weeks !== null &&
                !this.duration_at_least_2_weeks) {
            return false; // too short
        }
        if (this.n_core() >= 3 && this.n_total() >= 8) {
            return true;
        }
        if (!this.main_complete()) {
            return null; // addition of more information might increase severity
        }
        return false;
    },

    meets_criteria_moderate: function () {
        if (this.severe_clinically) {
            return false; // too severe
        }
        if (this.duration_at_least_2_weeks !== null &&
                !this.duration_at_least_2_weeks) {
            return false; // too short
        }
        if (this.n_core() >= 3 && this.n_total() >= 8) {
            return false; // too severe; that's severe
        }
        if (!this.main_complete()) {
            return null;
            // addition of more information might increase severity
        }
        if (this.n_core() >= 2 && this.n_total() >= 6) {
            return true;
        }
        return false;
    },

    meets_criteria_mild: function () {
        if (this.severe_clinically) {
            return false; // too severe
        }
        if (this.duration_at_least_2_weeks !== null &&
                !this.duration_at_least_2_weeks) {
            return false; // too short
        }
        if (this.n_core() >= 2 && this.n_total() >= 6) {
            return false; // too severe; that's moderate
        }
        if (!this.main_complete()) {
            return null;
            // addition of more information might increase severity
        }
        if (this.n_core() >= 2 && this.n_total() >= 4) {
            return true;
        }
        return false;
    },

    meets_criteria_none: function () {
        if (this.severe_clinically) {
            return false; // too severe
        }
        if (this.duration_at_least_2_weeks !== null &&
                !this.duration_at_least_2_weeks) {
            return true; // too short for depression
        }
        if (this.n_core() >= 2 && this.n_total() >= 4) {
            return false; // too severe
        }
        if (!this.main_complete()) {
            return null;
            // addition of more information might increase severity
        }
        return true;
    },

    meets_criteria_somatic: function () {
        var t = this.n_somatic(),
            u = taskcommon.numIncompleteByFieldnameArray(this, SOMATIC_NAMES);
        if (t >= 4) {
            return true;
        }
        if (t + u < 4) {
            return false;
        }
        return null;
    },

    get_somatic_description: function () {
        var x = this.meets_criteria_somatic();
        if (x === null) {
            return L("icd10depressive_category_somatic_unknown");
        }
        if (x) {
            return L("icd10depressive_category_with_somatic");
        }
        return L("icd10depressive_category_without_somatic");
    },

    get_main_description: function () {
        if (this.meets_criteria_severe_psychotic_schizophrenic()) {
            return L("icd10depressive_category_severe_psychotic_schizophrenic");
        }
        if (this.meets_criteria_severe_psychotic_icd()) {
            return L("icd10depressive_category_severe_psychotic");
        }
        if (this.meets_criteria_severe_nonpsychotic()) {
            return L("icd10depressive_category_severe_nonpsychotic");
        }
        if (this.meets_criteria_moderate()) {
            return L("icd10depressive_category_moderate");
        }
        if (this.meets_criteria_mild()) {
            return L("icd10depressive_category_mild");
        }
        if (this.meets_criteria_none()) {
            return L("icd10depressive_category_none");
        }
        return L("Unknown");
    },

    get_full_description: function () {
        var skipSomatic = this.main_complete() && this.meets_criteria_none();
        return (
            this.get_main_description() +
            (skipSomatic ? "" : " " + this.get_somatic_description())
        );
    },

    // Standard task functions
    isComplete: function () {
        return (
            this.date_pertains_to !== null &&
            this.main_complete()
        );
    },

    getSummary: function () {
        var skipSomatic = this.main_complete() && this.meets_criteria_none();
        return (
            taskcommon.formatDateSimple(this.date_pertains_to) + " " +
            this.get_main_description() + " " +
            (skipSomatic ? "" : this.get_somatic_description()) +
            this.isCompleteSuffix()
        );
    },

    detailgroup: function (arr) {
        var uifunc = require('lib/uifunc'),
            msg = "",
            i;
        for (i = 0; i < arr.length; ++i) {
            msg += taskcommon.descriptionValuePair(this, arr[i], arr[i],
                                                   uifunc.presentAbsentUnknown);
        }
        return msg;
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            msg;
        msg = (
            taskcommon.descriptionValuePair(this, "date_pertains_to",
                                            "date_pertains_to",
                                            taskcommon.formatDateSimple) +
            taskcommon.descriptionValuePair(this, "examiners_comments",
                                            "comments") +
            taskcommon.descriptionValuePair(this, "duration_at_least_2_weeks",
                                            "duration_at_least_2_weeks",
                                            uifunc.trueFalseUnknown)
        );
        msg += this.detailgroup(CORE_NAMES) + "\n";
        msg += this.detailgroup(ADDITIONAL_NAMES) + "\n";
        msg += taskcommon.descriptionValuePair(this, "severe_clinically",
                                               "severe_clinically",
                                               uifunc.trueFalseUnknown) + "\n";
        msg += this.detailgroup(SOMATIC_NAMES) + "\n";
        msg += this.detailgroup(PSYCHOSIS_NAMES) + "\n";
        msg += this.getSummary();
        return msg;
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            true_false_options = taskcommon.OPTIONS_FALSE_TRUE_BOOLEAN,
            present_absent_options = taskcommon.OPTIONS_ABSENT_PRESENT_BOOLEAN,
            STEM = "icd10depressive_",
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function editgroup(arr, mandatory) {
            return {
                type: "QuestionMCQGrid",
                horizontal: true,
                options: present_absent_options,
                questions: taskcommon.localizedStringArrayBySuffixArray(STEM,
                                                                        arr),
                fields: arr,
                mandatory: mandatory
            };
        }

        pages = [
            {
                title: L('t_icd10_depressive_episode'),
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
                        text: L('icd10depressive_duration_text'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: true_false_options,
                        questions: [
                            L("icd10depressive_duration_at_least_2_weeks")
                        ],
                        fields: [
                            "duration_at_least_2_weeks"
                        ],
                        mandatory: true
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10depressive_core'),
                        bold: true
                    },
                    editgroup(CORE_NAMES, true),
                    {
                        type: "QuestionText",
                        text: L('icd10depressive_additional'),
                        bold: true
                    },
                    editgroup(ADDITIONAL_NAMES, true),
                    {
                        type: "QuestionText",
                        text: L('icd10depressive_clinical_text'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: true_false_options,
                        questions: [
                            L("icd10depressive_severe_clinically")
                        ],
                        fields: [
                            "severe_clinically"
                        ],
                        mandatory: true
                    },
                    {
                        type: "QuestionText",
                        text: L('icd10depressive_somatic'),
                        bold: true
                    },
                    editgroup(SOMATIC_NAMES, false),
                    {
                        type: "QuestionText",
                        text: L('icd10depressive_psychotic'),
                        bold: true
                    },
                    editgroup(PSYCHOSIS_NAMES, true),
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

module.exports = Icd10Depressive;
