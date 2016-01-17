// Aims.js

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
    lang = require('lib/lang'),
    // TASK
    nscoredquestions = 10,
    // TABLE
    tablename = "aims",
    fieldlist = dbcommon.standardTaskFields(),
    ntotalquestions = 12;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, ntotalquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);


function Aims(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Aims, taskcommon.BaseTask);
lang.extendPrototype(Aims, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Aims,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 1, nscoredquestions);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByPrefix(this, "q", 1, ntotalquestions);
    },

    getSummary: function () {
        return (
            L('total_score') + " " + this.getTotalScore() + "/40" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return (
            taskcommon.valueDetail(this, "aims_q", "_s", " ", "q", 1, 10) +
            taskcommon.yesNoNullDetail(this, "aims_q", "_s", " ",
                                       "q", 11, 12) +
            "\n" + this.getSummary()
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire;
        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        pages = [
            {
                title: L('aims_intro_title'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionText",
                        text: L('aims_intro_info')
                    }
                ]
            },
            {
                title: L('aims_section1_title'),
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L('aims_section1_stem') },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('aims_main_option0'), 0),
                            new KeyValuePair(L('aims_main_option1'), 1),
                            new KeyValuePair(L('aims_main_option2'), 2),
                            new KeyValuePair(L('aims_main_option3'), 3),
                            new KeyValuePair(L('aims_main_option4'), 4)
                        ],
                        questions: [
                            L('aims_q1_question'),
                            L('aims_q2_question'),
                            L('aims_q3_question'),
                            L('aims_q4_question'),
                            L('aims_q5_question'),
                            L('aims_q6_question'),
                            L('aims_q7_question'),
                            L('aims_q8_question')
                        ],
                        fields: [
                            'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8'
                        ],
                        subtitles: [
                            {beforeIndex: 1 - 1, subtitle: L('aims_q1_subtitle') },
                            {beforeIndex: 5 - 1, subtitle: L('aims_q5_subtitle') },
                            {beforeIndex: 7 - 1, subtitle: L('aims_q7_subtitle') },
                            {beforeIndex: 8 - 1, subtitle: L('aims_q8_subtitle') }
                        ]
                    }
                ]
            },
            {
                title: L('aims_section2_title'),
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L('aims_q9_question') },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('aims_q9_option0'), 0), // different one
                            new KeyValuePair(L('aims_main_option1'), 1),
                            new KeyValuePair(L('aims_main_option2'), 2),
                            new KeyValuePair(L('aims_main_option3'), 3),
                            new KeyValuePair(L('aims_main_option4'), 4)
                        ],
                        field: "q9"
                    }
                ]
            },
            {
                title: L('aims_section3_title'),
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L('aims_q10_question') },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('aims_q10_option0'), 0),
                            new KeyValuePair(L('aims_q10_option1'), 1),
                            new KeyValuePair(L('aims_q10_option2'), 2),
                            new KeyValuePair(L('aims_q10_option3'), 3),
                            new KeyValuePair(L('aims_q10_option4'), 4)
                        ],
                        field: "q10"
                    }
                ]
            },
            {
                title: L('aims_section4_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionMCQGrid",
                        options: taskcommon.OPTIONS_NO_YES_INTEGER,
                        questions: [
                            L('aims_q11_question'),
                            L('aims_q12_question')
                        ],
                        fields: [ 'q11', 'q12' ]
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

module.exports = Aims;
