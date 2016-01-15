// LshsA.js

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
    tablename = "lshs_a",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 12;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions, DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

module.exports = function LshsA(patient_id) {
    var self = this;
    taskcommon.createStandardTaskMembers(self, LshsA, {
        tablename: tablename,
        fieldlist: fieldlist,
        patient_id: patient_id
    });

    // Scoring
    function getTotalScore() {
        return taskcommon.totalScoreFromPrefix(self, "q", 1, nquestions);
    }

    // Standard task functions
    self.isComplete = function () {
        return taskcommon.isCompleteFromPrefix(self, "q", 1, nquestions);
    };
    self.getSummary = function () {
        return L('total_score') + " " + getTotalScore() + "/48" + self.isCompleteSuffix();
    };
    self.getDetail = function () {
        return (
            taskcommon.valueDetail(self, "lshs_a_q", "_s", " ", "q", 1, nquestions) +
            "\n" +
            self.getSummary() + "\n"
        );
    };

    self.edit = function (readOnly) {
        var KeyValuePair = require('lib/KeyValuePair'),
            QuestionMCQ = require('questionnaire/QuestionMCQ'),
            Questionnaire = require('questionnaire/Questionnaire'),
            QuestionText = require('questionnaire/QuestionText'),
            options = [
                new KeyValuePair(L("lshs_a_option0"), 0),
                new KeyValuePair(L("lshs_a_option1"), 1),
                new KeyValuePair(L("lshs_a_option2"), 2),
                new KeyValuePair(L("lshs_a_option3"), 3),
                new KeyValuePair(L("lshs_a_option4"), 4)
            ],
            pages,
            questionnaire,
            n;

        function makepage(n) {
            return {
                title: L("lshs_a_titleprefix") + " " + n,
                elements: [
                    { type: QuestionText, text: L("lshs_a_q" + n + "_question") },
                    { type: QuestionMCQ, field: "q" + n, options: options }
                ]
            };
        }
        pages = [];
        for (n = 1; n <= nquestions; ++n) {
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
