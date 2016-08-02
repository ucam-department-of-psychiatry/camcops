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
/*global L */

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

    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

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
            this.xValueDetail("q", "_s", " ", "q", 1, 10) +
            this.xYesNoNullDetail("q", "_s", " ", "q", 11, 12) +
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
                title: this.XSTRING('intro_title'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionText",
                        text: this.XSTRING('intro_info')
                    }
                ]
            },
            {
                title: this.XSTRING('section1_title'),
                clinician: true,
                elements: [
                    { type: "QuestionText", text: this.XSTRING('section1_stem') },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(this.XSTRING('main_option0'), 0),
                            new KeyValuePair(this.XSTRING('main_option1'), 1),
                            new KeyValuePair(this.XSTRING('main_option2'), 2),
                            new KeyValuePair(this.XSTRING('main_option3'), 3),
                            new KeyValuePair(this.XSTRING('main_option4'), 4)
                        ],
                        questions: [
                            this.XSTRING('q1_question'),
                            this.XSTRING('q2_question'),
                            this.XSTRING('q3_question'),
                            this.XSTRING('q4_question'),
                            this.XSTRING('q5_question'),
                            this.XSTRING('q6_question'),
                            this.XSTRING('q7_question'),
                            this.XSTRING('q8_question')
                        ],
                        fields: [
                            'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8'
                        ],
                        subtitles: [
                            {beforeIndex: 1 - 1, subtitle: this.XSTRING('q1_subtitle') },
                            {beforeIndex: 5 - 1, subtitle: this.XSTRING('q5_subtitle') },
                            {beforeIndex: 7 - 1, subtitle: this.XSTRING('q7_subtitle') },
                            {beforeIndex: 8 - 1, subtitle: this.XSTRING('q8_subtitle') }
                        ]
                    }
                ]
            },
            {
                title: this.XSTRING('section2_title'),
                clinician: true,
                elements: [
                    { type: "QuestionText", text: this.XSTRING('q9_question') },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(this.XSTRING('q9_option0'), 0), // different one
                            new KeyValuePair(this.XSTRING('main_option1'), 1),
                            new KeyValuePair(this.XSTRING('main_option2'), 2),
                            new KeyValuePair(this.XSTRING('main_option3'), 3),
                            new KeyValuePair(this.XSTRING('main_option4'), 4)
                        ],
                        field: "q9"
                    }
                ]
            },
            {
                title: this.XSTRING('section3_title'),
                clinician: true,
                elements: [
                    { type: "QuestionText", text: this.XSTRING('q10_question') },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(this.XSTRING('q10_option0'), 0),
                            new KeyValuePair(this.XSTRING('q10_option1'), 1),
                            new KeyValuePair(this.XSTRING('q10_option2'), 2),
                            new KeyValuePair(this.XSTRING('q10_option3'), 3),
                            new KeyValuePair(this.XSTRING('q10_option4'), 4)
                        ],
                        field: "q10"
                    }
                ]
            },
            {
                title: this.XSTRING('section4_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionMCQGrid",
                        options: taskcommon.OPTIONS_NO_YES_INTEGER,
                        questions: [
                            this.XSTRING('q11_question'),
                            this.XSTRING('q12_question')
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
