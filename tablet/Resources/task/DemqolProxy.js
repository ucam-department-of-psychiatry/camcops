// DemqolProxy.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, continue: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "demqolproxy",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 32,
    N_SCORED_QUESTIONS = 31,
    MISSING_VALUE = -99,
    MINIMUM_N_FOR_TOTAL_SCORE = 16,
    REVERSE_SCORE = [1, 4, 6, 8, 11, 32];  // questions scored backwards

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push.apply(fieldlist, dbcommon.RESPONDENT_FIELDSPECS);
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function DemqolProxy(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(DemqolProxy, taskcommon.BaseTask);
lang.extendPrototype(DemqolProxy, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: DemqolProxy,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        // Higher score, better HRQL (health-related quality of life)
        var q,
            x,
            n = 0,
            total = 0;
        for (q = 1; q <= N_SCORED_QUESTIONS; ++q) {
            x = this["q" + q];
            if (x === null || x === MISSING_VALUE) {
                continue;
            }
            if (REVERSE_SCORE.indexOf(q) !== -1) {
                x = 5 - x;
            }
            n += 1;
            total += x;
        }
        if (n < MINIMUM_N_FOR_TOTAL_SCORE) {
            return null;
        }
        if (n < N_SCORED_QUESTIONS) {
            // As per the authors' sample SPSS script
            // (spss-syntax-demqol-proxy.pdf), but in a more obvious
            // mathematical way:
            return N_SCORED_QUESTIONS * total / n;
        }
        return total;
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() +
                " (Q1–31, range 31–124)" + this.isCompleteSuffix());
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            p0,
            p1,
            p2,
            p3,
            p4,
            p5,
            pages,
            mainoptions = [
                new KeyValuePair(L('demqol_a1'), 1),
                new KeyValuePair(L('demqol_a2'), 2),
                new KeyValuePair(L('demqol_a3'), 3),
                new KeyValuePair(L('demqol_a4'), 4),
                new KeyValuePair(L('demqol_no_response'), MISSING_VALUE)
            ],
            qoloptions = [
                new KeyValuePair(L('demqol_q29_a1'), 1),
                new KeyValuePair(L('demqol_q29_a2'), 2),
                new KeyValuePair(L('demqol_q29_a3'), 3),
                new KeyValuePair(L('demqol_q29_a4'), 4),
                new KeyValuePair(L('demqol_no_response'), MISSING_VALUE)
            ],
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3
        p0 = self.getClinicianAndRespondentDetailsPage(); // Clinician info 3/3
        p1 = {
            title: L('b_demqolproxy') + " " + L('page') + " 1/5",
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction1'),
                    italic: true
                },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction2'),
                    bold: true
                },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction3'),
                    bold: true
                },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction4'),
                    italic: true
                },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction5'),
                    bold: true
                },
                { type: "QuestionText", text: L('demqol_a1'), bold: true },
                { type: "QuestionText", text: L('demqol_a2'), bold: true },
                { type: "QuestionText", text: L('demqol_a3'), bold: true },
                { type: "QuestionText", text: L('demqol_a4'), bold: true },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction6'),
                    italic: true
                },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction7'),
                    bold: true
                },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction8'),
                    italic: true
                },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction9'),
                    bold: true
                }
            ]
        };
        p2 = {
            title: L('b_demqolproxy') + " " + L('page') + " 2/5",
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction10'),
                    bold: true
                },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction11'),
                    bold: true
                },
                {
                    type: "QuestionMCQGrid",
                    options: mainoptions,
                    questions: taskcommon.localizedStringArrayFromSequence(
                        'demqolproxy_q',
                        1,
                        11
                    ),
                    fields: taskcommon.stringArrayFromSequence('q', 1, 11)
                }
            ]
        };
        p3 = {
            title: L('b_demqolproxy') + " " + L('page') + " 3/5",
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction12'),
                    bold: true
                },
                {
                    type: "QuestionMCQGrid",
                    options: mainoptions,
                    questions: taskcommon.localizedStringArrayFromSequence(
                        'demqolproxy_q',
                        12,
                        20
                    ),
                    fields: taskcommon.stringArrayFromSequence('q', 12, 20)
                }
            ]
        };
        p4 = {
            title: L('b_demqolproxy') + " " + L('page') + " 4/5",
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction13'),
                    bold: true
                },
                {
                    type: "QuestionMCQGrid",
                    options: mainoptions,
                    questions: taskcommon.localizedStringArrayFromSequence(
                        'demqolproxy_q',
                        21,
                        31
                    ),
                    fields: taskcommon.stringArrayFromSequence('q', 21, 31)
                }
            ]
        };
        p5 = {
            title: L('b_demqolproxy') + " " + L('page') + " 5/5",
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    text: L('demqolproxy_instruction14'),
                    bold: true
                },
                {
                    type: "QuestionText",
                    text: L('demqolproxy_q32'),
                    bold: true
                },
                {
                    type: "QuestionMCQ",
                    options: qoloptions,
                    field: "q32"
                }
            ]
        };
        pages = [p0, p1, p2, p3, p4, p5];

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

module.exports = DemqolProxy;
