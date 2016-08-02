// Ace3.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, continue: true, unparam: true */
"use strict";
/*global L */
/* jshint -W100 */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // TASK
    IMAGE_SPOON = '/images/ace3/spoon.png',
    IMAGE_BOOK = '/images/ace3/book.png',
    IMAGE_KANGAROO = '/images/ace3/kangaroo.png',
    IMAGE_PENGUIN = '/images/ace3/penguin.png',
    IMAGE_ANCHOR = '/images/ace3/anchor.png',
    IMAGE_CAMEL = '/images/ace3/camel.png',
    IMAGE_HARP = '/images/ace3/harp.png',
    IMAGE_RHINOCEROS = '/images/ace3/rhinoceros.png',
    IMAGE_BARREL = '/images/ace3/barrel.png',
    IMAGE_CROWN = '/images/ace3/crown.png',
    IMAGE_CROCODILE = '/images/ace3/crocodile.png',
    IMAGE_ACCORDION = '/images/ace3/accordion.png',
    IMAGE_INFINITY = '/images/ace3/infinity.png',
    IMAGE_CUBE = '/images/ace3/cube.png',
    IMAGE_DOTS8 = '/images/ace3/dots8.png',
    IMAGE_DOTS10 = '/images/ace3/dots10.png',
    IMAGE_DOTS7 = '/images/ace3/dots7.png',
    IMAGE_DOTS9 = '/images/ace3/dots9.png',
    IMAGE_K = '/images/ace3/k.png',
    IMAGE_M = '/images/ace3/m.png',
    IMAGE_A = '/images/ace3/a.png',
    IMAGE_T = '/images/ace3/t.png',
    MEM_RECOGNIZE = "mem_recognize",
    LANG_COMMANDS_SENTENCES = "lang_commands_sentences",
    LANG_OPTIONAL_COMMAND = "lang_optional_command",
    // TABLE
    tablename = "ace3",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'age_at_leaving_full_time_education', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'occupation', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'handedness', type: DBCONSTANTS.TYPE_TEXT}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "attn_time", 1, 5,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "attn_place", 1, 5,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "attn_repeat_word", 1, 3,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: "attn_num_registration_trials", type: DBCONSTANTS.TYPE_INTEGER}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "attn_serial7_subtraction", 1, 5,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "mem_recall_word", 1, 3,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: "fluency_letters_score", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "fluency_animals_score", type: DBCONSTANTS.TYPE_INTEGER}
);
/*
fieldlist.push(
    {name:"fluency_letters_correct", type:DBCONSTANTS.TYPE_INTEGER},
    {name:"fluency_letters_incorrect", type:DBCONSTANTS.TYPE_INTEGER},
    {name:"fluency_animals_correct", type:DBCONSTANTS.TYPE_INTEGER},
    {name:"fluency_animals_incorrect", type:DBCONSTANTS.TYPE_INTEGER}
);
*/
dbcommon.appendRepeatedFieldDef(fieldlist, "mem_repeat_address_trial1_", 1, 7,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "mem_repeat_address_trial2_", 1, 7,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "mem_repeat_address_trial3_", 1, 7,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "mem_famous", 1, 4,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: "lang_follow_command_practice", type: DBCONSTANTS.TYPE_INTEGER}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "lang_follow_command", 1, 3,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "lang_write_sentences_point", 1, 2,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "lang_repeat_word", 1, 4,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "lang_repeat_sentence", 1, 2,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "lang_name_picture", 1, 12,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "lang_identify_concept", 1, 4,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: "lang_read_words_aloud", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "vsp_copy_infinity", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "vsp_copy_cube", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "vsp_draw_clock", type: DBCONSTANTS.TYPE_INTEGER}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "vsp_count_dots", 1, 4,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "vsp_identify_letter", 1, 4,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "mem_recall_address", 1, 7,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "mem_recognize_address", 1, 5,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: "picture1_blobid", type: DBCONSTANTS.TYPE_BLOBID},
    {name: "picture1_rotation", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "picture2_blobid", type: DBCONSTANTS.TYPE_BLOBID},
    {name: "picture2_rotation", type: DBCONSTANTS.TYPE_INTEGER},
    {name: "comments", type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

function Ace3(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Ace3, taskcommon.BaseTask);
lang.extendPrototype(Ace3, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Ace3,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _prohibitCommercial: true,

    // OTHER

    // Scoring (begin with 0 as 0 + null == 0, it seems)
    getAttnScore: function () {
        return (
            taskcommon.totalScoreByPrefix(this, "attn_time", 1, 5) +
            taskcommon.totalScoreByPrefix(this, "attn_place", 1, 5) +
            taskcommon.totalScoreByPrefix(this, "attn_repeat_word", 1, 3) +
            taskcommon.totalScoreByPrefix(this, "attn_serial7_subtraction", 1, 5)
        );
    },

    getMemRecognitionScore: function () {
        var score = 0;
        score += ((this.mem_recall_address1 && this.mem_recall_address2) ?
                1 :
                this.mem_recognize_address1
        ); // forename, surname
        score += (this.mem_recall_address3) ? 1 : this.mem_recognize_address2; // number
        score += ((this.mem_recall_address4 && this.mem_recall_address5) ?
                1 :
                this.mem_recognize_address3
        ); // streetname, streettype
        score += (this.mem_recall_address6) ? 1 : this.mem_recognize_address4; // city
        score += (this.mem_recall_address7) ? 1 : this.mem_recognize_address5; // county
        return score;
    },

    getMemScore: function () {
        return (
            taskcommon.totalScoreByPrefix(this, "mem_recall_word", 1, 3) +
            taskcommon.totalScoreByPrefix(this, "mem_repeat_address_trial3_", 1, 7) +
            taskcommon.totalScoreByPrefix(this, "mem_famous", 1, 4) +
            taskcommon.totalScoreByPrefix(this, "mem_recall_address", 1, 7) +
            this.getMemRecognitionScore() // 5 points
        );
    },

    getFluencyScore: function () {
        /*
        var l = this.fluency_letters_correct;
        var a = this.fluency_animals_correct;
        var score = (l >= 18 ? 7 :
                        (l >= 14 ? 6 :
                            (l >= 11 ? 5 :
                                (l >= 8 ? 4 :
                                    (l >= 6 ? 3 :
                                        (l >= 4 ? 2 :
                                            (l >= 2 ? 1 : 0) ) ) ) ) ) );
        score += (a >= 22 ? 7 :
                    (a >= 17 ? 6 :
                        (a >= 14 ? 5 :
                            (a >= 11 ? 4 :
                                (a >= 9 ? 3 :
                                    (a >= 7 ? 2 :
                                        (a >= 5 ? 1 : 0) ) ) ) ) ) );
        return score; // 2 * 7 points
        */
        return this.fluency_letters_score + this.fluency_animals_score;
    },

    getFollowCommandScore: function () {
        if (!this.lang_follow_command_practice) {
            return 0;
        }
        return taskcommon.totalScoreByPrefix(this, "lang_follow_command", 1, 3);
    },

    getRepeatWordScore: function () {
        var n = taskcommon.totalScoreByPrefix(this, "lang_repeat_word", 1, 4);
        return n >= 4 ? 2 : (n === 3 ? 1 : 0);
    },

    getLangScore: function () {
        return (
            this.getFollowCommandScore() + // 3 points
            taskcommon.totalScoreByPrefix(this, "lang_write_sentences_point", 1, 2) +
            this.getRepeatWordScore() + // 2 points
            taskcommon.totalScoreByPrefix(this, "lang_repeat_sentence", 1, 2) +
            taskcommon.totalScoreByPrefix(this, "lang_name_picture", 1, 12) +
            taskcommon.totalScoreByPrefix(this, "lang_identify_concept", 1, 4) +
            this.lang_read_words_aloud // 1 point
        );
    },

    getVisuospatialScore: function () {
        return (
            this.vsp_copy_infinity + // 1 point
            this.vsp_copy_cube + // 2 points
            this.vsp_draw_clock + // 5 points
            taskcommon.totalScoreByPrefix(this, "vsp_count_dots", 1, 4) +
            taskcommon.totalScoreByPrefix(this, "vsp_identify_letter", 1, 4)
        );
    },

    getTotalScore: function () {
        return (
            this.getAttnScore() +
            this.getMemScore() +
            this.getFluencyScore() +
            this.getLangScore() +
            this.getVisuospatialScore()
        );
    },

    isRecognitionComplete: function () {
        return (
            (
                // forename, surname
                (this.mem_recall_address1 && this.mem_recall_address2) ||
                this.mem_recognize_address1 !== null
            ) &&
            (this.mem_recall_address3 ||
                this.mem_recognize_address2 !== null) && // number
            (
                    // streetname, streettype
                    (this.mem_recall_address4 && this.mem_recall_address5) ||
                        this.mem_recognize_address3 !== null
                ) &&
            (this.mem_recall_address6 ||
                this.mem_recognize_address4 !== null) && // city
            (this.mem_recall_address7 ||
                this.mem_recognize_address5 !== null) // county
        );
    },

    // Standard task functions
    isComplete: function () {
        // In task order:
        return (
            taskcommon.isCompleteByPrefix(this, "attn_time", 1, 5) &&
            taskcommon.isCompleteByPrefix(this, "attn_place", 1, 5) &&
            taskcommon.isCompleteByPrefix(this, "attn_repeat_word", 1, 3) &&
            taskcommon.isCompleteByPrefix(this, "attn_serial7_subtraction", 1, 5) &&
            taskcommon.isCompleteByPrefix(this, "mem_recall_word", 1, 3) &&
            // this.fluency_letters_correct !== null &&
            // this.fluency_animals_correct !== null &&
            this.fluency_letters_score !== null &&
            this.fluency_animals_score !== null &&
            taskcommon.isCompleteByPrefix(this, "mem_repeat_address_trial3_", 1, 7) &&
            taskcommon.isCompleteByPrefix(this, "mem_famous", 1, 4) &&
            this.lang_follow_command_practice !== null &&
            (this.lang_follow_command_practice === 0 ||
                    taskcommon.isCompleteByPrefix(this, "lang_follow_command", 1, 3)) &&
            taskcommon.isCompleteByPrefix(this, "lang_write_sentences_point", 1, 2) &&
            taskcommon.isCompleteByPrefix(this, "lang_repeat_word", 1, 4) &&
            taskcommon.isCompleteByPrefix(this, "lang_repeat_sentence", 1, 2) &&
            taskcommon.isCompleteByPrefix(this, "lang_name_picture", 1, 12) &&
            taskcommon.isCompleteByPrefix(this, "lang_identify_concept", 1, 4) &&
            this.lang_read_words_aloud !== null &&
            this.vsp_copy_infinity !== null &&
            this.vsp_copy_cube !== null &&
            this.vsp_draw_clock !== null &&
            taskcommon.isCompleteByPrefix(this, "vsp_count_dots", 1, 4) &&
            taskcommon.isCompleteByPrefix(this, "vsp_identify_letter", 1, 4) &&
            taskcommon.isCompleteByPrefix(this, "mem_recall_address", 1, 7) &&
            this.isRecognitionComplete()
        );
    },

    getSummary: function () {
        var a = this.getAttnScore(),
            m = this.getMemScore(),
            f = this.getFluencyScore(),
            l = this.getLangScore(),
            v = this.getVisuospatialScore(),
            t = a + m + f + l + v;
        return (
            L('total_score') + " " + t + "/100. " +
            this.XSTRING('cat_attn') + " " + a + "/18 (" + Math.round(100 * a / 18) + "%). " +
            this.XSTRING('cat_mem') + " " + m + "/26 (" + Math.round(100 * m / 26) + "%). " +
            this.XSTRING('cat_fluency') + " " + f + "/14 (" + Math.round(100 * f / 14) + "%). " +
            this.XSTRING('cat_lang') + " " + l + "/26 (" + Math.round(100 * l / 26) + "%). " +
            this.XSTRING('cat_vsp') + " " + v + "/16 (" + Math.round(100 * v / 16) + "%)." +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        // Not terribly elegant!
        var s = "",
            started = false,
            i;
        for (i = 0; i < fieldlist.length; ++i) {
            if (fieldlist[i].name === "picture1_blobid" ||
                    fieldlist[i].name === "picture2_blobid") {
                continue;
            }
            if (fieldlist[i].name === "clinician_contact_details") {
                started = true;
            } else if (started) {
                s += fieldlist[i].name + ": " + this[fieldlist[i].name] + "\n";
            }
        }
        return s + "\n" + this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            moment = require('lib/moment'),
            now = moment(),
            season = "?",
            correct_date,
            pagenum = 1,
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3
        switch (now.month()) {
        case 11: // December
        case 0: // January
        case 1:
            season = this.XSTRING('season_winter');
            break;
        case 2:
        case 3:
        case 4:
            season = this.XSTRING('season_spring');
            break;
        case 5:
        case 6:
        case 7:
            season = this.XSTRING('season_summer');
            break;
        case 8:
        case 9:
        case 10:
            season = this.XSTRING('season_autumn');
            break;
        }
        correct_date = (
            "     " +
            now.format("dddd D MMMM YYYY") +
            "; " +
            season
        );

        pages = [
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                elements: [
                    // Preamble
                    {
                        type: "QuestionText",
                        text: this.XSTRING("instruction_need_paper"),
                        bold: true
                    },
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionText",
                        text: this.XSTRING("preamble_instruction")
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "age_at_leaving_full_time_education",
                                prompt: this.XSTRING("q_age_leaving_fte")
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "occupation",
                                prompt: this.XSTRING("q_occupation")
                            }
                        ]
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: false,
                        horizontal: true,
                        showInstruction: false,
                        field: "handedness",
                        options: [
                            new KeyValuePair(this.XSTRING("left_handed"), "L"),
                            new KeyValuePair(this.XSTRING("right_handed"), "R")
                        ]
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                elements: [
                    // Orientation
                    { type: "QuestionHeading", text: this.XSTRING("cat_attn") },
                    { type: "QuestionText", text: this.XSTRING("attn_q_time") },
                    {
                        type: "ContainerHorizontal",
                        elements: [
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_time1"),
                                field: "attn_time1"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_time2"),
                                field: "attn_time2"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_time3"),
                                field: "attn_time3"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_time4"),
                                field: "attn_time4"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_time5"),
                                field: "attn_time5"
                            }
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("instruction_time"),
                        italic: true
                    },
                    { type: "QuestionText", text: correct_date, italic: true },
                    { type: "QuestionText", text: this.XSTRING("attn_q_place") },
                    {
                        type: "ContainerHorizontal",
                        elements: [
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_place1"),
                                field: "attn_place1"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_place2"),
                                field: "attn_place2"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_place3"),
                                field: "attn_place3"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_place4"),
                                field: "attn_place4"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_place5"),
                                field: "attn_place5"
                            }
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("instruction_place"),
                        italic: true
                    },
                    // Lemon, key, ball (registration)
                    { type: "QuestionHeading", text: this.XSTRING("cat_attn") },
                    { type: "QuestionText", text: this.XSTRING("attn_q_words") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("attn_instruction_words"),
                        italic: true
                    },
                    {
                        type: "ContainerHorizontal",
                        elements: [
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("mem_word1"),
                                field: "attn_repeat_word1"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("mem_word2"),
                                field: "attn_repeat_word2"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("mem_word3"),
                                field: "attn_repeat_word3"
                            }
                        ]
                    },
                    {
                        type: "ContainerHorizontal",
                        elements: [
                            { type: "QuestionText", text: this.XSTRING("attn_q_register_n_trials") },
                            {
                                type: "QuestionMCQ",
                                mandatory: false,
                                horizontal: true,
                                showInstruction: false,
                                field: "attn_num_registration_trials",
                                options: [
                                    new KeyValuePair("1", 1),
                                    new KeyValuePair("2", 2),
                                    new KeyValuePair("3", 3),
                                    new KeyValuePair("4", 4),
                                    new KeyValuePair(">4", 0)
                                ]
                            }
                        ]
                    },
                    // Serial 7s
                    { type: "QuestionHeading", text: this.XSTRING("cat_attn") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("attn_q_serial_sevens")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("attn_instruction_sevens"),
                        italic: true
                    },
                    {
                        type: "ContainerHorizontal",
                        elements: [
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_subtraction1"),
                                field: "attn_serial7_subtraction1"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_subtraction2"),
                                field: "attn_serial7_subtraction2"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_subtraction3"),
                                field: "attn_serial7_subtraction3"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_subtraction4"),
                                field: "attn_serial7_subtraction4"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("attn_subtraction5"),
                                field: "attn_serial7_subtraction5"
                            }
                        ]
                    },
                    // Lemon, key, ball (recall)
                    { type: "QuestionHeading", text: this.XSTRING("cat_mem") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("mem_q_recall_words")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("mem_instruction_recall"),
                        italic: true
                    },
                    {
                        type: "ContainerHorizontal",
                        elements: [
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("mem_word1"),
                                field: "mem_recall_word1"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("mem_word2"),
                                field: "mem_recall_word2"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("mem_word3"),
                                field: "mem_recall_word3"
                            }
                        ]
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                elements: [
                    // Fluency
                    { type: "QuestionHeading", text: this.XSTRING("cat_fluency") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("fluency_subhead_letters"),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("fluency_q_letters")
                    },
                    {
                        type: "QuestionCountdown",
                        seconds: 60
                    },
                    /*
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "fluency_letters_correct",
                                prompt: this.XSTRING("fluency_prompt_letters_cor")
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "fluency_letters_incorrect",
                                prompt: this.XSTRING("fluency_prompt_inc")
                            },
                        ],
                    },
                    */
                    {
                        type: "QuestionText",
                        text: this.XSTRING("fluency_instruction_letters"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("fluency_prompt_letters_cor")
                    },
                    {
                        type: "QuestionMCQ",
                        showInstruction: false,
                        mandatory: true,
                        horizontal: true,
                        field: "fluency_letters_score",
                        options: [
                            new KeyValuePair("0–1", 0),
                            new KeyValuePair("2–3", 1),
                            new KeyValuePair("4–5", 2),
                            new KeyValuePair("6–7", 3),
                            new KeyValuePair("8–10", 4),
                            new KeyValuePair("11–13", 5),
                            new KeyValuePair("14–17", 6),
                            new KeyValuePair("≥18", 7)
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("fluency_subheading_animals"),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("fluency_q_animals")
                    },
                    {
                        type: "QuestionCountdown",
                        seconds: 60
                    },
                    /*
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "fluency_animals_correct",
                                prompt: this.XSTRING("fluency_prompt_animals_cor")
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "fluency_animals_incorrect",
                                prompt: this.XSTRING("fluency_prompt_inc")
                            },
                        ],
                    },
                    */
                    {
                        type: "QuestionText",
                        text: this.XSTRING("fluency_instruction_animals"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("fluency_prompt_animals_cor")
                    },
                    {
                        type: "QuestionMCQ",
                        showInstruction: false,
                        mandatory: true,
                        horizontal: true,
                        field: "fluency_animals_score",
                        options: [
                            new KeyValuePair("0–4", 0),
                            new KeyValuePair("5–6", 1),
                            new KeyValuePair("7–8", 2),
                            new KeyValuePair("9–10", 3),
                            new KeyValuePair("11–13", 4),
                            new KeyValuePair("14–16", 5),
                            new KeyValuePair("17–21", 6),
                            new KeyValuePair("≥22", 7)
                        ]
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                elements: [
                    // Learning the address
                    { type: "QuestionHeading", text: this.XSTRING("cat_mem") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("memory_q_address")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("memory_instruction_address_1"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("memory_instruction_address_2"),
                        italic: true
                    },
                    {
                        type: "ContainerTable",
                        elements: [
                            {
                                type: "ContainerVertical",
                                elements: [
                                    {
                                        type: "QuestionText",
                                        text: this.XSTRING("trial") + " 1"
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_1"),
                                                field: "mem_repeat_address_trial1_1",
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_2"),
                                                field: "mem_repeat_address_trial1_2",
                                                mandatory: false
                                            }
                                        ]
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_3"),
                                                field: "mem_repeat_address_trial1_3",
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_4"),
                                                field: "mem_repeat_address_trial1_4",
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_5"),
                                                field: "mem_repeat_address_trial1_5",
                                                mandatory: false
                                            }
                                        ]
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: this.XSTRING("address_6"),
                                        field: "mem_repeat_address_trial1_6",
                                        mandatory: false
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: this.XSTRING("address_7"),
                                        field: "mem_repeat_address_trial1_7",
                                        mandatory: false
                                    }
                                ]
                            },
                            {
                                type: "ContainerVertical",
                                elements: [
                                    {
                                        type: "QuestionText",
                                        text: this.XSTRING("trial") + " 2"
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_1"),
                                                field: "mem_repeat_address_trial2_1",
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_2"),
                                                field: "mem_repeat_address_trial2_2",
                                                mandatory: false
                                            }
                                        ]
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_3"),
                                                field: "mem_repeat_address_trial2_3",
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_4"),
                                                field: "mem_repeat_address_trial2_4",
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: this.XSTRING("address_5"),
                                                field: "mem_repeat_address_trial2_5",
                                                mandatory: false
                                            }
                                        ]
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: this.XSTRING("address_6"),
                                        field: "mem_repeat_address_trial2_6",
                                        mandatory: false
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: this.XSTRING("address_7"),
                                        field: "mem_repeat_address_trial2_7",
                                        mandatory: false
                                    }
                                ]
                            },
                            {
                                type: "ContainerVertical",
                                elements: [
                                    {
                                        type: "QuestionText",
                                        text: this.XSTRING("trial") + " 3"
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                mandatory: true,
                                                text: this.XSTRING("address_1"),
                                                field: "mem_repeat_address_trial3_1"
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                mandatory: true,
                                                text: this.XSTRING("address_2"),
                                                field: "mem_repeat_address_trial3_2"
                                            }
                                        ]
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                mandatory: true,
                                                text: this.XSTRING("address_3"),
                                                field: "mem_repeat_address_trial3_3"
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                mandatory: true,
                                                text: this.XSTRING("address_4"),
                                                field: "mem_repeat_address_trial3_4"
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                mandatory: true,
                                                text: this.XSTRING("address_5"),
                                                field: "mem_repeat_address_trial3_5"
                                            }
                                        ]
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        mandatory: true,
                                        text: this.XSTRING("address_6"),
                                        field: "mem_repeat_address_trial3_6"
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        mandatory: true,
                                        text: this.XSTRING("address_7"),
                                        field: "mem_repeat_address_trial3_7"
                                    }
                                ]
                            }
                        ]
                    },

                    // Famous people
                    { type: "QuestionHeading", text: this.XSTRING("cat_mem") },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("famous_1"),
                        field: "mem_famous1"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("famous_2"),
                        field: "mem_famous2"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("famous_3"),
                        field: "mem_famous3"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("famous_4"),
                        field: "mem_famous4"
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("instruction_famous"),
                        italic: true
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                pageTag: LANG_COMMANDS_SENTENCES,
                elements: [
                    // Commands
                    { type: "QuestionHeading", text: this.XSTRING("cat_lang") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_q_command_1")
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_command_practice"),
                        field: "lang_follow_command_practice"
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_q_command_2")
                    },
                    {
                        elementTag: LANG_OPTIONAL_COMMAND,
                        type: "QuestionBooleanText",
                        text: this.XSTRING("lang_command1"),
                        field: "lang_follow_command1"
                    },
                    {
                        elementTag: LANG_OPTIONAL_COMMAND,
                        type: "QuestionBooleanText",
                        text: this.XSTRING("lang_command2"),
                        field: "lang_follow_command2"
                    },
                    {
                        elementTag: LANG_OPTIONAL_COMMAND,
                        type: "QuestionBooleanText",
                        text: this.XSTRING("lang_command3"),
                        field: "lang_follow_command3"
                    },

                    // Writing sentences
                    { type: "QuestionHeading", text: this.XSTRING("cat_lang") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_q_sentences")
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_sentences_point1"),
                        field: "lang_write_sentences_point1"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_sentences_point2"),
                        field: "lang_write_sentences_point2"
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                elements: [

                    // Repeating words
                    { type: "QuestionHeading", text: this.XSTRING("cat_lang") },
                    { type: "QuestionText", text: this.XSTRING("lang_q_repeat") },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_repeat_word1"),
                        field: "lang_repeat_word1"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_repeat_word2"),
                        field: "lang_repeat_word2"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_repeat_word3"),
                        field: "lang_repeat_word3"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_repeat_word4"),
                        field: "lang_repeat_word4"
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_instruction_repeat"),
                        italic: true
                    },

                    // Repeating sentences
                    { type: "QuestionHeading", text: this.XSTRING("cat_lang") },
                    { type: "QuestionText", text: this.XSTRING("lang_q_repeat") },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_sentence1"),
                        field: "lang_repeat_sentence1"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_sentence2"),
                        field: "lang_repeat_sentence2"
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_instruction_sentences_1"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_instruction_sentences_2"),
                        italic: true
                    },

                    // Preparation for clinician for pictures
                    {
                        type: "QuestionHeading",
                        text: this.XSTRING("advance_warning_1"),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("advance_warning_2"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("advance_warning_3"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("advance_warning_4"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("advance_warning_5"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("advance_warning_6"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("advance_warning_7"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("advance_warning_8"),
                        italic: true
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinicianAssisted: true,
                elements: [
                    // Naming pictures
                    { type: "QuestionHeading", text: this.XSTRING("cat_lang") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_q_identify_pic")
                    },
                    {
                        type: "ContainerTable",
                        columns: 3,
                        elements: [
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture1",
                                image: IMAGE_SPOON
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture2",
                                image: IMAGE_BOOK
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture3",
                                image: IMAGE_KANGAROO
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture4",
                                image: IMAGE_PENGUIN
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture5",
                                image: IMAGE_ANCHOR
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture6",
                                image: IMAGE_CAMEL
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture7",
                                image: IMAGE_HARP
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture8",
                                image: IMAGE_RHINOCEROS
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture9",
                                image: IMAGE_BARREL
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture10",
                                image: IMAGE_CROWN
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture11",
                                image: IMAGE_CROCODILE
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "lang_name_picture12",
                                image: IMAGE_ACCORDION
                            }
                        ]
                    },
                    // Choosing pictures by concept
                    { type: "QuestionHeading", text: this.XSTRING("cat_lang") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_q_identify_concept")
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_concept1"),
                        field: "lang_identify_concept1"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_concept2"),
                        field: "lang_identify_concept2"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_concept3"),
                        field: "lang_identify_concept3"
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_concept4"),
                        field: "lang_identify_concept4"
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_instruction_identify_concept"),
                        italic: true
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinicianAssisted: true,
                elements: [
                    // Reading irregular words aloud
                    { type: "QuestionHeading", text: this.XSTRING("cat_lang") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_q_read_aloud")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_read_aloud_words"),
                        bold: true,
                        big: true
                    },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("lang_read_aloud_all_correct"),
                        field: "lang_read_words_aloud"
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("lang_instruction_read_aloud"),
                        italic: true
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinicianAssisted: true,
                elements: [
                    // Copy infinity
                    { type: "QuestionHeading", text: this.XSTRING("cat_vsp") },
                    { type: "QuestionText", text: this.XSTRING("vsp_q_infinity") },
                    { type: "QuestionImage", image: IMAGE_INFINITY },
                    {
                        type: "QuestionBooleanText",
                        mandatory: true,
                        text: this.XSTRING("vsp_infinity_correct"),
                        field: "vsp_copy_infinity"
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinicianAssisted: true,
                elements: [
                    // Copy cube
                    { type: "QuestionText", text: this.XSTRING("vsp_q_cube") },
                    { type: "QuestionImage", image: IMAGE_CUBE },
                    { type: "QuestionText", text: this.XSTRING("vsp_score_cube") },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: true,
                        showInstruction: false,
                        field: "vsp_copy_cube",
                        options: [
                            new KeyValuePair("0", 0),
                            new KeyValuePair("1", 1),
                            new KeyValuePair("2", 2)
                        ]
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                elements: [
                    // Draw clock
                    { type: "QuestionText", text: this.XSTRING("vsp_q_clock") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("vsp_instruction_clock"),
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("vsp_score_clock")
                    },
                    {
                        type: "QuestionMCQ",
                        mandatory: true,
                        horizontal: true,
                        showInstruction: false,
                        field: "vsp_draw_clock",
                        options: [
                            new KeyValuePair("0", 0),
                            new KeyValuePair("1", 1),
                            new KeyValuePair("2", 2),
                            new KeyValuePair("3", 3),
                            new KeyValuePair("4", 4),
                            new KeyValuePair("5", 5)
                        ]
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinicianAssisted: true,
                elements: [
                    // Count the dots
                    { type: "QuestionHeading", text: this.XSTRING("cat_vsp") },
                    { type: "QuestionText", text: this.XSTRING("vsp_q_dots") },
                    {
                        type: "ContainerTable",
                        columns: 2,
                        elements: [
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "vsp_count_dots1",
                                image: IMAGE_DOTS8
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "vsp_count_dots2",
                                image: IMAGE_DOTS10
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "vsp_count_dots3",
                                image: IMAGE_DOTS7
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "vsp_count_dots4",
                                image: IMAGE_DOTS9
                            }
                        ]
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinicianAssisted: true,
                elements: [
                    // Identify the badly-printed letters
                    { type: "QuestionHeading", text: this.XSTRING("cat_vsp") },
                    { type: "QuestionText", text: this.XSTRING("vsp_q_letters") },
                    {
                        type: "ContainerTable",
                        columns: 2,
                        elements: [
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "vsp_identify_letter1",
                                image: IMAGE_K
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "vsp_identify_letter2",
                                image: IMAGE_M
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "vsp_identify_letter3",
                                image: IMAGE_A
                            },
                            {
                                type: "QuestionBooleanImage",
                                mandatory: true,
                                field: "vsp_identify_letter4",
                                image: IMAGE_T
                            }
                        ]
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                elements: [
                    // Recall the address
                    { type: "QuestionHeading", text: this.XSTRING("cat_mem") },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("mem_q_recall_address")
                    },
                    {
                        type: "ContainerVertical",
                        elements: [
                            {
                                type: "ContainerHorizontal",
                                elements: [
                                    {
                                        type: "QuestionBooleanText",
                                        mandatory: true,
                                        text: this.XSTRING("address_1"),
                                        field: "mem_recall_address1"
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        mandatory: true,
                                        text: this.XSTRING("address_2"),
                                        field: "mem_recall_address2"
                                    }
                                ]
                            },
                            {
                                type: "ContainerHorizontal",
                                elements: [
                                    {
                                        type: "QuestionBooleanText",
                                        mandatory: true,
                                        text: this.XSTRING("address_3"),
                                        field: "mem_recall_address3"
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        mandatory: true,
                                        text: this.XSTRING("address_4"),
                                        field: "mem_recall_address4"
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        mandatory: true,
                                        text: this.XSTRING("address_5"),
                                        field: "mem_recall_address5"
                                    }
                                ]
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("address_6"),
                                field: "mem_recall_address6"
                            },
                            {
                                type: "QuestionBooleanText",
                                mandatory: true,
                                text: this.XSTRING("address_7"),
                                field: "mem_recall_address7"
                            }
                        ]
                    }
                ]
            },
            {
                // Recognize bits you didn't recall
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                onTheFly: true,
                pageTag: MEM_RECOGNIZE
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
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
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                elements: [
                    // Take picture #1 of piece of paper
                    {
                        type: "QuestionText",
                        text: this.XSTRING("picture1_q"),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("picture_instruction1")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("picture_instruction2")
                    },
                    {
                        type: "QuestionPhoto",
                        field: "picture1_blobid",
                        mandatory: false,
                        rotationField: "picture1_rotation"
                    }
                ]
            },
            {
                title: this.XSTRING("title_prefix") + " " + (pagenum++),
                clinician: true,
                elements: [
                    // Take picture #2 of piece of paper
                    {
                        type: "QuestionText",
                        text: this.XSTRING("picture2_q"),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("picture_instruction1")
                    },
                    {
                        type: "QuestionText",
                        text: this.XSTRING("picture_instruction2")
                    },
                    {
                        type: "QuestionPhoto",
                        field: "picture2_blobid",
                        mandatory: false,
                        rotationField: "picture2_rotation"
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
            fnFinished: function (result, editing_time_s) {
                self.defaultFinishedFn(result, editing_time_s);
                questionnaire = null; // for garbage collection, since we have closures referring to questionnaire
            },
            /* jshint unused:true */
            fnMakePageOnTheFly: function (currentPage, pageTag) {
                var elements = [
                        // Recognize the address
                        { type: "QuestionHeading", text: this.XSTRING("cat_mem") }
                    ];
                if (pageTag !== MEM_RECOGNIZE) {
                    throw new Error("Ace3/fnMakePageOnTheFly: called for " +
                                    "invalid page");
                }
                if (self.mem_recall_address1 &&
                        self.mem_recall_address2 &&
                        self.mem_recall_address3 &&
                        self.mem_recall_address4 &&
                        self.mem_recall_address5 &&
                        self.mem_recall_address6 &&
                        self.mem_recall_address7) {
                    elements.push(
                        {
                            type: "QuestionText",
                            text: this.XSTRING("no_need_for_extra_recall")
                        }
                    );
                } else {
                    elements.push(
                        {
                            type: "QuestionText",
                            text: this.XSTRING("mem_q_recognize_address")
                        }
                    );
                    if (!self.mem_recall_address1 ||
                            !self.mem_recall_address2) {
                        elements.push({
                            type: "QuestionMCQ",
                            mandatory: true,
                            horizontal: true,
                            showInstruction: false,
                            field: "mem_recognize_address1",
                            options: [
                                new KeyValuePair(this.XSTRING("mem_recall_option1_line1"), 0),
                                new KeyValuePair(this.XSTRING("mem_recall_option2_line1"), 1),
                                new KeyValuePair(this.XSTRING("mem_recall_option3_line1"), 0)
                            ]
                        });
                    }
                    if (!self.mem_recall_address3) {
                        elements.push({
                            type: "QuestionMCQ",
                            mandatory: true,
                            horizontal: true,
                            showInstruction: false,
                            field: "mem_recognize_address2",
                            options: [
                                new KeyValuePair(this.XSTRING("mem_recall_option1_line2"), 0),
                                new KeyValuePair(this.XSTRING("mem_recall_option2_line2"), 1),
                                new KeyValuePair(this.XSTRING("mem_recall_option3_line2"), 0)
                            ]
                        });
                    }
                    if (!self.mem_recall_address4 || !self.mem_recall_address5) {
                        elements.push({
                            type: "QuestionMCQ",
                            mandatory: true,
                            horizontal: true,
                            showInstruction: false,
                            field: "mem_recognize_address3",
                            options: [
                                new KeyValuePair(this.XSTRING("mem_recall_option1_line3"), 0),
                                new KeyValuePair(this.XSTRING("mem_recall_option2_line3"), 0),
                                new KeyValuePair(this.XSTRING("mem_recall_option3_line3"), 1)
                            ]
                        });
                    }
                    if (!self.mem_recall_address6) {
                        elements.push({
                            type: "QuestionMCQ",
                            horizontal: true,
                            showInstruction: false,
                            field: "mem_recognize_address4",
                            options: [
                                new KeyValuePair(this.XSTRING("mem_recall_option1_line4"), 0),
                                new KeyValuePair(this.XSTRING("mem_recall_option2_line4"), 1),
                                new KeyValuePair(this.XSTRING("mem_recall_option3_line4"), 0)
                            ]
                        });
                    }
                    if (!self.mem_recall_address7) {
                        elements.push({
                            type: "QuestionMCQ",
                            mandatory: true,
                            horizontal: true,
                            showInstruction: false,
                            field: "mem_recognize_address5",
                            options: [
                                new KeyValuePair(this.XSTRING("mem_recall_option1_line5"), 1),
                                new KeyValuePair(this.XSTRING("mem_recall_option2_line5"), 0),
                                new KeyValuePair(this.XSTRING("mem_recall_option3_line5"), 0)
                            ]
                        });
                    }
                }
                return {
                    title: this.XSTRING("title_prefix") + " 15", // magic number: memory page number
                    clinician: true,
                    elements: elements
                };
            },
            /* jshint unused:true */
            fnShowNext: function (currentPage, pageTag) {
                if (pageTag === LANG_COMMANDS_SENTENCES) {
                    questionnaire.setMandatoryByTag(
                        LANG_OPTIONAL_COMMAND,
                        self.lang_follow_command_practice
                    );
                }
                return { care: false }; // the mandatory framework will do the rest
            }
        });
        questionnaire.open();
    }
});

module.exports = Ace3;
