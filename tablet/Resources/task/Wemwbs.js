// Wemwbs.js

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

/*jslint node: true, newcap: true, nomen: true */
"use strict";
/*global L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "wemwbs",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 14,
    minqscore = 1,
    maxqscore = 5;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Wemwbs(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Wemwbs, taskcommon.BaseTask);
lang.extendPrototype(Wemwbs, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Wemwbs,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScoreFromPrefix(this, "q", 1, nquestions);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteFromPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + " (range " +
                (nquestions * minqscore) +
                "–" +
                (nquestions * maxqscore) +
                ")" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        return (
            taskcommon.valueDetail(this, "wemwbs_q", "", ": ", "q", 1,
                                   nquestions) +
            "\n" +
            this.getSummary()
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
                title: L('t_wemwbs'),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('wemwbs_prompt'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('wemwbs_a1'), 1),
                            new KeyValuePair(L('wemwbs_a2'), 2),
                            new KeyValuePair(L('wemwbs_a3'), 3),
                            new KeyValuePair(L('wemwbs_a4'), 4),
                            new KeyValuePair(L('wemwbs_a5'), 5)
                        ],
                        questions: taskcommon.localizedStringArrayFromSequence(
                            "wemwbs_q",
                            1,
                            nquestions
                        ),
                        fields: taskcommon.stringArrayFromSequence("q", 1,
                                                                   nquestions)
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

module.exports = Wemwbs;
