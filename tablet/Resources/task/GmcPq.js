// GmcPq.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "gmcpq",
    fieldlist = dbcommon.standardTaskFields(true),
    N_ETHNICITY_OPTIONS = 16,
    PT_ETHNICITY = "eth",
    PT_REASON = "reason",
    ET_ETHNICITY_OTHER = "eth_other",
    ET_REASON_OTHER = "reason_other";

fieldlist.push(
    {name: 'doctor', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'q1', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q2a', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'q2b', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'q2c', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'q2d', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'q2e', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'q2f', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'q2f_details', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'q3', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q4a', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q4b', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q4c', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q4d', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q4e', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q4f', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q4g', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q5a', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q5b', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q6', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'q7', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'q8', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'q9', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'q10', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'q11', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q12', type: DBCONSTANTS.TYPE_INTEGER}, // ethnicity
    {name: 'q12_details', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function GmcPq(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(GmcPq, taskcommon.BaseTask);
lang.extendPrototype(GmcPq, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: GmcPq,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _anonymous: true,

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (
            this.doctor !== null &&
            this.q1 !== null &&
            // q2...?
            this.q3 !== null &&
            this.q4a !== null &&
            this.q4b !== null &&
            this.q4c !== null &&
            this.q4d !== null &&
            this.q4e !== null &&
            this.q4f !== null &&
            this.q4g !== null &&
            this.q5a !== null &&
            this.q5b !== null &&
            this.q6 !== null &&
            this.q7 !== null &&
            this.q8 !== null
        );
    },

    getSummary: function () {
        return (L('gmcpq_q_doctor') + " " + this.doctor +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            q1options = [
                "?", L("gmcpq_q1_option1"), L("gmcpq_q1_option2"),
                L("gmcpq_q1_option3"), L("gmcpq_q1_option4")
            ],
            q4options = [
                L("gmcpq_q4_option0"), L("gmcpq_q4_option1"),
                L("gmcpq_q4_option2"), L("gmcpq_q4_option3"),
                L("gmcpq_q4_option4"), L("gmcpq_q4_option5")
            ],
            q5options = [
                L("gmcpq_q5_option0"), L("gmcpq_q5_option1"),
                L("gmcpq_q5_option2"), L("gmcpq_q5_option3"),
                L("gmcpq_q5_option4"), L("gmcpq_q5_option5")
            ],
            q11options = [
                "?", L("gmcpq_q11_option1"), L("gmcpq_q11_option2"),
                L("gmcpq_q11_option3"), L("gmcpq_q11_option4")
            ],
            q12options = [ "?" ],
            i;

        for (i = 1; i <= N_ETHNICITY_OPTIONS; ++i) {
            q12options.push(L("gmcpq_ethnicity_option" + i));
        }
        return (
            L("gmcpq_q_doctor") + " " + this.doctor + "\n" +
            L("gmcpq_q1") + taskcommon.arrayLookup(q1options, this.q1) + "\n" +
            L("gmcpq_q2") + "\n" +
            L("gmcpq_q2_a") + ": " + uifunc.yesNoNull(this.q2a) + "\n" +
            L("gmcpq_q2_b") + ": " + uifunc.yesNoNull(this.q2b) + "\n" +
            L("gmcpq_q2_c") + ": " + uifunc.yesNoNull(this.q2c) + "\n" +
            L("gmcpq_q2_d") + ": " + uifunc.yesNoNull(this.q2d) + "\n" +
            L("gmcpq_q2_e") + ": " + uifunc.yesNoNull(this.q2e) + "\n" +
            L("gmcpq_q2_f") + ": " + uifunc.yesNoNull(this.q2f) + "\n" +
            L("gmcpq_q3") + ": " + this.q3 + "\n" +
            L("gmcpq_q4") + ": " + "\n" +
            L("gmcpq_q4_a") + ": " + taskcommon.arrayLookup(q4options, this.q4a) + "\n" +
            L("gmcpq_q4_b") + ": " + taskcommon.arrayLookup(q4options, this.q4b) + "\n" +
            L("gmcpq_q4_c") + ": " + taskcommon.arrayLookup(q4options, this.q4c) + "\n" +
            L("gmcpq_q4_d") + ": " + taskcommon.arrayLookup(q4options, this.q4d) + "\n" +
            L("gmcpq_q4_e") + ": " + taskcommon.arrayLookup(q4options, this.q4e) + "\n" +
            L("gmcpq_q4_f") + ": " + taskcommon.arrayLookup(q4options, this.q4f) + "\n" +
            L("gmcpq_q4_g") + ": " + taskcommon.arrayLookup(q4options, this.q4g) + "\n" +
            L("gmcpq_q5") + " " + "\n" +
            L("gmcpq_q5_a") + ": " + taskcommon.arrayLookup(q5options, this.q5a) + "\n" +
            L("gmcpq_q5_b") + ": " + taskcommon.arrayLookup(q5options, this.q5b) + "\n" +
            L("gmcpq_q6") + ": " + uifunc.yesNoNull(this.q6) + "\n" +
            L("gmcpq_q7") + ": " + uifunc.yesNoNull(this.q7) + "\n" +
            L("gmcpq_q8") + ": " + uifunc.yesNoNull(this.q8) + "\n" +
            L("gmcpq_q9_s") + ": " + this.q9 + "\n" +
            L("sex") + " " + this.q10 + "\n" +
            L("gmcpq_q11") + " " + taskcommon.arrayLookup(q11options, this.q11) + "\n" +
            L("gmcpq_q12") + " " + taskcommon.arrayLookup(q12options, this.q12) + "\n" +
            L("gmcpq_ethnicity_other_s") + ": " + this.q12_details + "\n" +
            this.getSummary()
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            yes_no_options = taskcommon.OPTIONS_YES_NO_BOOLEAN,
            q12options = [],
            pages,
            questionnaire,
            i;

        function maketitle(n) {
            return L("gmcpq_titleprefix") + n;
        }

        for (i = 1; i <= N_ETHNICITY_OPTIONS; ++i) {
            q12options.push(new KeyValuePair(L("gmcpq_ethnicity_option" + i),
                                             i));
        }

        pages = [
            {
                title: maketitle(1),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('gmcpq_info1')
                    },
                    {
                        type: "QuestionText",
                        text: L('gmcpq_please_enter_doctor'),
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: true,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "doctor",
                                prompt: L("gmcpq_q_doctor")
                            },
                        ],
                    },
                    {
                        type: "QuestionText",
                        text: L('gmcpq_info2'),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: L('gmcpq_q1')
                    },
                    {
                        type: "QuestionMCQ",
                        field: "q1",
                        options: [
                            new KeyValuePair(L("gmcpq_q1_option1"), 1),
                            new KeyValuePair(L("gmcpq_q1_option2"), 2),
                            new KeyValuePair(L("gmcpq_q1_option3"), 3),
                            new KeyValuePair(L("gmcpq_q1_option4"), 4),
                        ],
                    },
                    {
                        type: "QuestionText",
                        text: L('gmcpq_info3'),
                        bold: true
                    },
                ],
            },
            {
                pageTag: PT_REASON,
                title: maketitle(2),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('gmcpq_q2')
                    },
                    {
                        type: "QuestionMultipleResponse",
                        min_answers: 1,
                        max_answers: 6,
                        options: [
                            L("gmcpq_q2_a"),
                            L("gmcpq_q2_b"),
                            L("gmcpq_q2_c"),
                            L("gmcpq_q2_d"),
                            L("gmcpq_q2_e"),
                            L("gmcpq_q2_f"),
                        ],
                        fields: [
                            "q2a",
                            "q2b",
                            "q2c",
                            "q2d",
                            "q2e",
                            "q2f",
                        ],
                    },
                    {
                        elementTag: ET_REASON_OTHER,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "q2f_details",
                                prompt: L("gmcpq_q2f_s")
                            },
                        ],
                    },
                ],
            },
            {
                title: maketitle(3),
                elements: [
                    { type: "QuestionText", text: L('gmcpq_q3') },
                    {
                        type: "QuestionMCQ",
                        field: "q3",
                        options: [
                            new KeyValuePair(L("gmcpq_q3_option1"), 1),
                            new KeyValuePair(L("gmcpq_q3_option2"), 2),
                            new KeyValuePair(L("gmcpq_q3_option3"), 3),
                            new KeyValuePair(L("gmcpq_q3_option4"), 4),
                            new KeyValuePair(L("gmcpq_q3_option5"), 5),
                        ],
                    },
                ],
            },
            {
                title: maketitle(4),
                elements: [
                    { type: "QuestionText", text: L('gmcpq_q4') },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('gmcpq_q4_option1'), 1),
                            new KeyValuePair(L('gmcpq_q4_option2'), 2),
                            new KeyValuePair(L('gmcpq_q4_option3'), 3),
                            new KeyValuePair(L('gmcpq_q4_option4'), 4),
                            new KeyValuePair(L('gmcpq_q4_option5'), 5),
                            new KeyValuePair(L('gmcpq_q4_option0'), 0),
                        ],
                        questions: [
                            L('gmcpq_q4_a'),
                            L('gmcpq_q4_b'),
                            L('gmcpq_q4_c'),
                            L('gmcpq_q4_d'),
                            L('gmcpq_q4_e'),
                            L('gmcpq_q4_f'),
                            L('gmcpq_q4_g'),
                        ],
                        fields: [
                            'q4a', 'q4b', 'q4c', 'q4d', 'q4e', 'q4f', 'q4g'
                        ],
                    },
                ],
            },
            {
                title: maketitle(5),
                elements: [
                    { type: "QuestionText", text: L('gmcpq_q5') },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('gmcpq_q5_option1'), 1),
                            new KeyValuePair(L('gmcpq_q5_option2'), 2),
                            new KeyValuePair(L('gmcpq_q5_option3'), 3),
                            new KeyValuePair(L('gmcpq_q5_option4'), 4),
                            new KeyValuePair(L('gmcpq_q5_option5'), 5),
                            new KeyValuePair(L('gmcpq_q5_option0'), 0),
                        ],
                        questions: [
                            L('gmcpq_q5_a'),
                            L('gmcpq_q5_b'),
                        ],
                        fields: [ 'q5a', 'q5b' ],
                    },
                ],
            },
            {
                title: maketitle(6),
                elements: [
                    { type: "QuestionText", text: L('gmcpq_q6') },
                    {
                        type: "QuestionMCQ",
                        field: "q6",
                        options: yes_no_options,
                    },
                ],
            },
            {
                title: maketitle(7),
                elements: [
                    { type: "QuestionText", text: L('gmcpq_q7') },
                    {
                        type: "QuestionMCQ",
                        field: "q7",
                        options: yes_no_options,
                    },
                ],
            },
            {
                title: maketitle(8),
                elements: [
                    { type: "QuestionText", text: L('gmcpq_q8') },
                    {
                        type: "QuestionMCQ",
                        field: "q8",
                        options: yes_no_options,
                    },
                ],
            },
            {
                title: maketitle(9), // comments
                elements: [
                    { type: "QuestionText", text: L('gmcpq_q9') },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "q9",
                                prompt: L("gmcpq_q9_s")
                            },
                        ],
                    },
                ],
            },
            {
                title: maketitle(10),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('gmcpq_info4'),
                        bold: true
                    },
                    { type: "QuestionText", text: L('gmcpq_q10') },
                    {
                        type: "QuestionMCQ",
                        field: "q10",
                        options: [
                            new KeyValuePair(L("male"), "M"),
                            new KeyValuePair(L("female"), "F"),
                        ],
                    },
                ],
            },
            {
                title: maketitle(11),
                elements: [
                    { type: "QuestionText", text: L('gmcpq_q11') },
                    {
                        type: "QuestionMCQ",
                        field: "q11",
                        options: [
                            new KeyValuePair(L("gmcpq_q11_option1"), 1),
                            new KeyValuePair(L("gmcpq_q11_option2"), 2),
                            new KeyValuePair(L("gmcpq_q11_option3"), 3),
                            new KeyValuePair(L("gmcpq_q11_option4"), 4),
                            new KeyValuePair(L("gmcpq_q11_option5"), 5),
                        ],
                    },
                ],
            },
            {
                pageTag: PT_ETHNICITY,
                title: maketitle(12),
                elements: [
                    { type: "QuestionText", text: L('gmcpq_q12') },
                    {
                        type: "QuestionMCQ",
                        field: "q12",
                        options: q12options,
                    },
                    {
                        elementTag: ET_ETHNICITY_OTHER,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "q12_details",
                                prompt: L("gmcpq_ethnicity_other_s")
                            },
                        ],
                    },
                ],
            },
            {
                title: L("finished"),
                elements: [
                    { type: "QuestionText", text: L('thank_you') },
                ],
            },
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: function (result, editing_time_s) {
                self.defaultFinishedFn(result, editing_time_s);
                questionnaire = null;
                // for garbage collection, since we have closures referring to
                // questionnaire
            },
            fnShowNext: function (currentPage, pageTag) {
                switch (pageTag) {
                case PT_ETHNICITY:
                    questionnaire.setMandatoryByTag(
                        ET_ETHNICITY_OTHER,
                        (self.q12 === 3 || self.q12 === 7 ||
                         self.q12 === 11 || self.q12 === 14 ||
                         self.q12 === 16)
                    );
                    break;
                case PT_REASON:
                    questionnaire.setMandatoryByTag(ET_REASON_OTHER,
                                                    self.q2f);
                    break;
                }
                return { care: false };
            },
        });
        questionnaire.open();
    },

});

module.exports = GmcPq;
