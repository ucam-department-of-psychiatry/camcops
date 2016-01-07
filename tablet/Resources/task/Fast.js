// Fast.js

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
    tablename = "fast",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 4,
    yes = "Y",
    no = "N";

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Fast(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Fast, taskcommon.BaseTask);
lang.extendPrototype(Fast, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Fast,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScore(this, "q", 1, nquestions);
    },

    isPositive: function () {
        if (this.q1 === 0) {
            return false; // "Never"
        }
        if (this.q1 === 3 || this.q1 === 4) {
            return true; // "Weekly" or "Daily..."
        }
        return (this.getTotalScore() >= 3);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        var uifunc = require('lib/uifunc');
        return (L('fast_positive') + " " + uifunc.yesNo(this.isPositive()) +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        return taskcommon.valueDetail(this, "fast_q", "_s", " ", "q", 1,
                                      nquestions) +
            "\n" +
            L('total_score') + " " + this.getTotalScore() + "/16\n" +
            "\n" +
            this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            mainoptions = [
                new KeyValuePair(L('fast_q1to3_option0'), 0),
                new KeyValuePair(L('fast_q1to3_option1'), 1),
                new KeyValuePair(L('fast_q1to3_option2'), 2),
                new KeyValuePair(L('fast_q1to3_option3'), 3),
                new KeyValuePair(L('fast_q1to3_option4'), 4)
            ],
            pages,
            questionnaire;

        pages = [
            {
                title: L('fast_title'),
                elements: [
                    { type: "QuestionText", text: L('fast_info') },
                    { type: "QuestionText", text: L('fast_q1'), bold: true },
                    {
                        type: "QuestionMCQ",
                        field: "q1",
                        options: mainoptions
                    },
                    { type: "QuestionText", text: L('fast_q2'), bold: true },
                    {
                        type: "QuestionMCQ",
                        field: "q2",
                        options: mainoptions
                    },
                    { type: "QuestionText", text: L('fast_q3'), bold: true },
                    {
                        type: "QuestionMCQ",
                        field: "q3",
                        options: mainoptions
                    },
                    { type: "QuestionText", text: L('fast_q4'), bold: true },
                    {
                        type: "QuestionMCQ",
                        field: "q4",
                        options: [
                            new KeyValuePair(L('fast_q4_option0'), 0),
                            new KeyValuePair(L('fast_q4_option2'), 2),
                            new KeyValuePair(L('fast_q4_option4'), 4)
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

module.exports = Fast;
