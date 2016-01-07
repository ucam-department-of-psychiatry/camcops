// Madrs.js

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
    tablename = "madrs",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 10;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions, DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: "period_rated", type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

module.exports = function Madrs(patient_id) {
    var self = this;
    taskcommon.createStandardTaskMembers(self, Madrs, {
        tablename: tablename,
        fieldlist: fieldlist,
        patient_id: patient_id,
        prohibitCommercial: true
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
        return L('total_score') + " " + getTotalScore() + "/53" + self.isCompleteSuffix();
    };
    self.getDetail = function () {
        var totalscore = getTotalScore(),
            severity = (totalscore > 34 ? L('severe')
                         : (totalscore >= 20 ? L('moderate')
                            : (totalscore >= 7 ? L('mild')
                              : L('normal')
                              )
                           )
            );
        return (
            taskcommon.valueDetail(self, "madrs_q", "_s", " ", "q", 1, nquestions) +
            "\n" +
            self.getSummary() + "\n" +
            "\n" +
            L('category') + " " + severity
        );
    };

    self.edit = function (readOnly) {
        taskcommon.setDefaultClinicianVariablesAtFirstUse(self, readOnly); // Clinician info 2/3

        var KeyValuePair = require('lib/KeyValuePair'),
            QuestionMCQ = require('questionnaire/QuestionMCQ'),
            Questionnaire = require('questionnaire/Questionnaire'),
            QuestionText = require('questionnaire/QuestionText'),
            QuestionTypedVariables = require('questionnaire/QuestionTypedVariables'),
            UICONSTANTS = require('common/UICONSTANTS'),
            option1 = new KeyValuePair(L('madrs_option1'), 1),
            option3 = new KeyValuePair(L('madrs_option3'), 3),
            option5 = new KeyValuePair(L('madrs_option5'), 5),
            pages,
            questionnaire,
            i;

        function makepage(q) {
            var options = [
                new KeyValuePair(L("madrs_q" + q + "_option0"), 0),
                option1,
                new KeyValuePair(L("madrs_q" + q + "_option2"), 2),
                option3,
                new KeyValuePair(L("madrs_q" + q + "_option4"), 4),
                option5,
                new KeyValuePair(L("madrs_q" + q + "_option6"), 6)
            ];
            return {
                title: L("madrs_q" + q + "_title"),
                clinician: true,
                elements: [
                    { type: QuestionText, text: L("madrs_q" + q + "_question") },
                    {
                        type: QuestionMCQ,
                        field: "q" + q,
                        options: options
                    }
                ]
            };
        }
        pages = [
            {
                title: L('madrs_intro_title'),
                clinician: true,
                elements: [
                    taskcommon.CLINICIAN_QUESTIONNAIRE_BLOCK, // Clinician info 3/3
                    { type: QuestionText, text: L('madrs_intro_question') },
                    {
                        type: QuestionTypedVariables,
                        mandatory: true,
                        useColumns: false,
                        variables: [
                            { type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE, field: "period_rated", prompt: L("madrs_q_period_rated") }
                        ]
                    }
                ]
            }
        ];
        for (i = 1; i <= nquestions; ++i) {
            pages.push(makepage(i));
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
