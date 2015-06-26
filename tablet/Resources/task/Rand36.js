// Rand36.js

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
    lang = require('lib/lang'),
    tablename = "rand36",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 36,
    DISPLAY_DP = 1;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function pageTitle(n) {
    return L("rand36_title") + " " + L("page") + " " + n;
}

function Rand36(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Rand36, taskcommon.BaseTask);
lang.extendPrototype(Rand36, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Rand36,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    recode: function (q) {
        var x = this["q" + q]; // response
        if (x === null || x < 1) {
            return null;
        }
        // http://m.rand.org/content/dam/rand/www/external/health/surveys_tools/mos/mos_core_36item_scoring.pdf
        switch (q) {
        case 1:
        case 2:
        case 20:
        case 22:
        case 34:
        case 36:
            // 1 becomes 100, 2 => 75, 3 => 50, 4 =>25, 5 => 0
            if (x > 5) {
                return null;
            }
            return 100 - 25 * (x - 1);

        case 3:
        case 4:
        case 5:
        case 6:
        case 7:
        case 8:
        case 9:
        case 10:
        case 11:
        case 12:
            // 1 => 0, 2 => 50, 3 => 100
            if (x > 3) {
                return null;
            }
            return 50 * (x - 1);

        case 13:
        case 14:
        case 15:
        case 16:
        case 17:
        case 18:
        case 19:
            // 1 => 0, 2 => 100
            if (x > 2) {
                return null;
            }
            return 100 * (x - 1);

        case 21:
        case 23:
        case 26:
        case 27:
        case 30:
            // 1 => 100, 2 => 80, 3 => 60, 4 => 40, 5 => 20, 6 => 0
            if (x > 6) {
                return null;
            }
            return 100 - 20 * (x - 1);

        case 24:
        case 25:
        case 28:
        case 29:
        case 31:
            // 1 => 0, 2 => 20, 3 => 40, 4 => 60, 5 => 80, 6 => 100
            if (x > 6) {
                return null;
            }
            return 20 * (x - 1);

        case 32:
        case 33:
        case 35:
            // 1 => 0, 2 => 25, 3 => 50, 4 => 75, 5 => 100
            if (x > 5) {
                return null;
            }
            return 25 * (x - 1);
        }
        return null;
    },

    scorePhysicalFunctioning: function () {
        return lang.toFixedOrNull(
            lang.mean(this.recode(3), this.recode(4), this.recode(5),
                      this.recode(6), this.recode(7), this.recode(8),
                      this.recode(9), this.recode(10), this.recode(11),
                      this.recode(12)),
            DISPLAY_DP
        );
    },

    scoreRoleLimitationsPhysical: function () {
        return lang.toFixedOrNull(
            lang.mean(this.recode(13), this.recode(14), this.recode(15),
                      this.recode(16)),
            DISPLAY_DP
        );
    },

    scoreRoleLimitationsEmotional: function () {
        return lang.toFixedOrNull(
            lang.mean(this.recode(17), this.recode(18), this.recode(19)),
            DISPLAY_DP
        );
    },

    scoreEnergy: function () {
        return lang.toFixedOrNull(
            lang.mean(this.recode(23), this.recode(27), this.recode(29),
                      this.recode(31)),
            DISPLAY_DP
        );
    },

    scoreEmotionalWellbeing: function () {
        return lang.toFixedOrNull(
            lang.mean(this.recode(24), this.recode(25), this.recode(26),
                      this.recode(28), this.recode(30)),
            DISPLAY_DP
        );
    },

    scoreSocialFunctioning: function () {
        return lang.toFixedOrNull(
            lang.mean(this.recode(20), this.recode(32)),
            DISPLAY_DP
        );
    },

    scorePain: function () {
        return lang.toFixedOrNull(
            lang.mean(this.recode(21), this.recode(22)),
            DISPLAY_DP
        );
    },

    scoreGeneralHealth: function () {
        return lang.toFixedOrNull(
            lang.mean(this.recode(1), this.recode(33), this.recode(34),
                      this.recode(35), this.recode(36)),
            DISPLAY_DP
        );
    },

    scoreOverall: function () {
        var values = [],
            q;
        for (q = 1; q <= nquestions; ++q) {
            values.push(this.recode(q));
        }
        return lang.toFixedOrNull(lang.mean(values), DISPLAY_DP);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (
            L('rand36_score_overall') + ": " + this.scoreOverall() + "/100" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return (
            this.getSummary() + "\n" +

            L("rand36_score_physical_functioning") + ": " +
            this.scorePhysicalFunctioning() + "/100\n" +

            L("rand36_score_role_limitations_physical") + ": " +
            this.scoreRoleLimitationsPhysical() + "/100\n" +

            L("rand36_score_role_limitations_emotional") + ": " +
            this.scoreRoleLimitationsEmotional() + "/100\n" +

            L("rand36_score_energy") + ": " + this.scoreEnergy() + "/100\n" +

            L("rand36_score_emotional_wellbeing") + ": " +
            this.scoreEmotionalWellbeing() + "/100\n" +

            L("rand36_score_social_functioning") + ": " +
            this.scoreSocialFunctioning() + "/100\n" +

            L("rand36_score_pain") + ": " + this.scorePain() + "/100\n" +

            L("rand36_score_general_health") + ": " +
            this.scoreGeneralHealth() + "/100\n"
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pagenum = 1,
            pages,
            questionnaire;

        pages = [
            {
                title: pageTitle(pagenum++),
                elements: [
                    { type: "QuestionText", text: L('rand36_q1'), bold: true },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('rand36_q1_option1'), 1),
                            new KeyValuePair(L('rand36_q1_option2'), 2),
                            new KeyValuePair(L('rand36_q1_option3'), 3),
                            new KeyValuePair(L('rand36_q1_option4'), 4),
                            new KeyValuePair(L('rand36_q1_option5'), 5),
                        ],
                        field: "q1",
                        showInstruction: false,
                        horizontal: false
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    { type: "QuestionText", text: L('rand36_q2'), bold: true },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('rand36_q2_option1'), 1),
                            new KeyValuePair(L('rand36_q2_option2'), 2),
                            new KeyValuePair(L('rand36_q2_option3'), 3),
                            new KeyValuePair(L('rand36_q2_option4'), 4),
                            new KeyValuePair(L('rand36_q2_option5'), 5),
                        ],
                        field: "q2",
                        showInstruction: false,
                        horizontal: false
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('rand36_activities_q'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('rand36_activities_option1'), 1),
                            new KeyValuePair(L('rand36_activities_option2'), 2),
                            new KeyValuePair(L('rand36_activities_option3'), 3)
                        ],
                        questions: [
                            L("rand36_q3"),
                            L("rand36_q4"),
                            L("rand36_q5"),
                            L("rand36_q6"),
                            L("rand36_q7"),
                            L("rand36_q8"),
                            L("rand36_q9"),
                            L("rand36_q10"),
                            L("rand36_q11"),
                            L("rand36_q12"),
                        ],
                        fields: [
                            "q3",
                            "q4",
                            "q5",
                            "q6",
                            "q7",
                            "q8",
                            "q9",
                            "q10",
                            "q11",
                            "q12",
                        ],
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('rand36_work_activities_physical_q'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('rand36_yesno_option1'), 1),
                            new KeyValuePair(L('rand36_yesno_option2'), 2),
                        ],
                        questions: [
                            L("rand36_q13"),
                            L("rand36_q14"),
                            L("rand36_q15"),
                            L("rand36_q16"),
                        ],
                        fields: [
                            "q13",
                            "q14",
                            "q15",
                            "q16",
                        ],
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('rand36_work_activities_emotional_q'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('rand36_yesno_option1'), 1),
                            new KeyValuePair(L('rand36_yesno_option2'), 2),
                        ],
                        questions: [
                            L("rand36_q17"),
                            L("rand36_q18"),
                            L("rand36_q19"),
                        ],
                        fields: [
                            "q17",
                            "q18",
                            "q19",
                        ],
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    { type: "QuestionText", text: L('rand36_q20'), bold: true },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('rand36_q20_option1'), 1),
                            new KeyValuePair(L('rand36_q20_option2'), 2),
                            new KeyValuePair(L('rand36_q20_option3'), 3),
                            new KeyValuePair(L('rand36_q20_option4'), 4),
                            new KeyValuePair(L('rand36_q20_option5'), 5),
                        ],
                        field: "q20",
                        showInstruction: false,
                        horizontal: false
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    { type: "QuestionText", text: L('rand36_q21'), bold: true },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('rand36_q21_option1'), 1),
                            new KeyValuePair(L('rand36_q21_option2'), 2),
                            new KeyValuePair(L('rand36_q21_option3'), 3),
                            new KeyValuePair(L('rand36_q21_option4'), 4),
                            new KeyValuePair(L('rand36_q21_option5'), 5),
                            new KeyValuePair(L('rand36_q21_option6'), 6),
                        ],
                        field: "q21",
                        showInstruction: false,
                        horizontal: false
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    { type: "QuestionText", text: L('rand36_q22'), bold: true },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('rand36_q22_option1'), 1),
                            new KeyValuePair(L('rand36_q22_option2'), 2),
                            new KeyValuePair(L('rand36_q22_option3'), 3),
                            new KeyValuePair(L('rand36_q22_option4'), 4),
                            new KeyValuePair(L('rand36_q22_option5'), 5),
                        ],
                        field: "q22",
                        showInstruction: false,
                        horizontal: false
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('rand36_last4weeks_q_a'),
                        bold: false
                    },
                    {
                        type: "QuestionText",
                        text: L('rand36_last4weeks_q_b'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('rand36_last4weeks_option1'), 1),
                            new KeyValuePair(L('rand36_last4weeks_option2'), 2),
                            new KeyValuePair(L('rand36_last4weeks_option3'), 3),
                            new KeyValuePair(L('rand36_last4weeks_option4'), 4),
                            new KeyValuePair(L('rand36_last4weeks_option5'), 5),
                            new KeyValuePair(L('rand36_last4weeks_option6'), 6),
                        ],
                        questions: [
                            L("rand36_q23"),
                            L("rand36_q24"),
                            L("rand36_q25"),
                            L("rand36_q26"),
                            L("rand36_q27"),
                            L("rand36_q28"),
                            L("rand36_q29"),
                            L("rand36_q30"),
                            L("rand36_q31"),
                        ],
                        fields: [
                            "q23",
                            "q24",
                            "q25",
                            "q26",
                            "q27",
                            "q28",
                            "q29",
                            "q30",
                            "q31",
                        ],
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    { type: "QuestionText", text: L('rand36_q32'), bold: true },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('rand36_q32_option1'), 1),
                            new KeyValuePair(L('rand36_q32_option2'), 2),
                            new KeyValuePair(L('rand36_q32_option3'), 3),
                            new KeyValuePair(L('rand36_q32_option4'), 4),
                            new KeyValuePair(L('rand36_q32_option5'), 5),
                        ],
                        field: "q32",
                        showInstruction: false,
                        horizontal: false
                    },
                ],
            },
            {
                title: pageTitle(pagenum++),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('rand36_q33to36stem'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('rand36_q33to36_option1'), 1),
                            new KeyValuePair(L('rand36_q33to36_option2'), 2),
                            new KeyValuePair(L('rand36_q33to36_option3'), 3),
                            new KeyValuePair(L('rand36_q33to36_option4'), 4),
                            new KeyValuePair(L('rand36_q33to36_option5'), 5),
                        ],
                        questions: [
                            L("rand36_q33"),
                            L("rand36_q34"),
                            L("rand36_q35"),
                            L("rand36_q36"),
                        ],
                        fields: [
                            "q33",
                            "q34",
                            "q35",
                            "q36",
                        ],
                    },
                ],
            },
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn,
        });
        questionnaire.open();
    },

});

module.exports = Rand36;
