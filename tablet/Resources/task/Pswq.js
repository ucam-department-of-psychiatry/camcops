// Pswq.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true, continue:true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "pswq",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 16,
    REVERSE_SCORE = [1, 3, 8, 10, 11];  // questions scored backwards;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Pswq(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Pswq, taskcommon.BaseTask);
lang.extendPrototype(Pswq, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Pswq,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "pswq",
    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // EXTRA STRINGS

    get_questions: function () {
        var arr = [],
            i;
        for (i = 1; i <= nquestions; ++i) {
            arr.push(this.XSTRING("q" + i, "Q" + i));
        }
        return arr;
    },

    // OTHER

    // Scoring
    getTotalScore: function () {
        var q,
            x,
            total = 0;
        for (q = 1; q <= nquestions; ++q) {
            x = this["q" + q];
            if (x === null) {
                continue;
            }
            if (REVERSE_SCORE.indexOf(q) !== -1) {
                x = 6 - x;  // 5 becomes 1, 1 becomes 5
            }
            total += x;
        }
        return total;
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteFromPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (
            "Total " + this.getTotalScore() + " (range 16–80) " +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            KeyValuePair = require('lib/KeyValuePair'),
            elements,
            pages,
            questionnaire;

        elements = [
            {
                type: "QuestionText",
                bold: true,
                text: this.XSTRING('instruction')
            },
            {
                type: "QuestionMCQGrid",
                options: [
                    new KeyValuePair('1: ' + this.XSTRING('anchor1'), 1),
                    new KeyValuePair('2', 2),
                    new KeyValuePair('3', 3),
                    new KeyValuePair('4', 4),
                    new KeyValuePair('5: ' + this.XSTRING('anchor5'), 5)
                ],
                questions: this.get_questions(),
                fields: taskcommon.stringArrayFromSequence("q", 1, nquestions),
                optionsWidthTogether: '65%'
            }
        ];

        pages = [
            {
                title: L('t_pswq'),
                clinician: false,
                elements: elements
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

module.exports = Pswq;
