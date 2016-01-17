// Gad7.js

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
    tablename = "gad7",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 7;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Gad7(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Gad7, taskcommon.BaseTask);
lang.extendPrototype(Gad7, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Gad7,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

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
        return (L('total_score') + " " + this.getTotalScore() + "/21" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var totalscore = this.getTotalScore(),
            severity = (totalscore >= 15 ? L('severe')
                        : (totalscore >= 10 ? L('moderate')
                           : (totalscore >= 5 ? L('mild')
                              : L('none')
                             )
                          )
                       );
        // Scoring: ref http://www.phqscreeners.com/instructions/instructions.pdf
        return (
            taskcommon.valueDetail(this, "gad7_q", "_s", " ", "q", 1,
                                   nquestions) +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('gad7_anxiety_severity') + " " + severity
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire;

        pages = [
            {
                title: L('gad7_title'),
                elements: [
                    { type: "QuestionText", text: L('gad7_stem') },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('gad7_a0'), 0),
                            new KeyValuePair(L('gad7_a1'), 1),
                            new KeyValuePair(L('gad7_a2'), 2),
                            new KeyValuePair(L('gad7_a3'), 3)
                        ],
                        questions: [
                            L('gad7_q1'),
                            L('gad7_q2'),
                            L('gad7_q3'),
                            L('gad7_q4'),
                            L('gad7_q5'),
                            L('gad7_q6'),
                            L('gad7_q7')
                        ],
                        fields: [ 'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7']
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

module.exports = Gad7;
