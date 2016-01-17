// Iesr.js

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
    tablename = "iesr",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 22,
    AVOIDANCE_QUESTIONS = [5, 7, 8, 11, 12, 13, 17, 22],
    INTRUSION_QUESTIONS = [1, 2, 3, 6, 9, 16, 20],
    HYPERAROUSAL_QUESTIONS = [4, 10, 14, 15, 18, 19, 21];

fieldlist.push(
    {name: 'event', type: DBCONSTANTS.TYPE_TEXT}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Iesr(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Iesr, taskcommon.BaseTask);
lang.extendPrototype(Iesr, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Iesr,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "iesr",
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

    // Standard task functions
    isComplete: function () {
        return this.event && taskcommon.isCompleteByPrefix(this, "q", 1, nquestions);
    },

    getTotalScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 1, nquestions);
    },

    getAvoidanceScore: function () {
        return taskcommon.totalScoreBySuffixes(this, "q",
                                                    AVOIDANCE_QUESTIONS);
    },

    getIntrusionScore: function () {
        return taskcommon.totalScoreBySuffixes(this, "q",
                                                    INTRUSION_QUESTIONS);
    },

    getHyperarousalScore: function () {
        return taskcommon.totalScoreBySuffixes(this, "q",
                                                    HYPERAROUSAL_QUESTIONS);
    },

    getSummary: function () {
        return (
            "Total " + this.getTotalScore() + "/88, " +
            "avoidance " + this.getAvoidanceScore() + "/32, " +
            "intrusion " + this.getAvoidanceScore() + "/28, " +
            "hyperarousal " + this.getAvoidanceScore() + "/28 " +
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
            UICONSTANTS = require('common/UICONSTANTS'),
            elements,
            pages,
            questionnaire;

        elements = [
            {
                type: "QuestionText",
                bold: true,
                text: this.XSTRING('instruction_1')
            },
            {
                type: "QuestionTypedVariables",
                mandatory: true,
                useColumns: false,
                variables: [
                    {
                        type: UICONSTANTS.TYPEDVAR_TEXT,
                        field: "event",
                        prompt: L('iesr_event')
                    }
                ]
            },
            {
                type: "QuestionText",
                bold: true,
                text: this.XSTRING('instruction_2')
            },
            {
                type: "QuestionMCQGrid",
                options: [
                    new KeyValuePair(L('iesr_a0'), 0),
                    new KeyValuePair(L('iesr_a1'), 1),
                    new KeyValuePair(L('iesr_a2'), 2),
                    new KeyValuePair(L('iesr_a3'), 3),
                    new KeyValuePair(L('iesr_a4'), 4)
                ],
                questions: this.get_questions(),
                fields: taskcommon.stringArrayFromSequence("q", 1, nquestions),
                optionsWidthTogether: '65%'
            }
        ];

        pages = [
            {
                title: L('t_iesr'),
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

module.exports = Iesr;
