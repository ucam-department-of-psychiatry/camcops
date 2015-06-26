// Gds15.js

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
    tablename = "gds15",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 15,
    SCORE_IF_YES = [2, 3, 4, 6, 8, 9, 10, 12, 14, 15],
    SCORE_IF_NO = [1, 5, 7, 11, 13];

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_TEXT);  // Y, N

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Gds15(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Gds15, taskcommon.BaseTask);
lang.extendPrototype(Gds15, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Gds15,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        var i,
            q,
            score = 0;
        for (i = 0; i < SCORE_IF_YES.length; ++i) {
            q = SCORE_IF_YES[i];
            if (this["q" + q] === taskcommon.YES_CHAR) {
                score += 1;
            }
        }
        for (i = 0; i < SCORE_IF_NO.length; ++i) {
            q = SCORE_IF_NO[i];
            if (this["q" + q] === taskcommon.NO_CHAR) {
                score += 1;
            }
        }
        return score;
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + "/15" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire;

        pages = [
            {
                title: L('b_gds15'),
                elements: [
                    { type: "QuestionText", text: L('gds15_instruction') },
                    {
                        type: "QuestionMCQGrid",
                        options: taskcommon.OPTIONS_YES_NO_CHAR,
                        questions: taskcommon.localizedStringArrayFromSequence(
                            'gds15_q',
                            1,
                            nquestions
                        ),
                        fields: taskcommon.stringArrayFromSequence('q', 1,
                                                                   nquestions),
                    },
                ],
            },
        ];

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

module.exports = Gds15;
