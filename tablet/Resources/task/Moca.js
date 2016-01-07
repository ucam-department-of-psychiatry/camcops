// Moca.js

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
    tablename = "moca",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 28,
    IMAGE_PATH = '/images/moca/path.png',
    IMAGE_CUBE = '/images/moca/cube.png',
    IMAGE_CLOCK = '/images/moca/clock.png',
    IMAGE_ANIMALS = '/images/moca/animals.png',
    CATEGORY_RECALL = "category_recall",
    MC_RECALL = "mc_recall";

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: 'education12y_or_less', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'trailpicture_blobid', type: DBCONSTANTS.TYPE_BLOBID},
    {name: 'cubepicture_blobid', type: DBCONSTANTS.TYPE_BLOBID},
    {name: 'clockpicture_blobid', type: DBCONSTANTS.TYPE_BLOBID}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "register_trial1_", 1, 5,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "register_trial2_", 1, 5,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "recall_category_cue_", 1, 5,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "recall_mc_cue_", 1, 5,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: 'comments', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Moca(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Moca, taskcommon.BaseTask);
lang.extendPrototype(Moca, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Moca,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _prohibitCommercial: true,
    _prohibitResearch: true,

    // OTHER

    // Scoring
    getTotalScore: function () {
        return (
            taskcommon.totalScore(this, "q", 1, nquestions) +
            this.education12y_or_less // extra point for this
        );
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + "/30" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var vsp = taskcommon.totalScore(this, "q", 1, 5),
            naming = taskcommon.totalScore(this, "q", 6, 8),
            attention = taskcommon.totalScore(this, "q", 9, 12),
            language = taskcommon.totalScore(this, "q", 13, 15),
            abstraction = taskcommon.totalScore(this, "q", 16, 17),
            memory = taskcommon.totalScore(this, "q", 18, 22),
            orientation = taskcommon.totalScore(this, "q", 23, 28),
            totalscore = this.getTotalScore(),
            category = totalscore >= 26 ? L('normal') : L('abnormal'),
            reg1 = "",
            reg2 = "",
            recallcat = "",
            recallmc = "",
            i;

        for (i = 1; i <= 5; ++i) {
            reg1 += (
                L("moca_registered") + " " + L("moca_memory_" + i) +
                " (" + L("moca_trial") + " 1): " +
                this["register_trial1_" + i] + "\n"
            );
            reg2 += (
                L("moca_registered") + " " + L("moca_memory_" + i) +
                " (" + L("moca_trial") + " 2): " +
                this["register_trial2_" + i] + "\n"
            );
            recallcat += (
                L("moca_recalled") + " " + L("moca_memory_" + i) +
                " " + L("moca_category_recall_suffix") + ": " +
                this["recall_category_cue_" + i] + "\n"
            );
            recallmc  += (
                L("moca_recalled") + " " + L("moca_memory_" + i) +
                " " + L("moca_mc_recall_suffix") + ": " +
                this["recall_mc_cue_" + i] + "\n"
            );
        }
        return (
            L("moca_education_s") + " " + this.education12y_or_less + "\n" +
            taskcommon.valueDetail(this, "moca_q", "_s", " ", "q", 1, 8) +
            reg1 +
            reg2 +
            taskcommon.valueDetail(this, "moca_q", "_s", " ", "q", 9, 22) +
            recallcat +
            recallmc +
            taskcommon.valueDetail(this, "moca_q", "_s", " ", "q", 23, nquestions) +
            "\n" +
            L("moca_subscore_visuospatial") + " " + vsp + "/5\n" +
            L("moca_subscore_naming") + " " + naming + "/3\n" +
            L("moca_subscore_attention") + " " + attention + "/6\n" +
            L("moca_subscore_language") + " " + language + "/3\n" +
            L("moca_subscore_abstraction") + " " + abstraction + "/2\n" +
            L("moca_subscore_memory") + " " + memory + "/5\n" +
            L("moca_subscore_orientation") + " " + orientation + "/6\n" +
            "\n" +
            L("moca_category") + " " + category + "\n" +
            "\n" +
            this.getSummary()
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
            options_corr_incorr = taskcommon.OPTIONS_INCORRECT_CORRECT_INTEGER,
            options_recalled = [
                new KeyValuePair(L('not_recalled'), 0),
                new KeyValuePair(L('recalled'), 1)
            ],
            options_yesno = taskcommon.OPTIONS_NO_YES_INTEGER,
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        pages = [
            {
                title: L('moca_title_preamble'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionText",
                        text: L('moca_education_instructions')
                    },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('moca_education_option0'), 0),
                            new KeyValuePair(L('moca_education_option1'), 1)
                        ],
                        field: "education12y_or_less"
                    }
                ]
            },
            {
                title: L('moca_title_prefix_singular') + " 1",
                disableScroll: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_trail_instructions')
                    },
                    {
                        type: "QuestionCanvas",
                        image: IMAGE_PATH,
                        field: "trailpicture_blobid"
                    }
                ]
            },
            {
                title: L('moca_title_prefix_singular') + " 2",
                disableScroll: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_cube_instructions')
                    },
                    {
                        type: "QuestionCanvas",
                        image: IMAGE_CUBE,
                        field: "cubepicture_blobid"
                    }
                ]
            },
            {
                title: L('moca_title_prefix_singular') + " 3–5",
                disableScroll: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_clock_instructions')
                    },
                    {
                        type: "QuestionCanvas",
                        image: IMAGE_CLOCK,
                        field: "clockpicture_blobid"
                    }
                ]
            },
            {
                title: L('moca_title_prefix_plural') + " 6–8",
                clinicianAssisted: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_naming_instructions')
                    },
                    {
                        type: "QuestionImage",
                        image: IMAGE_ANIMALS,
                        width: Titanium.UI.FILL
                    } // *** Image aspect ratio - somewhat hacky! This works because it's much wider than long.
                    // Better would be an "aspect fit" mode; I could write this for Android
                    // and an iOS one is at http://developer.appcelerator.com/question/23931/imageview-scaling-mode ;
                    // see also http://developer.appcelerator.com/question/121517/how-to-scale-image-proportionally
                ]
            },
            {
                title: (L('moca_title_prefix_plural') + " 1–8 " +
                        L('moca_scoring')),
                clinician: true,
                elements: [
                    { type: "QuestionImage", field: "trailpicture" },
                    { type: "QuestionImage", field: "cubepicture" },
                    { type: "QuestionImage", field: "clockpicture" },
                    {
                        type: "QuestionMCQGrid",
                        options: options_corr_incorr,
                        questions: [
                            L('moca_q1'),
                            L('moca_q2'),
                            L('moca_q3'),
                            L('moca_q4'),
                            L('moca_q5'),
                            L('moca_q6'),
                            L('moca_q7'),
                            L('moca_q8')
                        ],
                        fields: [
                            'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8'
                        ]
                    }
                ]
            },
            {
                title: (L('moca_title_prefix_plural') + " " +
                        L('moca_title_memorize')),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_memory_instruction1')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_yesno,
                        questions: [
                            L('moca_registered') + " " + L('moca_memory_1'),
                            L('moca_registered') + " " + L('moca_memory_2'),
                            L('moca_registered') + " " + L('moca_memory_3'),
                            L('moca_registered') + " " + L('moca_memory_4'),
                            L('moca_registered') + " " + L('moca_memory_5')
                        ],
                        fields: [
                            "register_trial1_1",
                            "register_trial1_2",
                            "register_trial1_3",
                            "register_trial1_4",
                            "register_trial1_5"
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: L('moca_memory_instruction2')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_yesno,
                        questions: [
                            L('moca_registered') + " " + L('moca_memory_1'),
                            L('moca_registered') + " " + L('moca_memory_2'),
                            L('moca_registered') + " " + L('moca_memory_3'),
                            L('moca_registered') + " " + L('moca_memory_4'),
                            L('moca_registered') + " " + L('moca_memory_5')
                        ],
                        fields: [
                            "register_trial2_1",
                            "register_trial2_2",
                            "register_trial2_3",
                            "register_trial2_4",
                            "register_trial2_5"
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: L('moca_memory_instruction3')
                    }
                ]
            },
            {
                title: L('moca_title_prefix_plural') + " 9–12",
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_digit_forward_instructions')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_corr_incorr,
                        questions: [
                            L('moca_q9')
                        ],
                        fields: [ 'q9' ]
                    },
                    {
                        type: "QuestionText",
                        text: L('moca_digit_backward_instructions')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_corr_incorr,
                        questions: [
                            L('moca_q10')
                        ],
                        fields: [ 'q10' ]
                    },
                    {
                        type: "QuestionText",
                        text: L('moca_tapping_instructions')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_corr_incorr,
                        questions: [ L('moca_q11') ],
                        fields: [ 'q11' ]
                    },
                    { type: "QuestionText", text: L('moca_q12') },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair(L('moca_q12_option0'), 0),
                            new KeyValuePair(L('moca_q12_option1'), 1),
                            new KeyValuePair(L('moca_q12_option2'), 2),
                            new KeyValuePair(L('moca_q12_option3'), 3)
                        ],
                        field: "q12"
                    }
                ]
            },
            {
                title: L('moca_title_prefix_plural') + " 13–15",
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_repetition_instructions_1')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_corr_incorr,
                        questions: [
                            L('moca_q13')
                        ],
                        fields: [ 'q13' ]
                    },
                    {
                        type: "QuestionText",
                        text: L('moca_repetition_instructions_2')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_corr_incorr,
                        questions: [
                            L('moca_q14')
                        ],
                        fields: [ 'q14' ]
                    },
                    {
                        type: "QuestionText",
                        text: L('moca_fluency_instructions')
                    },
                    { type: "QuestionCountdown", seconds: 60 },
                    {
                        type: "QuestionMCQGrid",
                        options: options_yesno,
                        questions: [
                            L('moca_q15')
                        ],
                        fields: [ "q15" ]
                    }
                ]
            },
            {
                title: L('moca_title_prefix_plural') + " 16–17",
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_abstraction_instructions')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_corr_incorr,
                        questions: [
                            L('moca_q16'),
                            L('moca_q17')
                        ],
                        fields: [ 'q16', 'q17' ]
                    }
                ]
            },
            {
                title: L('moca_title_prefix_plural') + " 18–22",
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_recall_instructions')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_recalled,
                        questions: [
                            L('moca_recalled') + " " + L('moca_memory_1'),
                            L('moca_recalled') + " " + L('moca_memory_2'),
                            L('moca_recalled') + " " + L('moca_memory_3'),
                            L('moca_recalled') + " " + L('moca_memory_4'),
                            L('moca_recalled') + " " + L('moca_memory_5')
                        ],
                        fields: [ 'q18', 'q19', 'q20', 'q21', 'q22' ]
                    }
                ]
            },
            {
                onTheFly: true,
                pageTag: CATEGORY_RECALL
            },
            {
                onTheFly: true,
                pageTag: MC_RECALL
            },
            {
                title: L('moca_title_prefix_plural') + " 23–28",
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L('moca_orientation_instructions')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: options_corr_incorr,
                        questions: [
                            L('moca_q23'),
                            L('moca_q24'),
                            L('moca_q25'),
                            L('moca_q26'),
                            L('moca_q27'),
                            L('moca_q28')
                        ],
                        fields: [ 'q23', 'q24', 'q25', 'q26', 'q27', 'q28' ]
                    },
                    {
                        type: "QuestionText",
                        text: L("moca_date_now_is"),
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
            fnFinished: self.defaultFinishedFn,
            fnShowNext: function (currentPage, pageTag) {
                if (pageTag === CATEGORY_RECALL || pageTag === MC_RECALL) {
                    // the optional cued recall pages
                    return {
                        care: true,
                        showNext: true
                    };
                }
                return {
                    care: false
                };
            },
            fnMakePageOnTheFly: function (currentPage, pageTag) {
                var questions = [],
                    fields = [],
                    ntotal = 0,
                    i;
                if (pageTag === CATEGORY_RECALL) {
                    for (i = 1; i <= 5; ++i) {
                        if (self["q" + (17 + i)] === 0) {
                            questions.push(L("moca_category_recall_" + i));
                            fields.push("recall_category_cue_" + i);
                            ++ntotal;
                        }
                    }
                    if (ntotal === 0) {
                        return {
                            pageTag: CATEGORY_RECALL,
                            title: (L('moca_title_prefix_plural') + " 18–22 " +
                                    L('moca_category_recall_suffix')),
                            clinician: true,
                            elements: [
                                {
                                    type: "QuestionText",
                                    text: L('moca_no_need_for_extra_recall')
                                }
                            ]
                        };
                    }
                    return {
                        pageTag: CATEGORY_RECALL,
                        title: (L('moca_title_prefix_plural') + " 18–22 " +
                                L('moca_category_recall_suffix')),
                        clinician: true,
                        elements: [
                            {
                                type: "QuestionText",
                                text: L('moca_category_recall_instructions')
                            },
                            {
                                type: "QuestionMCQGrid",
                                options: options_recalled,
                                questions: questions,
                                fields: fields
                            }
                        ]
                    };
                }
                if (pageTag === MC_RECALL) {
                    for (i = 1; i <= 5; ++i) {
                        if (self["q" + (17 + i)] === 0 &&
                                self["recall_category_cue_" + i] === 0) {
                            questions.push(L("moca_mc_recall_" + i));
                            fields.push("recall_mc_cue_" + i);
                            ++ntotal;
                        }
                    }
                    if (ntotal === 0) {
                        return {
                            pageTag: MC_RECALL,
                            title: (L('moca_title_prefix_plural') + " 18–22 " +
                                    L('moca_mc_recall_suffix')),
                            clinician: true,
                            elements: [
                                {
                                    type: "QuestionText",
                                    text: L('moca_no_need_for_extra_recall')
                                }
                            ]
                        };
                    }
                    return {
                        pageTag: MC_RECALL,
                        title: (L('moca_title_prefix_plural') + " 18–22 " +
                                L('moca_mc_recall_suffix')),
                        clinician: true,
                        elements: [
                            {
                                type: "QuestionText",
                                text: L('moca_mc_recall_instructions')
                            },
                            {
                                type: "QuestionMCQGrid",
                                options: options_recalled,
                                questions: questions,
                                fields: fields
                            }
                        ]
                    };
                }
                throw new Error("Moca/fnMakePageOnTheFly: called for " +
                                "invalid page");
            }
        });
        questionnaire.open();
    }

});

module.exports = Moca;
