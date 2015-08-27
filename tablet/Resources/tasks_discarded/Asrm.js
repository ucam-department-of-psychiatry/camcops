// Asrm.js

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
    tablename = "asrm",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 5;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions, DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

module.exports = function Asrm(patient_id) {
    var self = this;
    taskcommon.createStandardTaskMembers(self, Asrm, {
        tablename: tablename,
        fieldlist: fieldlist,
        patient_id: patient_id
    });

    // Scoring
    function getTotalScore() {
        return taskcommon.totalScore(self, "q", 1, nquestions);
    }

    // Standard task functions
    self.isComplete = function () {
        return taskcommon.isComplete(self, "q", 1, nquestions);
    };
    self.getSummary = function () {
        return L('total_score') + " " + getTotalScore() + "/20" + self.isCompleteSuffix();
    };
    self.getDetail = function () {
        var uifunc = require('lib/uifunc');
        return taskcommon.valueDetail(self, "asrm_q", "_s", " ", "q", 1, nquestions) +
            "\n" + self.getSummary() + "\n" +
            "\n" +
            L('asrm_above_cutoff') + " " + uifunc.yesNo(getTotalScore() >= 6);
    };

    self.edit = function (readOnly) {
        var KeyValuePair = require('lib/KeyValuePair'),
            QuestionMCQ = require('questionnaire/QuestionMCQ'),
            Questionnaire = require('questionnaire/Questionnaire'),
            QuestionText = require('questionnaire/QuestionText'),
            pages = [],
            questionnaire,
            n;

        function makepage(n) {
            return {
                title: L("asrm_q" + n + "_title"),
                elements: [
                    { type: QuestionText, text: L('asrm_question') },
                    {
                        type: QuestionMCQ,
                        field: "q" + n,
                        options: [
                            new KeyValuePair(L("asrm_q" + n + "_option0"), 0),
                            new KeyValuePair(L("asrm_q" + n + "_option1"), 1),
                            new KeyValuePair(L("asrm_q" + n + "_option2"), 2),
                            new KeyValuePair(L("asrm_q" + n + "_option3"), 3),
                            new KeyValuePair(L("asrm_q" + n + "_option4"), 4)
                        ]
                    }
                ]
            };
        }

        for (n = 1; n <= 5; ++n) {
            pages.push(makepage(n));
        }

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn
        });
        questionnaire.open();
    };

    return self;
};
