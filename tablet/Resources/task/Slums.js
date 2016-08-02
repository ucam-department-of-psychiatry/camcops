// Slums.js

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
/* jshint -W100 */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "slums",
    fieldlist = dbcommon.standardTaskFields(),
    qlist = [
        'q1',
        'q2',
        'q3',
        'q5a',
        'q5b',
        'q6',
        'q7a',
        'q7b',
        'q7c',
        'q7d',
        'q7e',
        'q8b',
        'q8c',
        'q9a',
        'q9b',
        'q10a',
        'q10b',
        'q11a',
        'q11b',
        'q11c',
        'q11d'
    ],
    IMAGE_CIRCLE = '/images/slums/circle.png',
    IMAGE_SHAPES = '/images/slums/shapes.png';

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'alert', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'highschooleducation', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q1', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q2', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q3', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q5a', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q5b', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q6', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q7a', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q7b', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q7c', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q7d', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q7e', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q8b', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q8c', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q9a', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q9b', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q10a', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q10b', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q11a', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q11b', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q11c', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q11d', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'clockpicture_blobid', type: DBCONSTANTS.TYPE_BLOBID},
    {name: 'shapespicture_blobid', type: DBCONSTANTS.TYPE_BLOBID},
    {name: 'comments', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Slums(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Slums, taskcommon.BaseTask);
lang.extendPrototype(Slums, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Slums,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        var total = 0,
            i;
        for (i = 0; i < qlist.length; ++i) {
            total += this[qlist[i]];
        }
        return total;
    },

    // Standard task functions
    isComplete: function () {
        var i;
        if (this.alert === null || this.highschooleducation === null) {
            return false;
        }
        for (i = 0; i < qlist.length; ++i) {
            if (this[qlist[i]] === null) {
                return false;
            }
        }
        return true;
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + "/30" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            score = this.getTotalScore(),
            category = (this.highschooleducation ?
                    (score >= 27 ?
                            L("normal") :
                            (score >= 21 ?
                                    L("slums_category_mci") :
                                    L("slums_category_dementia"))) :
                    (score >= 25 ?
                            L("normal") :
                            (score >= 20 ?
                                    L("slums_category_mci") :
                                    L("slums_category_dementia")))
            ),
            msg = (
                L("slums_alert_s") + " " + uifunc.yesNoNull(this.alert) + "\n" +
                L("slums_highschool_s") + " " +
                uifunc.yesNoNull(this.highschooleducation) + "\n\n"
            ),
            i;
        for (i = 0; i < qlist.length; ++i) {
            msg += (
                L("slums_" + qlist[i] + "_s") + " " + this[qlist[i]] + "\n"
            );
        }
        return (
            msg + "\n" + this.getSummary() + "\n\n" +
            L("category") + " " + category
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            moment = require('lib/moment'),
            now = moment(),
            correct_date = "     " + now.format("dddd D MMMM YYYY"),
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        pages = [
            {
                title: L('slums_title_preamble'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionMCQGrid",
                        options: taskcommon.OPTIONS_NO_YES_INTEGER,
                        questions: [
                            L('slums_q_alert'),
                            L('slums_q_highschool')
                        ],
                        fields: [ 'alert', 'highschooleducation' ]
                    }
                ]
            },
            {
                title: L('slums_title_prefix_plural') + " 1–3",
                clinician: true,
                elements: [
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('incorrect'), 0),
                            new KeyValuePair(L('correct'), 1)
                        ],
                        questions: [
                            L('slums_q1'),
                            L('slums_q2'),
                            L('slums_q3')
                        ],
                        fields: [ 'q1', 'q2', 'q3' ]
                    },
                    {
                        type: "QuestionText",
                        text: L("slums_date_now_is"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: correct_date,
                        italic: true
                    }
                ]
            },
            {
                title: L('slums_title_prefix_singular') + " 4",
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L('slums_q4') }
                ]
            },
            {
                title: L('slums_title_prefix_singular') + " 5",
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L('slums_q5') },
                    {
                        type: "QuestionMCQGrid",
                        options: taskcommon.OPTIONS_INCORRECT_CORRECT_INTEGER,
                        questions: [ L('slums_q5a') ],
                        fields: [ 'q5a' ]
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('incorrect'), 0),
                            new KeyValuePair(L('correct'), 2) // NB different scoring
                        ],
                        questions: [ L('slums_q5b') ],
                        fields: [ 'q5b' ]
                    }
                ]
            },
            {
                title: L('slums_title_prefix_singular') + " 6",
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L('slums_q6') },
                    { type: "QuestionCountdown", seconds: 60 },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('slums_q6_option0'), 0),
                            new KeyValuePair(L('slums_q6_option1'), 1),
                            new KeyValuePair(L('slums_q6_option2'), 2),
                            new KeyValuePair(L('slums_q6_option3'), 3)
                        ],
                        field: "q6"
                    }
                ]
            },
            {
                title: L('slums_title_prefix_singular') + " 7",
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L('slums_q7') },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('not_recalled'), 0),
                            new KeyValuePair(L('recalled'), 1)
                        ],
                        questions: [
                            L('slums_q7a'),
                            L('slums_q7b'),
                            L('slums_q7c'),
                            L('slums_q7d'),
                            L('slums_q7e')
                        ],
                        fields: [ 'q7a', 'q7b', 'q7c', 'q7d', 'q7e' ]
                    }
                ]
            },
            {
                title: L('slums_title_prefix_singular') + " 8",
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L('slums_q8') },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('incorrect'), 0),
                            new KeyValuePair(L('correct'), 1)
                        ],
                        questions: [
                            L('slums_q8b'),
                            L('slums_q8c')
                        ],
                        fields: [ 'q8b', 'q8c' ]
                    }
                ]
            },
            {
                title: L('slums_title_prefix_singular') + " 9",
                disableScroll: true,
                elements: [
                    { type: "QuestionText", text: L('slums_q9') },
                    {
                        type: "QuestionCanvas",
                        image: IMAGE_CIRCLE,
                        field: "clockpicture_blobid"
                    }
                ]
            },
            {
                title: (L('slums_title_prefix_singular') + " 9 " +
                        L('slums_scoring')),
                clinician: true,
                elements: [
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('incorrect'), 0),
                            new KeyValuePair(L('correct'), 2) // NB different scoring
                        ],
                        questions: [
                            L('slums_q9a'),
                            L('slums_q9b')
                        ],
                        fields: [ 'q9a', 'q9b' ]
                    }
                ]
            },
            {
                title: L('slums_title_prefix_singular') + " 10",
                clinicianAssisted: true,
                disableScroll: true,
                elements: [
                    { type: "QuestionText", text: L('slums_q10_part1') },
                    { type: "QuestionText", text: L('slums_q10_part2') },
                    // ... ideally text would be below the canvas, but canvas
                    // size takes up rest of available space
                    {
                        type: "QuestionCanvas",
                        image: IMAGE_SHAPES,
                        field: "shapespicture_blobid"
                    }
                ]
            },
            {
                title: (L('slums_title_prefix_singular') + " 10 " +
                        L('slums_scoring')),
                clinician: true,
                elements: [
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('incorrect'), 0),
                            new KeyValuePair(L('correct'), 1)
                        ],
                        questions: [
                            L('slums_q10a'),
                            L('slums_q10b')
                        ],
                        fields: [ 'q10a', 'q10b' ]
                    }
                ]
            },
            {
                title: L('slums_title_prefix_singular') + " 11",
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L('slums_q11') },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('incorrect'), 0),
                            new KeyValuePair(L('correct'), 2)
                            // TWO points for each correct answer for this one
                        ],
                        questions: [
                            L('slums_q11a'),
                            L('slums_q11b'),
                            L('slums_q11c'),
                            L('slums_q11d')
                        ],
                        fields: [ 'q11a', 'q11b', 'q11c', 'q11d' ]
                    }
                ]
            },
            {
                title: L("examiners_comments"),
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
                                prompt: L("examiners_comments_prompt"),
                                hint: L("examiners_comments")
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

module.exports = Slums;
