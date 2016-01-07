// Icd10Mixed.js

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
    tablename = "icd10mixed",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'date_pertains_to', type: DBCONSTANTS.TYPE_DATE},
    {name: 'comments', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'mixture_or_rapid_alternation', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'duration_at_least_2_weeks', type: DBCONSTANTS.TYPE_BOOLEAN}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Icd10Mixed(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
    var moment = require('lib/moment');
    // Default values
    this.date_pertains_to = moment(); // Default is today
}

lang.inheritPrototype(Icd10Mixed, taskcommon.BaseTask);
lang.extendPrototype(Icd10Mixed, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Icd10Mixed,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Meets criteria? These also return null for unknown.
    meets_criteria: function () {
        if (this.mixture_or_rapid_alternation &&
                this.duration_at_least_2_weeks) {
            return true;
        }
        if (this.mixture_or_rapid_alternation === false ||
                this.duration_at_least_2_weeks === false) {
            return false;
        }
        return null;
    },

    // Standard task functions
    isComplete: function () {
        return this.meets_criteria() !== null;
    },

    getSummary: function () {
        var uifunc = require('lib/uifunc');
        return (
            taskcommon.formatDateSimple(this.date_pertains_to) + " " +
            L("meets_criteria") + " " +
            uifunc.trueFalseUnknown(this.meets_criteria()) +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc');
        return (
            taskcommon.descriptionValuePair(this, "date_pertains_to",
                                            "date_pertains_to",
                                            taskcommon.formatDateSimple) +
            taskcommon.descriptionValuePair(this, "examiners_comments",
                                            "comments") +
            taskcommon.descriptionValuePair(this, L("icd10mixed_a"),
                                            "mixture_or_rapid_alternation",
                                            uifunc.trueFalseUnknown) +
            taskcommon.descriptionValuePair(this, L("icd10mixed_b"),
                                            "duration_at_least_2_weeks",
                                            uifunc.trueFalseUnknown) +
            "\n" +
            this.getSummary()
        );
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            true_false_options = taskcommon.OPTIONS_FALSE_TRUE_BOOLEAN,
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

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
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: true_false_options,
                        questions: [
                            L("icd10mixed_a"),
                            L("icd10mixed_b")
                        ],
                        fields: [
                            "mixture_or_rapid_alternation",
                            "duration_at_least_2_weeks"
                        ],
                        mandatory: true
                    },
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

module.exports = Icd10Mixed;
