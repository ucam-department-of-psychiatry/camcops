// Caps.js

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
    // TABLE
    tablename = "caps",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 32,
    // TASK
    RATING_ELEMENT = "rating_element",
    RATING_STATIC_ELEMENT = "static_element";

dbcommon.appendRepeatedFieldDef(fieldlist, "endorse", 1, nquestions,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "distress", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "intrusiveness", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "frequency", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Caps(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Caps, taskcommon.BaseTask);
lang.extendPrototype(Caps, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Caps,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _prohibitCommercial: true,
    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.countBooleansByPrefix(this, "endorse", 1, nquestions);
    },

    getDistressScore: function () {
        var score = 0,
            q;
        for (q = 1; q <= nquestions; ++q) {
            if (this["endorse" + q] && this["distress" + q] !== null) {
                score += this["distress" + q];
            }
        }
        return score;
    },

    getIntrusivenessScore: function () {
        var score = 0,
            q;
        for (q = 1; q <= nquestions; ++q) {
            if (this["endorse" + q] && this["intrusiveness" + q] !== null) {
                score += this["intrusiveness" + q];
            }
        }
        return score;
    },

    getFrequencyScore: function () {
        var score = 0,
            q;
        for (q = 1; q <= nquestions; ++q) {
            if (this["endorse" + q] && this["frequency" + q] !== null) {
                score += this["frequency" + q];
            }
        }
        return score;
    },

    questionComplete: function (q) {
        if (this["endorse" + q] === null) {
            return false;
        }
        if (this["endorse" + q]) {
            if (this["distress" + q] === null ||
                    this["intrusiveness" + q] === null ||
                    this["frequency" + q] === null) {
                return false;
            }
        }
        return true;
    },

    // Standard task functions
    isComplete: function () {
        var i;
        for (i = 1; i <= nquestions; ++i) {
            if (!this.questionComplete(i)) {
                return false;
            }
        }
        return true;
    },

    getSummary: function () {
        return (
            L('total_score') + " " +
            this.getTotalScore() + "/32 (D " +
            this.getDistressScore() + "/160, I " +
            this.getIntrusivenessScore() + "/160, F " +
            this.getFrequencyScore() + "/160)" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            msg = "",
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += (this.XSTRING("q" + i) + " " +
                    uifunc.yesNoNull(this["endorse" + i]));
            if (this["endorse" + i]) {
                msg += (
                    " (D " + this["distress" + i] +
                    ", I " + this["intrusiveness" + i] +
                    ", F " + this["frequency" + i] + ")"
                );
            }
            msg += "\n";
        }
        return (msg + "\n" + this.getSummary());
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            options_yesno = taskcommon.OPTIONS_NO_YES_BOOLEAN,
            options_distress = [
                new KeyValuePair(this.XSTRING('distress_option1'), 1),
                new KeyValuePair("2", 2),
                new KeyValuePair("3", 3),
                new KeyValuePair("4", 4),
                new KeyValuePair(this.XSTRING('distress_option5'), 5)
            ],
            options_intrusiveness = [
                new KeyValuePair(this.XSTRING('intrusiveness_option1'), 1),
                new KeyValuePair("2", 2),
                new KeyValuePair("3", 3),
                new KeyValuePair("4", 4),
                new KeyValuePair(this.XSTRING('intrusiveness_option5'), 5)
            ],
            options_frequency = [
                new KeyValuePair(this.XSTRING('frequency_option1'), 1),
                new KeyValuePair("2", 2),
                new KeyValuePair("3", 3),
                new KeyValuePair("4", 4),
                new KeyValuePair(this.XSTRING('frequency_option5'), 5)
            ],
            pages,
            q,
            questionnaire;

        function makepage(q) {
            var endorsed = self["endorse" + q],
                mandatory = endorsed ? true : false,
                visible = mandatory; // (endorsed === null || endorsed);
            return {
                title: "CAPS (" + q + " / 32)",
                pageTag: q,
                elements: [
                    {
                        type: "QuestionText",
                        text: self.XSTRING("q" + q),
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        field: "endorse" + q,
                        options: options_yesno,
                        showInstruction: false,
                        horizontal: true,
                        mandatory: true
                    },
                    {
                        elementTag: RATING_STATIC_ELEMENT,
                        type: "QuestionText",
                        text: self.XSTRING("if_yes_please_rate"),
                        bold: true,
                        visible: visible
                    },
                    {
                        elementTag: RATING_ELEMENT,
                        type: "QuestionMCQ",
                        field: "distress" + q,
                        options: options_distress,
                        showInstruction: false,
                        horizontal: true,
                        mandatory: mandatory,
                        visible: visible
                    },
                    {
                        elementTag: RATING_STATIC_ELEMENT,
                        type: "QuestionHorizontalRule",
                        visible: visible
                    },
                    {
                        elementTag: RATING_ELEMENT,
                        type: "QuestionMCQ",
                        field: "intrusiveness" + q,
                        options: options_intrusiveness,
                        showInstruction: false,
                        horizontal: true,
                        mandatory: mandatory,
                        visible: visible
                    },
                    {
                        elementTag: RATING_STATIC_ELEMENT,
                        type: "QuestionHorizontalRule",
                        visible: visible
                    },
                    {
                        elementTag: RATING_ELEMENT,
                        type: "QuestionMCQ",
                        field: "frequency" + q,
                        options: options_frequency,
                        showInstruction: false,
                        horizontal: true,
                        mandatory: mandatory,
                        visible: visible
                    }
                ]
            };
        }

        pages = [
            {
                title: this.XSTRING('instruction_title'),
                elements: [
                    { type: "QuestionHeading", text: this.XSTRING('instruction_1') },
                    { type: "QuestionText", text: this.XSTRING('instruction_2') },
                    { type: "QuestionText", text: this.XSTRING('instruction_3') },
                    { type: "QuestionText", text: this.XSTRING('instruction_4') },
                    { type: "QuestionText", text: this.XSTRING('instruction_5'), bold: true },
                    { type: "QuestionHeading", text: this.XSTRING('instruction_6') },
                    { type: "QuestionText", text: this.XSTRING('instruction_7') },
                    { type: "QuestionText", text: this.XSTRING('instruction_8') },
                    { type: "QuestionText", text: this.XSTRING('instruction_9') },
                    { type: "QuestionText", text: this.XSTRING('instruction_10') }
                    // remove "example questions", which relate to a paper-based illustration of how to circle the ratings:
                    // { type: "QuestionHeading", text: this.XSTRING('instruction_11') },
                    // { type: "QuestionText", text: this.XSTRING('instruction_12') },
                ]
            }
        ];
        for (q = 1; q <= nquestions; ++q) {
            pages.push({ pageTag: q, onTheFly: true });
        }

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            /* jshint unused:true */
            fnMakePageOnTheFly: function (pageId, pageTag) {
                return makepage(pageTag);
            },
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: function (field, value) {
                var endorsed,
                    mandatory,
                    visible;
                self.defaultSetFieldFn(field, value);
                if (field.substring(0, "endorse".length) === "endorse") {
                    endorsed = value;
                    mandatory = endorsed ? true : false;
                    visible = mandatory; // (endorsed === null || endorsed);
                    questionnaire.setMandatoryByTag(RATING_ELEMENT, mandatory);
                    questionnaire.setVisibleByTag(RATING_ELEMENT, visible);
                    questionnaire.setVisibleByTag(RATING_STATIC_ELEMENT,
                                                  visible);
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

module.exports = Caps;
