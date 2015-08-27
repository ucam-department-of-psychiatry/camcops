// Audit.js

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
    tablename = "audit",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 10;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Audit(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Audit, taskcommon.BaseTask);
lang.extendPrototype(Audit, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Audit,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _prohibitCommercial: true,

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScore(this, "q", 1, nquestions);
    },

    // Standard task functions
    isComplete: function () {
        var i;
        if (this.q1 === null || this.q9 === null || this.q10 === null) {
            // Always need these three.
            return false;
        }
        if (this.q1 === 0) {
            // Special limited-information completeness
            return true;
        }
        if (this.q2 !== null &&
                this.q3 !== null &&
                (this.q2 + this.q3 === 0)) {
            // Special limited-information completeness
            return true;
        }
        // Otherwise, any null values cause problems
        for (i = 1; i <= nquestions; ++i) {
            if (this["q" + i] === null) {
                return false;
            }
        }
        return true;
    },

    getSummary: function () {
        return (
            L('total_score') + " " +
            this.getTotalScore() + "/" + nquestions * 4 +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc');
        return (
            taskcommon.valueDetail(this, "audit_q", "_s", " ", "q", 1,
                                   nquestions) +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('audit_exceeds_standard_cutoff') + " " +
            uifunc.yesNo(this.getTotalScore() >= 8)
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            options1 = [
                new KeyValuePair(L("audit_q1_option0"), 0),
                new KeyValuePair(L("audit_q1_option1"), 1),
                new KeyValuePair(L("audit_q1_option2"), 2),
                new KeyValuePair(L("audit_q1_option3"), 3),
                new KeyValuePair(L("audit_q1_option4"), 4)
            ],
            options2 = [
                new KeyValuePair(L("audit_q2_option0"), 0),
                new KeyValuePair(L("audit_q2_option1"), 1),
                new KeyValuePair(L("audit_q2_option2"), 2),
                new KeyValuePair(L("audit_q2_option3"), 3),
                new KeyValuePair(L("audit_q2_option4"), 4)
            ],
            options3to8 = [
                new KeyValuePair(L("audit_q3to8_option0"), 0),
                new KeyValuePair(L("audit_q3to8_option1"), 1),
                new KeyValuePair(L("audit_q3to8_option2"), 2),
                new KeyValuePair(L("audit_q3to8_option3"), 3),
                new KeyValuePair(L("audit_q3to8_option4"), 4)
            ],
            options9to10 = [
                new KeyValuePair(L("audit_q9to10_option0"), 0),
                new KeyValuePair(L("audit_q9to10_option2"), 2),
                new KeyValuePair(L("audit_q9to10_option4"), 4)
            ],
            pages = [{
                title: L("t_audit"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("audit_instructions_1")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: L("audit_instructions_2")
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
            }],
            questionnaire;

        function makepage(question, options) {
            return {
                title: L("audit_q" + question + "_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("audit_q" + question + "_question")
                    },
                    {
                        type: "QuestionMCQ",
                        showInstruction: false,
                        field: "q" + question,
                        options: options
                    }
                ]
            };
        }
        pages.push(makepage(1, options1));
        pages.push(makepage(2, options2));
        pages.push(makepage(3, options3to8));
        pages.push(makepage(4, options3to8));
        pages.push(makepage(5, options3to8));
        pages.push(makepage(6, options3to8));
        pages.push(makepage(7, options3to8));
        pages.push(makepage(8, options3to8));
        pages.push(makepage(9, options9to10));
        pages.push(makepage(10, options9to10));

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn,
            fnNextPage: function (pageId_zero_based) {
                var offset = 0,
                    // +1 for being zero-based; -1 for the instruction page
                    real_pageId = pageId_zero_based + offset;
                if (real_pageId === 1 && self.q1 === 0) {
                    return 9 - offset; // skip to Q9 (by zero-based index)
                }
                if (real_pageId === 3 && (self.q2 + self.q3 === 0)) {
                    return 9 - offset; // skip to Q9 (by zero-based index)
                }
                return pageId_zero_based + 1; // by default, move to the next question
            },
            fnPreviousPage: function (pageId_zero_based) {
                var offset = 0,
                    // +1 for being zero-based; -1 for the instruction page
                    real_pageId = pageId_zero_based + offset;
                if (real_pageId === 9 && self.q1 === 0) {
                    return 1 - offset; // skip to Q1 (by zero-based index)
                }
                if (real_pageId === 9 && (self.q2 + self.q3 === 0)) {
                    return 3 - offset; // skip to Q3 (by zero-based index)
                }
                return pageId_zero_based - 1; // by default, move to the previous question
            }
        });
        questionnaire.open();
    }
});

module.exports = Audit;
