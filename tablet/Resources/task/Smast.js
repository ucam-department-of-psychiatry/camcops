// Smast.js

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
    tablename = "smast",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 13;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_TEXT);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function score(value, question) {
    var yes = taskcommon.YES_CHAR;
    if (value === null) {
        return 0;
    }
    if (question === 1 || question === 4 || question === 5) {
        return (value === yes ? 0 : 1);
    }
    return (value === yes ? 1 : 0);
}

function Smast(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Smast, taskcommon.BaseTask);
lang.extendPrototype(Smast, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Smast,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        var total = 0,
            i;
        for (i = 1; i <= nquestions; ++i) {
            total += score(this["q" + i], i);
        }
        return total;
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + "/" +
                nquestions + this.isCompleteSuffix());
    },

    getDetail: function () {
        var totalscore = this.getTotalScore(),
            likelihood = (totalscore >= 3 ? L('smast_problem_probable')
                : (totalscore >= 2 ? L('smast_problem_possible')
                   : L('smast_problem_unlikely')
                  )
            ),
            scores = " (" + L('smast_scores') + " ",
            msg = "",
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += (L("smast_q" + i + "_s") + " " + this["q" + i] + scores +
                    score(this["q" + i], i) + ")\n");
        }
        return (msg +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('smast_problem_likelihood') + " " + likelihood
        );
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            questions = [],
            fields = [],
            i,
            pages,
            questionnaire;

        for (i = 1; i <= nquestions; ++i) {
            questions.push(L("smast_q" + i));
            fields.push("q" + i);
        }
        pages = [
            {
                title: L('smast_title'),
                elements: [
                    { type: "QuestionText", text: L('smast_stem') },
                    {
                        type: "QuestionMCQGrid",
                        options: taskcommon.OPTIONS_YES_NO_CHAR,
                        questions: questions,
                        fields: fields,
                        optionsWidthTogether: '25%',
                        subtitles: [
                            {beforeIndex: 5, subtitle: "" },
                            {beforeIndex: 10, subtitle: "" },
                            {beforeIndex: 15, subtitle: "" }
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

module.exports = Smast;
