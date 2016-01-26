// Frs.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "frs",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 30,
    NEVER = 0,
    SOMETIMES = 1,
    ALWAYS = 2,
    NA = -99,
    NA_QUESTIONS = [9, 10, 11, 13, 14, 15, 17, 18, 19, 20, 21, 27],
    SPECIAL_NA_TEXT_QUESTIONS = [27],
    NO_SOMETIMES_QUESTIONS = [30],
    TABULAR_LOGIT_RANGES = [
        // tests a <= x < b
        [[100, Infinity], 5.39],
        [[97, 100], 4.12],
        [[93, 97], 3.35],
        [[90, 93], 2.86],
        [[87, 90], 2.49],
        [[83, 87], 2.19],
        [[80, 83], 1.92],
        [[77, 80], 1.68],
        [[73, 77], 1.47],
        [[70, 73], 1.26],
        [[67, 70], 1.07],
        [[63, 67], 0.88],
        [[60, 63], 0.7],
        [[57, 60], 0.52],
        [[53, 57], 0.34],
        [[50, 53], 0.16],
        [[47, 50], -0.02],
        [[43, 47], -0.2],
        [[40, 43], -0.4],
        [[37, 40], -0.59],
        [[33, 37], -0.8],
        [[30, 33], -1.03],
        [[27, 30], -1.27],
        [[23, 27], -1.54],
        [[20, 23], -1.84],
        [[17, 20], -2.18],
        [[13, 17], -2.58],
        [[10, 13], -3.09],
        [[6, 10], -3.8],
        [[3, 6], -4.99],
        [[0, 3], -6.66]
    ],
    /* Don't do this (http://stackoverflow.com/questions/12244483)
    SCORE = {
        NEVER: 1,
        SOMETIMES: 0,
        ALWAYS: 0
        // Confirmed by Eneida Mioshi 2015-01-20; "sometimes" and "always"
        // score the same.
    }
    */
    SCORE = {};

SCORE[NEVER] = 1;
SCORE[SOMETIMES] = 0;
SCORE[ALWAYS] = 0;
// Confirmed by Eneida Mioshi 2015-01-20; "sometimes" and "always"
// score the same.

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push.apply(fieldlist, dbcommon.RESPONDENT_FIELDSPECS);
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push({name: "comments", type: DBCONSTANTS.TYPE_TEXT});

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Frs(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Frs, taskcommon.BaseTask);
lang.extendPrototype(Frs, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Frs,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "frs",
    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    getSeverity: function (logit) {
        // p1593 of Mioshi et al. (2010)
        // Copes with Infinity comparisons
        if (logit >= 4.12) {
            return "very mild";
        }
        if (logit >= 1.92) {
            return "mild";
        }
        if (logit >= -0.40) {
            return "moderate";
        }
        if (logit >= -2.58) {
            return "severe";
        }
        if (logit >= -4.99) {
            return "very severe";
        }
        return "profound";
    },

    getTabularLogit: function (score) {
        // Looks up the tabulated logit from the score
        var pct_score = 100 * score,
            i,
            a,
            b,
            val;
        for (i = 0; i < TABULAR_LOGIT_RANGES.length; ++i) {
            a = TABULAR_LOGIT_RANGES[i][0][0];
            b = TABULAR_LOGIT_RANGES[i][0][1];
            if (a <= pct_score && pct_score < b) {
                val = TABULAR_LOGIT_RANGES[i][1];
                return val;
            }
        }
        return null;
    },

    getScore: function () {
        var total = 0,
            n = 0,
            q,
            value,
            score = null,
            logit = null,
            severity = "";
        for (q = 1; q <= nquestions; ++q) {
            value = this["q" + q];
            if (value !== null && value !== NA) {
                n += 1;
                total += SCORE[value];
            }
        }
        if (n > 0) {
            score = total / n;
            // logit = Math.log(score / (1 - score));  // base e
            // ... Will return Infinity if score == 1
            logit = this.getTabularLogit(score);
            severity = this.getSeverity(logit);
        }
        return {
            'total': total,
            'n': n,
            'score': score,
            'logit': logit,
            'severity': severity
        };
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        var score = this.getScore();
        return (
            "Total = " + score.total + " (0–n, higher better); " +
            "n = " + score.n + " (out of 30); " +
            "score = " + score.score + " (0–1); " +
            "tabulated logit of score = " + score.logit + "; " +
            "severity = " + score.severity +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function makeoptions(q) {
            var prefix = "q" + q + "_a_",
                opts = [new KeyValuePair(self.XSTRING(prefix + "never"),
                                         NEVER)];
            if (!lang.arrayContains(NO_SOMETIMES_QUESTIONS, q)) {
                opts.push(new KeyValuePair(self.XSTRING(prefix + "sometimes"),
                                           SOMETIMES));
            }
            opts.push(new KeyValuePair(self.XSTRING(prefix + "always"),
                                       ALWAYS));
            if (lang.arrayContains(NA_QUESTIONS, q)) {
                if (lang.arrayContains(SPECIAL_NA_TEXT_QUESTIONS, q)) {
                    opts.push(new KeyValuePair(self.XSTRING(prefix + "na"),
                                               NA));
                } else {
                    opts.push(new KeyValuePair(L("NA"), NA));
                }
            }
            return opts;
        }

        function makeqelements(q) {
            var options = makeoptions(q);
            return [
                {
                    type: "QuestionText",
                    bold: true,
                    text: self.XSTRING("q" + q + "_q")
                },
                {
                    type: "QuestionText",
                    text: self.XSTRING("q" + q + "_detail")
                },
                {
                    type: "QuestionMCQ",
                    field: "q" + q,
                    options: options,
                    showInstruction: false,
                    horizontal: false,
                    mandatory: true
                }
            ];
        }

        function makeqgroup(start, end, initial_elements) {
            var i,
                elements = initial_elements || [];
            for (i = start; i <= end; ++i) {
                elements.push.apply(elements, makeqelements(i));
            }
            return elements;
        }

        pages = [
            this.getClinicianAndRespondentDetailsPage(), // Clinician info 3/3
            {
                title: this.XSTRING('h_behaviour'),
                clinician: true,
                elements: makeqgroup(1, 7)
            },
            {
                title: this.XSTRING('h_outing'),
                clinician: true,
                elements: makeqgroup(8, 9)
            },
            {
                title: this.XSTRING('h_outing'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: self.XSTRING("houshold_instruction")
                    }
                ].concat(makeqgroup(10, 12))
            },
            {
                title: this.XSTRING('h_finances'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: self.XSTRING("finances_instruction_1")
                    },
                    {
                        type: "QuestionText",
                        text: self.XSTRING("finances_instruction_2")
                    }
                ].concat(makeqgroup(13, 16))
            },
            {
                title: this.XSTRING('h_medications'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: self.XSTRING("medications_instruction")
                    }
                ].concat(makeqgroup(17, 18))
            },
            {
                title: this.XSTRING('h_mealprep'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: self.XSTRING("mealprep_instruction")
                    }
                ].concat(makeqgroup(19, 26))
            },
            {
                title: this.XSTRING('h_selfcare'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: self.XSTRING("selfcare_instruction")
                    }
                ].concat(makeqgroup(27, 30))
            },
            {
                title: L('t_frs'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "comments",
                                prompt: L("clinicians_comments")
                            }
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

module.exports = Frs;
