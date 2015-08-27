// CgiSch.js

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
    tablename = "cgisch",
    fieldlist = dbcommon.standardTaskFields(),
    NQ_PER_SECTION = 5;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "severity", 1, NQ_PER_SECTION,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "change", 1, NQ_PER_SECTION,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function CgiSch(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(CgiSch, taskcommon.BaseTask);
lang.extendPrototype(CgiSch, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: CgiSch,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    // Standard task functions
    isComplete: function () {
        return (
            taskcommon.isComplete(this, "severity", 1, NQ_PER_SECTION) &&
            taskcommon.isComplete(this, "change", 1, NQ_PER_SECTION)
        );
    },

    getSummary: function () {
        return (
            L('cgisch_summary_i_5') + ": " + this.severity5 + ". " +
            L('cgisch_summary_ii_5') + ": " + this.change5 + "." +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return (
            L('cgisch_i_title') + "\n" +
            "\n" +
            L('cgisch_q1') + ": " + this.severity1 + "\n" +
            L('cgisch_q2') + ": " + this.severity2 + "\n" +
            L('cgisch_q3') + ": " + this.severity3 + "\n" +
            L('cgisch_q4') + ": " + this.severity4 + "\n" +
            L('cgisch_q5') + ": " + this.severity5 + "\n" +
            "\n" +
            L('cgisch_ii_title') + "\n" +
            "\n" +
            L('cgisch_q1') + ": " + this.change1 + "\n" +
            L('cgisch_q2') + ": " + this.change2 + "\n" +
            L('cgisch_q3') + ": " + this.change3 + "\n" +
            L('cgisch_q4') + ": " + this.change4 + "\n" +
            L('cgisch_q5') + ": " + this.change5 + "\n" +
            "\n" +
            this.isCompleteSuffix()
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            severity_options = [],
            i,
            change_options = [],
            questions = [],
            severity_fields = [],
            change_fields = [],
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        for (i = 1; i <= 7; ++i) {
            severity_options.push(new KeyValuePair(L("cgisch_i_option" + i),
                                                   i));
        }
        for (i = 1; i <= 7; ++i) {
            change_options.push(new KeyValuePair(L("cgisch_ii_option" + i),
                                                 i));
        }
        change_options.push(new KeyValuePair(L("cgisch_ii_option9"), 9));
        for (i = 1; i <= NQ_PER_SECTION; ++i) {
            questions.push(L("cgisch_q" + i));
            severity_fields.push("severity" + i);
            change_fields.push("change" + i);
        }

        pages = [
            self.getClinicianDetailsPage(), // Clinician info 3/3
            {
                title: L("cgisch_i_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("cgisch_i_question"),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        optionsWidthTogether: "75%",
                        options: severity_options,
                        questions: questions,
                        fields: severity_fields
                    }
                ]
            },
            {
                title: L("cgisch_ii_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("cgisch_ii_question"),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        optionsWidthTogether: "75%",
                        options: change_options,
                        questions: questions,
                        fields: change_fields
                    },
                    {
                        type: "QuestionText",
                        text: L("cgisch_ii_postscript")
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

module.exports = CgiSch;
