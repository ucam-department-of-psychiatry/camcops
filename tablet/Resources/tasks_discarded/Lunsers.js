// Lunsers.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, continue: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    tablename = "lunsers",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 51,
    list_epse = [19, 29, 34, 37, 40, 43, 48],
    list_anticholinergic = [6, 10, 32, 38, 51],
    list_allergic = [1, 35, 47, 49],
    list_miscellaneous = [5, 22, 39, 44],
    list_psychic = [2, 4, 9, 14, 18, 21, 23, 26, 31, 41],
    list_otherautonomic = [15, 16, 20, 27, 36],
    list_hormonal_female = [7, 13, 17, 24, 46, 50],
    list_hormonal_male = [7, 17, 24, 46],
    list_redherrings = [3, 8, 11, 12, 25, 28, 30, 33, 42, 45];

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions, DBCONSTANTS.TYPE_INTEGER);

// Crash when a button is touched with 51 questions.
// Lots of: !!! Unable to convert unknown Java object class 'org.appcelerator.kroll.KrollRuntime$1' to Js value !!!
// Then: JNI ERROR (app bug): local reference table overflow (max=512)
// https://developer.appcelerator.com/question/140132/scrollview-with-over-500-elements
// Fixed by changing event-sending method to app-wide.

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

module.exports = function Lunsers(patient_id) {
    var self = this;
    taskcommon.createStandardTaskMembers(self, Lunsers, {
        tablename: tablename,
        fieldlist: fieldlist,
        patient_id: patient_id
    });

    // Scoring
    function getTotalScore(female) {
        var total = 0,
            i;
        for (i = 1; i <= nquestions; ++i) {
            if (!female && (i === 13 || i === 50)) {
                continue;
            }
            total += self["q" + i];
        }
        return total;
    }
    function getGroupScore(list) {
        var total = 0,
            i;
        for (i = 0; i < list.length; ++i) {
            total += self["q" + list[i]];
        }
        return total;
    }

    // Standard task functions
    self.isComplete = function () {
        var female = self.isFemale(),
            i;
        for (i = 1; i <= nquestions; ++i) {
            if (!female && (i === 13 || i === 50)) {
                continue;
            }
            if (self["q" + i] === null) {
                return false;
            }
        }
        return true;
    };
    self.getSummary = function () {
        var female = self.isFemale(),
            max = female ? 204 : 196;
        return L('total_score') + " " + getTotalScore(female) + "/" + max + self.isCompleteSuffix();
    };
    self.getDetail = function () {
        var female = self.isFemale(),
            msg = "",
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += "Q" + i + " (" + L("lunsers_q" + i) + "): " + self["q" + i] + "\n";
        }
        return (
            msg +
            "\n" +
            L("lunsers_group_epse") + ": " + getGroupScore(list_epse) + "/28\n" +
            L("lunsers_group_anticholinergic") + ": " + getGroupScore(list_anticholinergic) + "/20\n" +
            L("lunsers_group_allergic") + ": " + getGroupScore(list_allergic) + "/16\n" +
            L("lunsers_group_miscellaneous") + ": " + getGroupScore(list_miscellaneous) + "/16\n" +
            L("lunsers_group_psychic") + ": " + getGroupScore(list_psychic) + "/40\n" +
            L("lunsers_group_otherautonomic") + ": " + getGroupScore(list_otherautonomic) + "/20\n" +
            L("lunsers_group_hormonal") + ": " + getGroupScore(female ? list_hormonal_female : list_hormonal_male) + "/" + (female ? 24 : 16) + "\n" +
            L("lunsers_group_redherrings") + ": " + getGroupScore(list_redherrings) + "/40\n" +
            "\n" +
            L("lunsers_sideeffects") + ": " + getGroupScore(list_epse) + "/28\n" +
            self.getSummary() + "\n"
        );
    };

    self.edit = function (readOnly) {
        var female = self.isFemale(),
            KeyValuePair = require('lib/KeyValuePair'),
            QuestionMCQGrid = require('questionnaire/QuestionMCQGrid'),
            Questionnaire = require('questionnaire/Questionnaire'),
            QuestionText = require('questionnaire/QuestionText'),
            options = [
                new KeyValuePair(L('lunsers_option0'), 0),
                new KeyValuePair(L('lunsers_option1'), 1),
                new KeyValuePair(L('lunsers_option2'), 2),
                new KeyValuePair(L('lunsers_option3'), 3),
                new KeyValuePair(L('lunsers_option4'), 4)
            ],
            fields = [],
            qs = [],
            n,
            pages,
            questionnaire;

        for (n = 1; n <= nquestions; ++n) {
            if (female && (n === 13 || n === 50)) {
                continue;
            }
            fields.push("q" + n);
            qs.push(n + ". " + L("lunsers_q" + n));
        }
        pages = [
            {
                title: L("lunsers_title"),
                elements: [
                    { type: QuestionText, text: L("lunsers_stem") },
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
