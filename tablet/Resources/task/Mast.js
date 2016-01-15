// Mast.js

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
    tablename = "mast",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 24;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_TEXT);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function score(value, question) {
    if (value === null) {
        return 0;
    }
    var yes = taskcommon.YES_CHAR,
        presence = (value === yes ? 1 : 0), // for most questions
        points = 2; // Points per question; most score 2
    if (question === 1 || question === 4 || question === 6 || question === 7) {
        presence = (value === yes ? 0 : 1);
        // for these questions, negative responses are alcoholic
    }
    if (question === 3 || question === 5 || question === 9 || question === 16) {
        points = 1;
    } else if (question === 8 || question === 19 || question === 20) {
        points = 5;
    }
    return points * presence;
}

function Mast(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Mast, taskcommon.BaseTask);
lang.extendPrototype(Mast, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Mast,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

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
        return taskcommon.isCompleteFromPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + "/53" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            scores = " (" + L('mast_scores') + " ",
            msg = "",
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += (L("mast_q" + i + "_s") + " " + this["q" + i] + scores +
                    score(this["q" + i], i) + ")\n");
        }
        return (msg +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('mast_exceeds_threshold') + " " +
            uifunc.yesNo(this.getTotalScore() >= 13)
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
            questions.push(L("mast_q" + i));
            fields.push("q" + i);
        }
        pages = [
            {
                title: L('mast_title'),
                elements: [
                    { type: "QuestionText", text: L('mast_stem') },
                    {
                        type: "QuestionMCQGrid",
                        options: taskcommon.OPTIONS_YES_NO_CHAR,
                        questions: questions,
                        fields: fields,
                        optionsWidthTogether: '25%',
                        subtitles: [
                            {beforeIndex: 6, subtitle: "" },
                            {beforeIndex: 12, subtitle: "" },
                            {beforeIndex: 18, subtitle: "" }
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

module.exports = Mast;
