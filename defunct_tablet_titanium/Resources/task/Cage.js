// Cage.js

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
/*global L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // TABLE
    tablename = "cage",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 4;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_TEXT);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function score(value) {
    if (value === null) {
        return 0;
    }
    return (value === taskcommon.YES_CHAR ? 1 : 0);
}

function Cage(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Cage, taskcommon.BaseTask);
lang.extendPrototype(Cage, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Cage,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    // Scoring

    getTotalScore: function () {
        var total = 0,
            i;
        for (i = 1; i <= nquestions; ++i) {
            total += score(this["q" + i]);
        }
        return total;
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (
            L('total_score') + " " + this.getTotalScore() + "/" + nquestions +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            total = this.getTotalScore();
        return (
            this.xValueDetail("q", "_s", " ", "q", 1, nquestions) +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            this.XSTRING('over_threshold') + " " + uifunc.yesNo(total >= 2)
        );
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire;

        pages = [
            {
                title: this.XSTRING('title'),
                elements: [
                    { type: "QuestionText", text: this.XSTRING('stem') },
                    {
                        type: "QuestionMCQGrid",
                        options: taskcommon.OPTIONS_YES_NO_CHAR,
                        questions: [
                            this.XSTRING('q1'),
                            this.XSTRING('q2'),
                            this.XSTRING('q3'),
                            this.XSTRING('q4')
                        ],
                        fields: [ 'q1', 'q2', 'q3', 'q4' ],
                        optionsWidthTogether: '25%'
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

module.exports = Cage;