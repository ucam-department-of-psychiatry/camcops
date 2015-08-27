// MdsUpdrs.js

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
    // TABLE
    tablename = "mds_updrs",
    fieldlist = dbcommon.standardTaskFields(),
    extrafields = [
        // Part I
        {name: "q1a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_1", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_2", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_3", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_4", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_5", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_6", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_6a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_7", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_8", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_9", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_10", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_11", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_12", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q1_13", type: DBCONSTANTS.TYPE_INTEGER},
        // Part II
        {name: "q2_1", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_2", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_3", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_4", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_5", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_6", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_7", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_8", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_9", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_10", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_11", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_12", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q2_13", type: DBCONSTANTS.TYPE_INTEGER},
        // Part III
        {name: "q3a", type: DBCONSTANTS.TYPE_BOOLEAN},  // yes/no
        {name: "q3b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3c", type: DBCONSTANTS.TYPE_BOOLEAN},  // yes/no
        {name: "q3c1", type: DBCONSTANTS.TYPE_REAL},  // minutes
        {name: "q3_1", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_2", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_3a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_3b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_3c", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_3d", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_3e", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_4a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_4b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_5a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_5b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_6a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_6b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_7a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_7b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_8a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_8b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_9", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_10", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_11", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_12", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_13", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_14", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_15a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_15b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_16a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_16b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_17a", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_17b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_17c", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_17d", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_17e", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_18", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q3_dyskinesia_present", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "q3_dyskinesia_interfered", type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: "q3_hy_stage", type: DBCONSTANTS.TYPE_INTEGER},
        // Part IV
        {name: "q4_1", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q4_2", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q4_3", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q4_4", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q4_5", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q4_6", type: DBCONSTANTS.TYPE_INTEGER}
    ],
    PAGETAG_3 = "p3",
    ELEMENTTAG_3C1 = "q3c1";

fieldlist.push.apply(fieldlist, extrafields); // append extrafields to fieldlist

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function MdsUpdrs(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(MdsUpdrs, taskcommon.BaseTask);
lang.extendPrototype(MdsUpdrs, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: MdsUpdrs,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _crippled: true,

    // OTHER

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByFieldlistArray(this, extrafields);
    },

    getSummary: function () {
        return L('no_summary_see_facsimile') + this.isCompleteSuffix();
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            roman = require('lib/roman'),
            main_options = [
                new KeyValuePair(L("mds_updrs_a0"), 0),
                new KeyValuePair(L("mds_updrs_a1"), 1),
                new KeyValuePair(L("mds_updrs_a2"), 2),
                new KeyValuePair(L("mds_updrs_a3"), 3),
                new KeyValuePair(L("mds_updrs_a4"), 4)
            ],
            source_options = [
                new KeyValuePair(L("mds_updrs_respondent_pt"), 0),
                new KeyValuePair(L("mds_updrs_respondent_cg"), 1),
                new KeyValuePair(L("mds_updrs_respondent_both"), 2)
            ],
            on_off_options = [
                new KeyValuePair(L("off"), 0),
                new KeyValuePair(L("on"), 1)
            ],
            hy_options = [
                new KeyValuePair("0", 0),
                new KeyValuePair("1", 1),
                new KeyValuePair("2", 2),
                new KeyValuePair("3", 3),
                new KeyValuePair("4", 4),
                new KeyValuePair("5", 5)
            ],
            elements_i,
            elements_ii,
            elements_iii,
            elements_iv,
            pages,
            questionnaire,
            i,
            part3bits = [
                "1", "2", "3a", "3b", "3c", "3d", "3e",
                "4a", "4b", "5a", "5b", "6a", "6b", "7a", "7b", "8a", "8b",
                "9", "10", "11", "12", "13", "14",
                "15a", "15b", "16a", "16b",
                "17a", "17b", "17c", "17d", "17e",
                "18"
            ],
            part3q = [],
            part3f = [];

        function pagetitle(partnum) {
            return (
                L("t_mds_updrs") + " " + L("part") + ": " +
                    roman.romanize(partnum)
            );
        }

        elements_i = [
            {
                type: "QuestionText",
                text: "Part I, Q1a (information source for 1.1–1.6"
            },
            {
                type: "QuestionMCQ",
                options: source_options,
                field: "q1a",
                showInstruction: false,
                horizontal: true
            },
            {
                type: "QuestionMCQGrid",
                options: main_options,
                questions: taskcommon.stringArrayFromSequence("Part I, Q1.",
                                                              1, 6),
                fields: taskcommon.stringArrayFromSequence("q1_", 1, 6)
            },
            {
                type: "QuestionText",
                text: "Part I, Q1.6a (information source for 1.7–1.13"
            },
            {
                type: "QuestionMCQ",
                options: source_options,
                field: "q1_6a",
                showInstruction: false,
                horizontal: true
            },
            {
                type: "QuestionMCQGrid",
                options: main_options,
                questions: taskcommon.stringArrayFromSequence("Part I, Q1.",
                                                              7, 13),
                fields: taskcommon.stringArrayFromSequence("q1_", 7, 13)
            }
        ];

        elements_ii = [
            {
                type: "QuestionMCQGrid",
                options: main_options,
                questions: taskcommon.stringArrayFromSequence("Part II, Q2.",
                                                              1, 13),
                fields: taskcommon.stringArrayFromSequence("q2_", 1, 13)
            }
        ];

        for (i = 0; i < part3bits.length; ++i) {
            part3q.push("Part III, Q3." + part3bits[i]);
            part3f.push("q3_" + part3bits[i]);
        }
        elements_iii = [
            {
                type: "QuestionText",
                text: "Part III, Q3a (medication)"
            },
            {
                type: "QuestionMCQ",
                options: taskcommon.OPTIONS_NO_YES_BOOLEAN,
                field: "q3a",
                showInstruction: false,
                horizontal: true
            },
            {
                type: "QuestionText",
                text: "Part III, Q3b (clinical state)"
            },
            {
                type: "QuestionMCQ",
                options: on_off_options,
                field: "q3b",
                showInstruction: false,
                horizontal: true
            },
            {
                type: "QuestionText",
                text: "Part III, Q3c (levodopa)"
            },
            {
                type: "QuestionMCQ",
                options: taskcommon.OPTIONS_NO_YES_BOOLEAN,
                field: "q3c",
                showInstruction: false,
                horizontal: true
            },
            {
                elementTag: ELEMENTTAG_3C1,
                type: "QuestionTypedVariables",
                mandatory: false,
                useColumns: true,
                variables: [
                    {
                        type: UICONSTANTS.TYPEDVAR_REAL,
                        field: "q3c1",
                        prompt: "Q3c.1, minutes since last dose",
                        min: 0
                    }
                ]
            },
            {
                type: "QuestionMCQGrid",
                options: main_options,
                questions: part3q,
                fields: part3f
            },
            {
                type: "QuestionText",
                text: "q3_dyskinesia_present"
            },
            {
                type: "QuestionMCQ",
                options: taskcommon.OPTIONS_NO_YES_BOOLEAN,
                field: "q3_dyskinesia_present",
                showInstruction: false,
                horizontal: true
            },
            {
                type: "QuestionText",
                text: "q3_dyskinesia_interfered"
            },
            {
                type: "QuestionMCQ",
                options: taskcommon.OPTIONS_NO_YES_BOOLEAN,
                field: "q3_dyskinesia_interfered",
                showInstruction: false,
                horizontal: true
            },
            {
                type: "QuestionText",
                text: "Hoehn & Yahr stage"
            },
            {
                type: "QuestionMCQ",
                options: hy_options,
                field: "q3_hy_stage",
                showInstruction: false,
                horizontal: true
            }
        ];

        elements_iv = [
            {
                type: "QuestionMCQGrid",
                options: main_options,
                questions: taskcommon.stringArrayFromSequence("Part IV, Q4.",
                                                              1, 6),
                fields: taskcommon.stringArrayFromSequence("q4_", 1, 6)
            }
        ];

        pages = [
            {
                title: pagetitle(1),
                elements: elements_i
            },
            {
                title: pagetitle(2),
                elements: elements_ii
            },
            {
                title: pagetitle(3),
                pageTag: PAGETAG_3,
                elements: elements_iii
            },
            {
                title: pagetitle(4),
                elements: elements_iv
            }
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn,
            fnShowNext: function (currentPage, pageTag) {
                if (pageTag === PAGETAG_3) {
                    questionnaire.setMandatoryByTag(
                        ELEMENTTAG_3C1,
                        self.q3c
                    );
                }
                return { care: false };
            }
        });
        questionnaire.open();
    }
});

module.exports = MdsUpdrs;
