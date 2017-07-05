// Ifs.js

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
/*global Titanium */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "ifs",
    IMAGE_SWM = '/images/ifs/swm.png',
    DIGIT_ELEMENT_PREFIX = "digit_element_",
    Q4_PAGETAG = "q4page",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: "q1", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q2", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q3", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q4_len2_1", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len2_2", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len3_1", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len3_2", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len4_1", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len4_2", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len5_1", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len5_2", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len6_1", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len6_2", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len7_1", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q4_len7_2", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "q5", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q6_seq1", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q6_seq2", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q6_seq3", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q6_seq4", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q7_proverb1", type: DBCONSTANTS.TYPE_REAL},  // can score 0.5
    {name: "q7_proverb2", type: DBCONSTANTS.TYPE_REAL},
    {name: "q7_proverb3", type: DBCONSTANTS.TYPE_REAL},
    {name: "q8_sentence1", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q8_sentence2", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "q8_sentence3", type: DBCONSTANTS.TYPE_INTEGER}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Ifs(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Ifs, taskcommon.BaseTask);
lang.extendPrototype(Ifs, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Ifs,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "ifs",
    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    getScore: function () {
        var total = 0,
            wm = 0,
            q1,
            q2,
            q3,
            q4,
            q5,
            q6,
            q7,
            q8,
            seqlen,
            val1,
            val2;
        q1 = this.q1 || 0;
        q2 = this.q2 || 0;
        q3 = this.q3 || 0;
        q4 = 0;
        for (seqlen = 2; seqlen <= 7; ++seqlen) {
            val1 = this["q4_len" + seqlen + "_1"];
            val2 = this["q4_len" + seqlen + "_2"];
            q4 += val1 || val2 ? 1 : 0;
            if (!val1 && !val2) {
                break;
            }
        }
        q5 = this.q5 || 0;
        q6 = (
            (this.q6_seq1 || 0) +
            (this.q6_seq2 || 0) +
            (this.q6_seq3 || 0) +
            (this.q6_seq4 || 0)
        );
        q7 = (
            (this.q7_proverb1 || 0) +
            (this.q7_proverb2 || 0) +
            (this.q7_proverb3 || 0)
        );
        q8 = (
            (this.q8_sentence1 || 0) +
            (this.q8_sentence2 || 0) +
            (this.q8_sentence3 || 0)
        );
        total = q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8;
        wm = q4 + q6;  // working memory index (though not verbal)
        return {total: total, wm: wm};
    },

    // Standard task functions
    isComplete: function () {
        var seqlen,
            val1,
            val2,
            simple_qs = [
                "q1", "q2", "q3", "q5",
                "q6_seq1", "q6_seq2", "q6_seq3", "q6_seq4",
                "q7_proverb1", "q7_proverb2", "q7_proverb3",
                "q8_sentence1", "q8_sentence2", "q8_sentence3"
            ];
        // Obligatory stuff
        if (!taskcommon.isComplete(this, simple_qs)) {
            return false;
        }
        // Q4 (digit span), where we can terminate early
        // The sequences come in pairs. The task terminates when the patient
        // gets both items wrong within the pair.
        for (seqlen = 2; seqlen <= 7; ++seqlen) {
            val1 = this["q4_len" + seqlen + "_1"];
            val2 = this["q4_len" + seqlen + "_2"];
            if (val1 === null || val2 === null) {
                return false;
            }
            if (!val1 && !val2) {
                return true;  // all done
            }
        }
        return true;
    },

    getSummary: function () {
        var score = this.getScore();
        return (
            "Total = " + score.total + "/30; " +
            "working memory index = " + score.wm + "/10" +
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
            pages,
            questionnaire,
            proverb_options,
            inhibition_options;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3
        proverb_options = [
            new KeyValuePair(this.XSTRING("q7_a_1"), 1),
            new KeyValuePair(this.XSTRING("q7_a_half"), 0.5),
            new KeyValuePair(this.XSTRING("q7_a_0"), 0)
        ];
        inhibition_options = [
            new KeyValuePair(this.XSTRING("q8_a2"), 2),
            new KeyValuePair(this.XSTRING("q8_a1"), 1),
            new KeyValuePair(this.XSTRING("q8_a0"), 0)
        ];

        pages = [
            this.getClinicianDetailsPage(), // Clinician info 3/3

            // ----------------------------------------------------------------
            // Q1
            // ----------------------------------------------------------------
            {
                title: this.XSTRING('q1_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q1_instruction_1")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q1_instruction_2")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q1_instruction_3")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q1_instruction_4")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q1_instruction_5")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q1",
                        options: [
                            new KeyValuePair(this.XSTRING("q1_a3"), 3),
                            new KeyValuePair(this.XSTRING("q1_a2"), 2),
                            new KeyValuePair(this.XSTRING("q1_a1"), 1),
                            new KeyValuePair(this.XSTRING("q1_a0"), 0)
                        ]
                    }
                ]
            },

            // ----------------------------------------------------------------
            // Q2
            // ----------------------------------------------------------------
            {
                title: this.XSTRING('q2_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q2_instruction_1")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q2_instruction_2")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q2_instruction_3")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q2_instruction_4")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q2_instruction_5")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q2",
                        options: [
                            new KeyValuePair(this.XSTRING("q2_a3"), 3),
                            new KeyValuePair(this.XSTRING("q2_a2"), 2),
                            new KeyValuePair(this.XSTRING("q2_a1"), 1),
                            new KeyValuePair(this.XSTRING("q2_a0"), 0)
                        ]
                    }
                ]
            },

            // ----------------------------------------------------------------
            // Q3
            // ----------------------------------------------------------------
            {
                title: this.XSTRING('q3_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q3_instruction_1")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q3_instruction_2")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q3_instruction_3")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q3_instruction_4")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q3_instruction_5")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q3",
                        options: [
                            new KeyValuePair(this.XSTRING("q3_a3"), 3),
                            new KeyValuePair(this.XSTRING("q3_a2"), 2),
                            new KeyValuePair(this.XSTRING("q3_a1"), 1),
                            new KeyValuePair(this.XSTRING("q3_a0"), 0)
                        ]
                    }
                ]
            },

            // ----------------------------------------------------------------
            // Q4
            // ----------------------------------------------------------------
            {
                onTheFly: true,
                pageTag: Q4_PAGETAG
            },

            // ----------------------------------------------------------------
            // Q5
            // ----------------------------------------------------------------
            {
                title: this.XSTRING('q5_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q5_instruction_1")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q5_instruction_2")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q5_instruction_3")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q5",
                        options: [
                            new KeyValuePair(this.XSTRING("q5_a2"), 2),
                            new KeyValuePair(this.XSTRING("q5_a1"), 1),
                            new KeyValuePair(this.XSTRING("q5_a0"), 0)
                        ]
                    }
                ]
            },

            // ----------------------------------------------------------------
            // Q6
            // ----------------------------------------------------------------
            {
                title: this.XSTRING('q6_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q6_instruction_1")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q6_instruction_2")
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("q6_seq1"),
                        field: "q6_seq1"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("q6_seq2"),
                        field: "q6_seq2"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("q6_seq3"),
                        field: "q6_seq3"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("q6_seq4"),
                        field: "q6_seq4"
                    },
                    {
                        // A simple QuestionImage expands beyond the right-
                        // hand edge. It would probably be worth fixing this.
                        // However, the simple quick fix is to put it inside
                        // a 1-column tabe, and then everything works fine.
                        type: "ContainerTable",
                        columns: 1,
                        elements: [
                            {
                                type: "QuestionImage",
                                image: IMAGE_SWM
                            }
                        ]
                    }
                ]
            },

            // ----------------------------------------------------------------
            // Q7
            // ----------------------------------------------------------------
            {
                title: this.XSTRING('q7_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q7_proverb1")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q7_proverb1",
                        options: proverb_options
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q7_proverb2")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q7_proverb2",
                        options: proverb_options
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q7_proverb3")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q7_proverb3",
                        options: proverb_options
                    }
                ]
            },

            // ----------------------------------------------------------------
            // Q8
            // ----------------------------------------------------------------
            {
                title: this.XSTRING('q8_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionHeading",
                        bold: true,
                        text: this.XSTRING("q8_instruction_1")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q8_instruction_2")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q8_instruction_3")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q8_instruction_4")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q8_instruction_5")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("q8_instruction_6")
                    },
                    {
                        type: "QuestionHeading",
                        bold: true,
                        text: this.XSTRING("q8_instruction_7")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q8_instruction_8")
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q8_instruction_9")
                    },
                    { type: "QuestionHorizontalRule" },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q8_sentence_1")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q8_sentence1",
                        options: inhibition_options
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q8_sentence_2")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q8_sentence2",
                        options: inhibition_options
                    },
                    {
                        type: "QuestionText",
                        bold: true,
                        text: this.XSTRING("q8_sentence_3")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: false,
                        showInstruction: false,
                        field: "q8_sentence3",
                        options: inhibition_options
                    }
                ]
            }
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            /* jshint unused:true */
            fnMakePageOnTheFly: function (pageId, pageTag) {
                if (pageTag !== Q4_PAGETAG) {
                    Titanium.API.error("fnMakePageOnTheFly: bad call");
                    return;
                }
                var elements = [
                        {
                            type: "QuestionText",
                            text: self.XSTRING("q4_instruction_1")
                        }
                    ],
                    seqlen,
                    pair,
                    required = true,
                    val1,
                    val2;
                for (seqlen = 2; seqlen <= 7; ++seqlen) {
                    for (pair = 1; pair <= 2; ++pair) {
                        elements.push({
                            elementTag: DIGIT_ELEMENT_PREFIX + seqlen,
                            type: "QuestionBooleanText",
                            mandatory: required,
                            visible: required,
                            text: self.XSTRING("q4_seq_len" + seqlen +
                                               "_" + pair),
                            field: "q4_len" + seqlen + "_" + pair
                        });
                    }
                    val1 = self["q4_len" + seqlen + "_1"];
                    val2 = self["q4_len" + seqlen + "_2"];
                    if (!val1 && !val2) {
                        // ... integers are returned for boolean fields;
                        // see BooleanWidget.toggle(). So don't use
                        // "=== false".
                        required = false;  // for subsequent items
                    }
                }
                return {
                    title: self.XSTRING('q4_title'),
                    clinician: true,
                    elements: elements
                };
            },
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: function (field, value) {
                var required,
                    seqlen,
                    tag,
                    val1,
                    val2;
                self.defaultSetFieldFn(field, value);
                if (lang.startsWith(field, "q4")) {
                    required = true;
                    for (seqlen = 2; seqlen <= 7; ++seqlen) {
                        tag = DIGIT_ELEMENT_PREFIX + seqlen;
                        questionnaire.setMandatoryByTag(tag, required);
                        questionnaire.setVisibleByTag(tag, required);
                        val1 = this["q4_len" + seqlen + "_1"];
                        val2 = this["q4_len" + seqlen + "_2"];
                        if (!val1 && !val2) {
                            // ... integers are returned for boolean fields;
                            // see BooleanWidget.toggle(). So don't use
                            // "=== false".
                            required = false;  // for subsequent items
                        }
                    }
                }
            },
            fnFinished: function (result, editing_time_s) {
                self.defaultFinishedFn(result, editing_time_s);
                questionnaire = null; // for garbage collection, since we have
                // closures referring to questionnaire
            }
        });
        questionnaire.open();
    }
});

module.exports = Ifs;
