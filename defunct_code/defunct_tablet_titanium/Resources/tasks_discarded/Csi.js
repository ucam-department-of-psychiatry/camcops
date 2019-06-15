// Csi.js

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
    tablename = "csi",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 14; // the first 14 of the BFCRS

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions, DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

module.exports = function Csi(patient_id) {
    // Start with a record structure.
    var self = this;
    taskcommon.createStandardTaskMembers(self, Csi, {
        tablename: tablename,
        fieldlist: fieldlist,
        patient_id: patient_id
    });

    // Scoring
    function getTotalScore() {
        return taskcommon.totalScoreByPrefix(self, "q", 1, nquestions);
    }

    // Standard task functions
    self.isComplete = function () {
        return taskcommon.isCompleteByPrefix(self, "q", 1, nquestions);
    };
    self.getSummary = function () {
        return L('total_score') + " " + getTotalScore() + "/14" + self.isCompleteSuffix();
    };
    self.getDetail = function () {
        var uifunc = require('lib/uifunc'),
            numsymptoms = getTotalScore(),
            catatonia = (numsymptoms >= 2),
            msg = "",
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += L("bfcrs_s_prefix") + i + " (" + L("bfcrs_q" + i + "_title") + "): " + uifunc.yesNoNull(self["q" + i]) + "\n";
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
            QuestionMCQGrid = require('questionnaire/QuestionMCQGrid'),
            Questionnaire = require('questionnaire/Questionnaire'),
            QuestionText = require('questionnaire/QuestionText'),
            options = [
                new KeyValuePair(L('Absent'), 0),
                new KeyValuePair(L('Present'), 1)
            ],
            fields = [],
            qs = [],
            n,
            pages,
            questionnaire;

        for (n = 1; n <= nquestions; ++n) {
            fields.push("q" + n);
            qs.push(n + ". " + L("bfcrs_q" + n + "_title") + ". " + L("bfcrs_q" + n + "_question"));
        }
        pages = [
            {
                title: L("bfcrs_csi_title"),
                clinician: true,
                elements: [
                    { type: QuestionText, text: L("csi_stem") },
                    {
                        type: QuestionMCQGrid,
                        options: options,
                        questions: qs,
                        fields: fields
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
    };

    return self;
};
