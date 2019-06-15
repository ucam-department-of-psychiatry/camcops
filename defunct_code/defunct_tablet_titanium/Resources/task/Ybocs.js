// Ybocs.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true, continue:true */
"use strict";
/*global L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "ybocs",
    fieldlist = dbcommon.standardTaskFields(),
    extrafields = [
        {name: "q1b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "q6b", type: DBCONSTANTS.TYPE_INTEGER},
        {name: "target_obsession_1", type: DBCONSTANTS.TYPE_TEXT},
        {name: "target_obsession_2", type: DBCONSTANTS.TYPE_TEXT},
        {name: "target_obsession_3", type: DBCONSTANTS.TYPE_TEXT},
        {name: "target_compulsion_1", type: DBCONSTANTS.TYPE_TEXT},
        {name: "target_compulsion_2", type: DBCONSTANTS.TYPE_TEXT},
        {name: "target_compulsion_3", type: DBCONSTANTS.TYPE_TEXT},
        {name: "target_avoidance_1", type: DBCONSTANTS.TYPE_TEXT},
        {name: "target_avoidance_2", type: DBCONSTANTS.TYPE_TEXT},
        {name: "target_avoidance_3", type: DBCONSTANTS.TYPE_TEXT}
    ],
    QSEQUENCE = ['1', '1b', '2', '3', '4', '5', '6', '6b', '7', '8', '9', '10',
                 '11', '12', '13', '14', '15', '16', '17', '18', '19'],
    MAX_SCORES = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
                  4, 4, 4, 4, 4, 4, 6, 6, 3];

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push.apply(fieldlist, extrafields);
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, 19,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Ybocs(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Ybocs, taskcommon.BaseTask);
lang.extendPrototype(Ybocs, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Ybocs,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "ybocs",
    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    // Scoring
    getObsessionScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 1, 5);
    },

    getCompulsionScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 6, 10);
    },

    getTotalScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 1, 10);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByPrefix(this, "q", 1, 10);
    },

    getSummary: function () {
        return (
            "Total " + this.getTotalScore() + "/40; " +
            "obsession score " + this.getObsessionScore() + "/20; " +
            "compulsion score " + this.getCompulsionScore() + "/20 " +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    makeQuestionPage: function (q, max_score) {
        var KeyValuePair = require('lib/KeyValuePair'),
            options = [],
            elements,
            page,
            i;
        for (i = 0; i <= max_score; ++i) {
            options.push(new KeyValuePair(this.XSTRING('q' + q + '_a' + i),
                                          i));
        }
        elements = [
            {
                type: "QuestionText",
                bold: true,
                text: this.XSTRING('q' + q + '_question')
            },
            {
                type: "QuestionText",
                text: this.XSTRING('q' + q + '_explanation')
            },
            {
                type: "QuestionMCQ",
                options: options,
                field: 'q' + q,
                showInstruction: false,
                horizontal: false
            }
        ];
        page = {
            title: this.XSTRING('q' + q + '_title'),
            clinician: true,
            elements: elements
        };
        return page;
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            page1elements,
            pages,
            i,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        pages = [ self.getClinicianDetailsPage() ]; // Clinician info 3/3
        // Instruction page
        page1elements = [{
            type: "QuestionText",
            bold: true,
            text: this.XSTRING('instruction_1')
        }];
        for (i = 2; i <= 18; ++i) {
            page1elements.push({
                type: "QuestionText",
                text: this.XSTRING('instruction_' + i)
            });
        }
        pages.push({
            title: L('t_ybocs'),
            clinician: true,
            elements: page1elements
        });
        // Target symptom page
        pages.push({
            title: this.XSTRING('target_symptom_list_title'),
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    bold: true,
                    text: this.XSTRING('target_obsession_stem')
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "target_obsession_1",
                            prompt: this.XSTRING('target_obsession_stem') + " 1"
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "target_obsession_2",
                            prompt: this.XSTRING('target_obsession_stem') + " 2"
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "target_obsession_3",
                            prompt: this.XSTRING('target_obsession_stem') + " 3"
                        }
                    ]
                },
                {
                    type: "QuestionText",
                    bold: true,
                    text: this.XSTRING('target_compulsion_stem')
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "target_compulsion_1",
                            prompt: this.XSTRING('target_compulsion_stem') + " 1"
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "target_compulsion_2",
                            prompt: this.XSTRING('target_compulsion_stem') + " 2"
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "target_compulsion_3",
                            prompt: this.XSTRING('target_compulsion_stem') + " 3"
                        }
                    ]
                },
                {
                    type: "QuestionText",
                    bold: true,
                    text: this.XSTRING('target_avoidance_stem')
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    useColumns: true,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "target_avoidance_1",
                            prompt: this.XSTRING('target_avoidance_stem') + " 1"
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "target_avoidance_2",
                            prompt: this.XSTRING('target_avoidance_stem') + " 2"
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "target_avoidance_3",
                            prompt: this.XSTRING('target_avoidance_stem') + " 3"
                        }
                    ]
                }
            ]
        });
        // Question pages
        for (i = 0; i < QSEQUENCE.length; ++i) {
            pages.push(this.makeQuestionPage(QSEQUENCE[i], MAX_SCORES[i]));
        }
        // Last page
        pages.push({
            title: L('end_matter'),
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    text: this.XSTRING('closing_1')
                },
                {
                    type: "QuestionText",
                    text: this.XSTRING('closing_2')
                },
                {
                    type: "QuestionText",
                    text: this.XSTRING('closing_3')
                }
            ]
        });

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

module.exports = Ybocs;
