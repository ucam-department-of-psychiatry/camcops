// Phq9.js

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
    tablename = "phq9",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 10,
    nscoredquestions = 9;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Phq9(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Phq9, taskcommon.BaseTask);
lang.extendPrototype(Phq9, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Phq9,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 1, nscoredquestions);
    },

    // Standard task functions
    isComplete: function () {
        if (!taskcommon.isCompleteByPrefix(this, "q", 1, 9)) {
            return false;
        }
        if (this.q10 === null) {
            if (this.getTotalScore() === 0) {
                return true;
            }
            return false;
        }
        return true;
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + "/27" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            totalscore = this.getTotalScore(),
            severity = (totalscore >= 20 ? L('severe')
                        : (totalscore >= 15 ? L('moderately_severe')
                           : (totalscore >= 10 ? L('moderate')
                              : (totalscore >= 5 ? L('mild')
                                 : L('none')
                                )
                             )
                          )
            ),
            ncore = (this.q1 >= 2 ? 1 : 0) +
                    (this.q2 >= 2 ? 1 : 0),
            nother = (this.q3 >= 2 ? 1 : 0) +
                     (this.q4 >= 2 ? 1 : 0) +
                     (this.q5 >= 2 ? 1 : 0) +
                     (this.q6 >= 2 ? 1 : 0) +
                     (this.q7 >= 2 ? 1 : 0) +
                     (this.q8 >= 2 ? 1 : 0) +
                     (this.q9 >= 1 ? 1 : 0), // Suicidality: counted WHENEVER present
            ntotal = ncore + nother,
            mds = (ncore >= 1) && (ntotal >= 5),
            ods = (ncore >= 1) && (ntotal >= 2) && (ntotal <= 4);
        // Scoring: ref PMID 10568646, http://www.phqscreeners.com/instructions/instructions.pdf
        return (
            taskcommon.valueDetail(this, "phq9_q", "_s", " ", "q", 1,
                                   nquestions) +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('phq9_mds') + " " + uifunc.yesNo(mds) + "\n" +
            L('phq9_ods') + " " + uifunc.yesNo(ods) + "\n" +
            L('phq9_depression_severity') + " " + severity
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
                title: L('phq9_title_main'),
                elements: [
                    { type: "QuestionText", text: L('phq9_stem'), bold: true },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('phq9_a0'), 0),
                            new KeyValuePair(L('phq9_a1'), 1),
                            new KeyValuePair(L('phq9_a2'), 2),
                            new KeyValuePair(L('phq9_a3'), 3)
                        ],
                        questions: [
                            L('phq9_q1'),
                            L('phq9_q2'),
                            L('phq9_q3'),
                            L('phq9_q4'),
                            L('phq9_q5'),
                            L('phq9_q6'),
                            L('phq9_q7'),
                            L('phq9_q8'),
                            L('phq9_q9')
                        ],
                        fields: [
                            'q1', 'q2', 'q3', 'q4', 'q5',
                            'q6', 'q7', 'q8', 'q9'
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: L('phq9_finalq'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('phq9_fa0'), 0),
                            new KeyValuePair(L('phq9_fa1'), 1),
                            new KeyValuePair(L('phq9_fa2'), 2),
                            new KeyValuePair(L('phq9_fa3'), 3)
                        ],
                        field: 'q10'
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
            fnFinished: self.defaultFinishedFn,
            fnShowNext: function () {
                return {
                    care: true,
                    showNext: self.isComplete()
                };
            }
        });
        questionnaire.open();
    }

});

module.exports = Phq9;
