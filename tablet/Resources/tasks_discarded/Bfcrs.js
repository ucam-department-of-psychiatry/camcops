// Bfcrs.js

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
    tablename = "bfcrs",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 23;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions, DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

var ncsiquestions = 14;

module.exports = function Bfcrs(patient_id) {
    var self = this;
    taskcommon.createStandardTaskMembers(self, Bfcrs, {
        tablename: tablename,
        fieldlist: fieldlist,
        patient_id: patient_id
    });

    // Scoring
    function getTotalScore() {
        return taskcommon.totalScoreFromPrefix(self, "q", 1, nquestions);
    }
    function getNumCSISymptoms() {
        var count = 0,
            i;
        for (i = 1; i <= ncsiquestions; ++i) {
            if (self["q" + i] > 0) {
                ++count;
            }
        }
        return count;
    }

    // Standard task functions
    self.isComplete = function () {
        return taskcommon.isCompleteFromPrefix(self, "q", 1, nquestions);
    };
    self.getSummary = function () {
        return L('total_score') + " " + getTotalScore() + "/69" + self.isCompleteSuffix();
    };
    self.getDetail = function () {
        var uifunc = require('lib/uifunc'),
            msg = "",
            numcsisymptoms = getNumCSISymptoms(),
            catatonia = (numcsisymptoms >= 2),
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += L("bfcrs_s_prefix") + i + " (" + L("bfcrs_q" + i + "_title") + "): " + self["q" + i] + "\n";
        }
        return (
            msg +
            "\n" +
            L("csi_catatonia_present") + " " + uifunc.yesNo(catatonia) + "\n" +
            "\n" +
            self.getSummary() + "\n"
        );
    };

    self.edit = function (readOnly) {
        var KeyValuePair = require('lib/KeyValuePair'),
            QuestionMCQ = require('questionnaire/QuestionMCQ'),
            Questionnaire = require('questionnaire/Questionnaire'),
            QuestionText = require('questionnaire/QuestionText'),
            pages,
            questionnaire,
            n,
            only0and3;

        function makepage(n, only0and3) {
            var options = [];
            options.push(new KeyValuePair(L("bfcrs_q" + n + "_option0"), 0));
            if (!only0and3) {
                options.push(new KeyValuePair(L("bfcrs_q" + n + "_option1"), 1));
                options.push(new KeyValuePair(L("bfcrs_q" + n + "_option2"), 2));
            }
            options.push(new KeyValuePair(L("bfcrs_q" + n + "_option3"), 3));
            return {
                title: L("bfcrs_title_prefix") + n + ": " + L("bfcrs_q" + n + "_title"),
                clinician: true,
                elements: [
                    { type: QuestionText, text: L("bfcrs_q" + n + "_question") },
                    {
                        type: QuestionMCQ,
                        field: "q" + n,
                        options: options
                    }
                ]
            };
        }

        pages = [];
        for (n = 1; n <= nquestions; ++n) {
            only0and3 = n === 13 || (n >= 17 && n <= 21);
            pages.push(makepage(n, only0and3));
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
