// CbiR.js

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
/*global L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "cbir",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 45;

fieldlist.push.apply(fieldlist, dbcommon.RESPONDENT_FIELDSPECS);
fieldlist.push(
    {name: 'confirm_blanks', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'comments', type: DBCONSTANTS.TYPE_TEXT}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "frequency", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "distress", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function CbiR(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(CbiR, taskcommon.BaseTask);
lang.extendPrototype(CbiR, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: CbiR,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    isCompleteQuestions: function () {
        return taskcommon.isCompleteByPrefix(this, "frequency", 1, nquestions) &&
            taskcommon.isCompleteByPrefix(this, "distress", 1, nquestions);
    },

    // Standard task functions
    isComplete: function () {
        return this.isRespondentComplete() && this.isCompleteQuestions();
    },

    getSummary: function () {
        return (this.respondent_relationship || "") + this.isCompleteSuffix();
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            elements1,
            elements2,
            elements3,
            pages,
            questionnaire,
            freq_options = [
                new KeyValuePair(this.XSTRING('f0'), 0),
                new KeyValuePair(this.XSTRING('f1'), 1),
                new KeyValuePair(this.XSTRING('f2'), 2),
                new KeyValuePair(this.XSTRING('f3'), 3),
                new KeyValuePair(this.XSTRING('f4'), 4)
            ],
            distress_options = [
                new KeyValuePair(this.XSTRING('d0'), 0),
                new KeyValuePair(this.XSTRING('d1'), 1),
                new KeyValuePair(this.XSTRING('d2'), 2),
                new KeyValuePair(this.XSTRING('d3'), 3),
                new KeyValuePair(this.XSTRING('d4'), 4)
            ],
            ET_MAIN = "m",
            ET_BLANKS = "b";

        function makeBlock(heading, first, last) {
            return [
                {
                    type: "QuestionText",
                    bold: true,
                    text: heading
                },
                {
                    elementTag: ET_MAIN,
                    type: "QuestionMCQGridDouble",
                    questions: taskcommon.localizedStringArrayFromSequence(
                        "cbir_q",
                        first,
                        last
                    ),
                    stem_1: self.XSTRING('stem_frequency'),
                    options_1: freq_options,
                    fields_1: taskcommon.stringArrayFromSequence(
                        "frequency",
                        first,
                        last
                    ),
                    stem_2: self.XSTRING('stem_distress'),
                    options_2: distress_options,
                    fields_2: taskcommon.stringArrayFromSequence(
                        "distress",
                        first,
                        last
                    ),
                    mandatory: true
                }
            ];
        }

        elements1 = [
            {
                type: "QuestionText",
                text: this.XSTRING('for_carer'),
                italic: true
            },
            this.getRespondentQuestionnaireBlock(true)
        ];

        elements2 = [
            {
                type: "QuestionText",
                text: this.XSTRING('instruction_1')
            },
            {
                type: "QuestionText",
                text: this.XSTRING('instruction_2')
            },
            {
                type: "QuestionText",
                text: this.XSTRING('instruction_3')
            }
        ];
        lang.appendArray(elements2, makeBlock(this.XSTRING('h_memory'), 1, 8));
        lang.appendArray(elements2, makeBlock(this.XSTRING('h_everyday'), 9, 13));
        lang.appendArray(elements2, makeBlock(this.XSTRING('h_selfcare'), 14, 17));
        lang.appendArray(elements2,
                         makeBlock(this.XSTRING('h_abnormalbehaviour'), 18, 23));
        lang.appendArray(elements2, makeBlock(this.XSTRING('h_mood'), 24, 27));
        lang.appendArray(elements2, makeBlock(this.XSTRING('h_beliefs'), 28, 30));
        lang.appendArray(elements2, makeBlock(this.XSTRING('h_eating'), 31, 34));
        lang.appendArray(elements2, makeBlock(this.XSTRING('h_sleep'), 35, 36));
        lang.appendArray(elements2,
                         makeBlock(this.XSTRING('h_stereotypy_motor'), 37, 40));
        lang.appendArray(elements2, makeBlock(this.XSTRING('h_motivation'), 41, 45));
        lang.appendArray(elements2, [
            {
                elementTag: ET_BLANKS,
                type: "QuestionText",
                bold: true,
                text: this.XSTRING('confirmblanks_q')
            },
            {
                elementTag: ET_BLANKS,
                type: "QuestionBooleanText",
                text: this.XSTRING('confirmblanks_a'),
                field: "confirm_blanks",
                mandatory: true
            }
        ]);

        elements3 = [
            {
                type: "QuestionTypedVariables",
                mandatory: false,
                useColumns: false,
                variables: [
                    {
                        type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                        field: "comments",
                        prompt: this.XSTRING('comments')
                    }
                ]
            },
            {
                type: "QuestionText",
                bold: true,
                text: this.XSTRING('thanks')
            }
        ];

        pages = [
            {
                title: L('t_cbir') + " (1/3)",
                clinician: false,
                elements: elements1
            },
            {
                title: L('t_cbir') + " (2/3)",
                clinician: false,
                elements: elements2
            },
            {
                title: L('t_cbir') + " (3/3)",
                clinician: false,
                elements: elements3
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
                if (currentPage !== 1) {
                    return { care: false };
                }
                // http://stackoverflow.com/questions/784929
                var blanks = !self.isCompleteQuestions(),
                    override = !!self.confirm_blanks;
                // Titanium.API.trace("blanks: " + blanks + ", override = " +
                //                    override);
                questionnaire.setMandatoryAndVisibleByTag(ET_BLANKS, blanks);
                questionnaire.setMandatoryByTag(ET_MAIN, !override);
                return { care: false };
            }
        });

        questionnaire.open();
    }

});

module.exports = CbiR;
