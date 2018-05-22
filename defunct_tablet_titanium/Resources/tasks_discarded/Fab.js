// Fab.js

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
    tablename = "fab",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 6;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions, DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

module.exports = function Fab(patient_id) {
    var self = this;
    taskcommon.createStandardTaskMembers(self, Fab, {
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
        return (L('total_score') + " " + getTotalScore() + "/18" +
                self.isCompleteSuffix());
    };
    self.getDetail = function () {
        var uifunc = require('lib/uifunc');
        return (
            taskcommon.valueDetail(self, "fab_q", "_s", " ", "q", 1, nquestions) +
            "\n" +
            self.getSummary() + "\n" +
            "\n" +
            L('fab_below_cutoff') + " " + uifunc.yesNo(getTotalScore() <= 12) + "\n"
        );
    };

    self.edit = function (readOnly) {
        taskcommon.setDefaultClinicianVariablesAtFirstUse(self, readOnly); // Clinician info 2/3

        var KeyValuePair = require('lib/KeyValuePair'),
            QuestionMCQ = require('questionnaire/QuestionMCQ'),
            Questionnaire = require('questionnaire/Questionnaire'),
            QuestionText = require('questionnaire/QuestionText'),
            QuestionCountdown = require('questionnaire/QuestionCountdown'),
            pages,
            questionnaire;

        function makepage(n, reverse) {
            var options = [],
                elements = [ { type: QuestionText, text: L("fab_q" + n + "_question") } ],
                i;
            if (n === 2) {
                elements.push({ type: QuestionCountdown, seconds: 60 });
            }
            elements.push({ type: QuestionMCQ, field: "q" + n, options: options });
            if (reverse) {
                for (i = 3; i >= 0; --i) {
                    options.push(new KeyValuePair(L("fab_q" + n + "_option" + i), i));
                }
            } else {
                for (i = 0; i <= 3; ++i) {
                    options.push(new KeyValuePair(L("fab_q" + n + "_option" + i), i));
                }
            }
            return {
                title: L("fab_q" + n + "_title"),
                clinician: true,
                elements: elements
            };
        }
        pages = [ taskcommon.CLINICIAN_DETAILS_PAGE ]; // Clinician info 3/3
        pages.push(makepage(1, true));
        pages.push(makepage(2, true));
        pages.push(makepage(3, true));
        pages.push(makepage(4, true));
        pages.push(makepage(5, true));
        pages.push(makepage(6, true));

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
