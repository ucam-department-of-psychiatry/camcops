// Icd10Schizotypal.js

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
    tablename = "icd10schizotypal",
    fieldlist = dbcommon.standardTaskFields(),
    N_A = 9;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'date_pertains_to', type: DBCONSTANTS.TYPE_DATE},
    {name: 'comments', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'b', type: DBCONSTANTS.TYPE_BOOLEAN}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "a", 1, N_A,
                                DBCONSTANTS.TYPE_BOOLEAN);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Icd10Schizotypal(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
    var moment = require('lib/moment');
    // Default values
    this.date_pertains_to = moment(); // Default is today
}

lang.inheritPrototype(Icd10Schizotypal, taskcommon.BaseTask);
lang.extendPrototype(Icd10Schizotypal, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Icd10Schizotypal,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Meets criteria? These also return null for unknown.
    meetsCriteria: function () {
        if (!this.isComplete()) {
            return null;
        }
        return (
            taskcommon.countBooleans(this, "a", 1, N_A) >= 4 &&
            this.b
        );
    },

    // Standard task functions
    isComplete: function () {
        return (
            this.date_pertains_to !== null &&
            taskcommon.isComplete(this, "a", 1, N_A) &&
            this.b !== null
        );
    },

    getSummary: function () {
        var uifunc = require('lib/uifunc');
        return (
            taskcommon.formatDateSimple(this.date_pertains_to) + " " +
            L('meets_criteria') + ": " +
            uifunc.yesNoUnknown(this.meetsCriteria()) +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc');
        return (
            L('date_pertains_to') + " " +
            taskcommon.formatDateSimple(this.date_pertains_to) + "\n" +
            L('examiners_comments') + ": " + this.comments + "\n" +
            L('meets_criteria') + ": " +
            uifunc.yesNoUnknown(this.meetsCriteria()) + "\n" +
            this.isCompleteSuffix()
        );
    },

    edit: function (readOnly) {
        var self = this,
            UICONSTANTS = require('common/UICONSTANTS'),
            Questionnaire = require('questionnaire/Questionnaire'),
            yes_no_options = taskcommon.OPTIONS_FALSE_TRUE_BOOLEAN,
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        pages = [
            {
                title: L('icd10schizotypal_title'),
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
                        text: L('icd10schizotypal_a'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "icd10schizotypal_a",
                            1,
                            N_A
                        ),
                        fields: taskcommon.stringArrayFromSequence("a", 1,
                                                                   N_A),
                        mandatory: true
                    },
                    {
                        type: "QuestionText",
                        text: L('and'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        options: yes_no_options,
                        questions: [ L("icd10schizotypal_b") ],
                        fields: [ "b" ],
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

module.exports = Icd10Schizotypal;
