// Dast.js

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
    // TABLE
    tablename = "dast",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 28;

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
    if (question === 4 || question === 5 || question === 7) {
        return (value === yes ? 0 : 1);
    }
    return (value === yes ? 1 : 0);
}

function Dast(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Dast, taskcommon.BaseTask);
lang.extendPrototype(Dast, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Dast,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _prohibitCommercial: true,

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
            scores = " (" + L('dast_scores') + " ",
            msg = "",
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += (
                L("dast_q" + i + "_s") + " " +
                this["q" + i] + scores + score(this["q" + i], i) + ")\n"
            );
        }
        return (msg +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('dast_exceeds_standard_cutoff_1') + " " +
            uifunc.yesNo(this.getTotalScore() >= 6) + "\n" +
            L('dast_exceeds_standard_cutoff_2') + " " +
            uifunc.yesNo(this.getTotalScore() >= 11)
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
            questions.push(L("dast_q" + i));
            fields.push("q" + i);
        }
        pages = [
            {
                title: L('dast_title'),
                elements: [
                    { type: "QuestionText", text: L('dast_stem') },
                    {
                        type: "QuestionMCQGrid",
                        options: taskcommon.OPTIONS_YES_NO_CHAR,
                        questions: questions,
                        fields: fields,
                        optionsWidthTogether: '25%',
                        subtitles: [
                            {beforeIndex: 5, subtitle: "" },
                            {beforeIndex: 10, subtitle: "" },
                            {beforeIndex: 15, subtitle: "" },
                            {beforeIndex: 20, subtitle: "" },
                            {beforeIndex: 25, subtitle: "" }
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

module.exports = Dast;
