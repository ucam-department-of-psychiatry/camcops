// Epds.js

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
    tablename = "epds",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 10;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions, DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

module.exports = function Epds(patient_id) {
    var self = this;
    taskcommon.createStandardTaskMembers(self, Epds, {
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
        return (
            L('total_score') + " " + getTotalScore() + "/30, " +
            L('epds_suicidality') + " " + self.q10 + "/3" +
            self.isCompleteSuffix()
        );
    };
    self.getDetail = function () {
        var uifunc = require('lib/uifunc');
        return (
            taskcommon.valueDetail(self, "epds_q", "_s", " ", "q", 1, nquestions) +
            "\n" +
            self.getSummary() + "\n" +
            "\n" +
            L('epds_above_cutoff_1') + " " + uifunc.yesNo(getTotalScore() >= 10) + "\n" +
            L('epds_above_cutoff_2') + " " + uifunc.yesNo(getTotalScore() >= 13) + "\n" +
            L('epds_always_look_at_suicide')
        );
    };

    self.edit = function (readOnly) {
        var KeyValuePair = require('lib/KeyValuePair'),
            QuestionMCQ = require('questionnaire/QuestionMCQ'),
            Questionnaire = require('questionnaire/Questionnaire'),
            QuestionText = require('questionnaire/QuestionText'),
            pages,
            questionnaire;

        function makepage(n, reverse) {
            var options = [],
                i;
            if (reverse) {
                for (i = 3; i >= 0; --i) {
                    options.push(new KeyValuePair(L("epds_q" + n + "_option" + i), i));
                }
            } else {
                for (i = 0; i <= 3; ++i) {
                    options.push(new KeyValuePair(L("epds_q" + n + "_option" + i), i));
                }
            }
            return {
                title: L("epds_q" + n + "_title"),
                elements: [
                    { type: QuestionText, text: L("epds_question_common") },
                    { type: QuestionText, text: L("epds_q" + n + "_question"), bold: true },
                    { type: QuestionMCQ, field: "q" + n, options: options }
                ]
            };
        }
        pages = [];
        pages.push(makepage(1, false));
        pages.push(makepage(2, false));
        pages.push(makepage(3, true));
        pages.push(makepage(4, false));
        pages.push(makepage(5, true));
        pages.push(makepage(6, true));
        pages.push(makepage(7, true));
        pages.push(makepage(8, true));
        pages.push(makepage(9, true));
        pages.push(makepage(10, true));

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
