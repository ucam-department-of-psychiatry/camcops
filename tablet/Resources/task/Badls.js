// Badls.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "badls",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 20,
    SCORING = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 0};

fieldlist.push.apply(fieldlist, dbcommon.RESPONDENT_FIELDSPECS);
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_TEXT);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Badls(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Badls, taskcommon.BaseTask);
lang.extendPrototype(Badls, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Badls,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "badls",
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
    score: function (qnum) {
        var value = this["q" + qnum];
        if (SCORING.hasOwnProperty(value)) {
            return SCORING[value];
        }
        // Undefined...
        return 0;
    },

    totalScore: function () {
        var total = 0,
            i;
        for (i = 1; i <= nquestions; ++i) {
            total += this.score(i);
        }
        return total;
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (
            "Total score " + this.totalScore() + "/60" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            elements,
            i,
            pages,
            questionnaire;

        elements = [
            this.getRespondentQuestionnaireBlock(true),
            {
                type: "QuestionText",
                text: this.XSTRING('instruction_1')
            },
            {
                type: "QuestionText",
                text: this.XSTRING('instruction_2')
            },
            {
                type: "QuestionText",
                text: this.XSTRING('instruction_3')
            }
        ];
        for (i = 1; i <= nquestions; ++i) {
            elements.push(
                {
                    type: "QuestionText",
                    bold: true,
                    text: this.XSTRING('q' + i)
                },
                {
                    type: "QuestionMCQ",
                    showInstruction: false,
                    options: [
                        new KeyValuePair(this.XSTRING('q' + i + '_a'), 'a'),
                        new KeyValuePair(this.XSTRING('q' + i + '_b'), 'b'),
                        new KeyValuePair(this.XSTRING('q' + i + '_c'), 'c'),
                        new KeyValuePair(this.XSTRING('q' + i + '_d'), 'd'),
                        new KeyValuePair(this.XSTRING('q' + i + '_e'), 'e')
                    ],
                    field: 'q' + i
                }
            );
        }

        pages = [
            {
                title: L('t_badls'),
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

module.exports = Badls;
