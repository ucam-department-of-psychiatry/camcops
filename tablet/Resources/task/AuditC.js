// AuditC.js

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
    tablename = "audit_c",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 3;

// AUDIT-C = FIRST THREE QUESTION OF THE AUDIT.

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function AuditC(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(AuditC, taskcommon.BaseTask);
lang.extendPrototype(AuditC, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: AuditC,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _prohibitCommercial: true,

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 1, nquestions);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (
            L('total_score') + " " +
            this.getTotalScore() + "/" + nquestions * 4 +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return (
            taskcommon.valueDetail(this, "audit_q", "_s", " ", "q", 1,
                                   nquestions) +
            "\n" +
            this.getSummary()
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pages = [
                {
                    title: L("t_audit"),
                    clinician: true,
                    elements: [
                        {
                            type: "QuestionText",
                            text: L("audit_instructions_1")
                        },
                        {
                            type: "QuestionText",
                            text: L("audit_instructions_3")
                        },
                        {
                            type: "QuestionText",
                            bold: true,
                            text: L("audit_instructions_4")
                        },
                        {
                            type: "QuestionText",
                            text: L("audit_instructions_5")
                        }
                    ]
                },
                {
                    title: L("audit_c_qprefix") + " 1",
                    clinician: true,
                    elements: [
                        {
                            type: "QuestionText",
                            bold: true,
                            text: L("audit_c_q1_question")
                        },
                        {
                            type: "QuestionText",
                            text: L("audit_c_instruction")
                        },
                        {
                            type: "QuestionMCQ",
                            field: "q1",
                            showInstruction: false,
                            options: [
                                new KeyValuePair(L("audit_q1_option0"), 0),
                                new KeyValuePair(L("audit_q1_option1"), 1),
                                new KeyValuePair(L("audit_q1_option2"), 2),
                                new KeyValuePair(L("audit_q1_option3"), 3),
                                new KeyValuePair(L("audit_q1_option4"), 4)
                            ]
                        }
                    ]
                },
                {
                    title: L("audit_c_qprefix") + " 2",
                    clinician: true,
                    elements: [
                        {
                            type: "QuestionText",
                            bold: true,
                            text: L("audit_c_q2_question")
                        },
                        {
                            type: "QuestionMCQ",
                            field: "q2",
                            showInstruction: false,
                            options: [
                                new KeyValuePair(L("audit_c_q2_option0"), 0),
                                // ... modified
                                new KeyValuePair(L("audit_q2_option1"), 1),
                                new KeyValuePair(L("audit_q2_option2"), 2),
                                new KeyValuePair(L("audit_q2_option3"), 3),
                                new KeyValuePair(L("audit_q2_option4"), 4)
                            ]
                        }
                    ]
                },
                {
                    title: L("audit_c_qprefix") + " 3",
                    clinician: true,
                    elements: [
                        {
                            type: "QuestionText",
                            bold: true,
                            text: L("audit_c_q3_question")
                        },
                        {
                            type: "QuestionMCQ",
                            field: "q3",
                            showInstruction: false,
                            options: [
                                new KeyValuePair(L("audit_q3to8_option0"), 0),
                                new KeyValuePair(L("audit_q3to8_option1"), 1),
                                new KeyValuePair(L("audit_q3to8_option2"), 2),
                                new KeyValuePair(L("audit_q3to8_option3"), 3),
                                new KeyValuePair(L("audit_q3to8_option4"), 4)
                            ]
                        }
                    ]
                }
            ],
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

module.exports = AuditC;
