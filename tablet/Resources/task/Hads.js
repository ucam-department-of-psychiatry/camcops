// Hads.js

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
    extrastrings = require('table/extrastrings'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // TABLE
    tablename = "hads",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 14,
    EXTRASTRING_TASKNAME = "hads",
    INVERTED_QUESTIONS = [1, 3, 5, 6, 8, 10, 11, 13],
    ANXIETY_QUESTIONS = [1, 3, 5, 7, 9, 11, 13],
    DEPRESSION_QUESTIONS = [2, 4, 6, 8, 10, 12, 14];

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Hads(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Hads, taskcommon.BaseTask);
lang.extendPrototype(Hads, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Hads,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    isTaskCrippled: function () {
        return !extrastrings.task_exists(EXTRASTRING_TASKNAME);
    },

    // EXTRA STRINGS

    XSTRING: function (name) {
        return extrastrings.get(EXTRASTRING_TASKNAME, name,
                                "[HADS: " + name + "]");
    },

    // OTHER

    // Scoring
    getScore: function (questions) {
        var i,
            n,
            value,
            score = 0;
        for (i = 0; i < questions.length; ++i) {
            n = questions[i];
            value = this['q' + n];
            if (value !== null) {
                score += value;
            }
        }
        return score;
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (
            L('hads_anxiety_score') + ": " +
            this.getScore(ANXIETY_QUESTIONS) + "/21. " +
            L('hads_depression_score') + ": " +
            this.getScore(DEPRESSION_QUESTIONS) + "/21 " +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    questionOptionsInverted: function (n) {
        // Does option 3 appear at the top of the list?
        return (INVERTED_QUESTIONS.indexOf(n) !== -1);
    },

    getCrippledPages: function () {
        var KeyValuePair = require('lib/KeyValuePair'),
            elements,
            page,
            hads_options = [
                new KeyValuePair("0", 0),
                new KeyValuePair("1", 1),
                new KeyValuePair("2", 2),
                new KeyValuePair("3", 3),
            ],
            questions = [],
            fields = [],
            n,
            q;
        for (n = 1; n <= nquestions; ++n) {
            q = L("question") + " " + n;
            if ((ANXIETY_QUESTIONS.indexOf(n) !== -1)) {
                q += " (A)";
            }
            if ((DEPRESSION_QUESTIONS.indexOf(n) !== -1)) {
                q += " (D)";
            }
            questions.push(q);
            fields.push("q" + n);
        }
        elements = [
            {
                type: "QuestionText",
                text: L('data_collection_only'),
                bold: true
            },
            {
                type: "QuestionText",
                text: L('enter_the_answers')
            },
            {
                type: "QuestionMCQGrid",
                mandatory: true,
                options: hads_options,
                questions: questions,
                fields: fields,
            },
        ];
        page = {
            title: L("t_hads"),
            elements: elements,
        };
        return [page];
    },

    getFullPages: function () {
        var KeyValuePair = require('lib/KeyValuePair'),
            pages = [{
                title: L("t_hads"),
                elements: [
                    {
                        type: "QuestionText",
                        text: this.XSTRING('instruction_1'),
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING('instruction_2'),
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING('instruction_3'),
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: L('press_next_to_continue'),
                    },
                ],
            }],
            elements,
            options,
            n;
        for (n = 1; n <= nquestions; ++n) {
            options = [
                new KeyValuePair(this.XSTRING('q' + n + '_a0'), 0),
                new KeyValuePair(this.XSTRING('q' + n + '_a1'), 1),
                new KeyValuePair(this.XSTRING('q' + n + '_a2'), 2),
                new KeyValuePair(this.XSTRING('q' + n + '_a3'), 3),
            ];
            if (this.questionOptionsInverted(n)) {
                options.reverse();
            }
            elements = [
                {
                    type: "QuestionText",
                    bold: true,
                    text: this.XSTRING('q' + n + '_stem'),
                },
                {
                    type: "QuestionMCQ",
                    mandatory: true,
                    showInstruction: false,
                    options: options,
                    field: 'q' + n,
                },
            ];
            pages.push({
                title: L("t_hads") + " Q" + n,
                elements: elements,
            });
        }
        return pages;
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire;
        if (this.isTaskCrippled()) {
            pages = this.getCrippledPages();
        } else {
            pages = this.getFullPages();
        }
        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn,
        });
        questionnaire.open();
    },
});

module.exports = Hads;
