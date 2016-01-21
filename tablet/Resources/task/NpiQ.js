// NpiQ.js

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
    tablename = "npiq",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 12,
    // TASK
    ENDORSED = "endorsed",
    SEVERITY = "severity",
    DISTRESS = "distress",
    RATING_ELEMENT = "rating_element",
    RATING_STATIC_ELEMENT = "static_element";

fieldlist.push.apply(fieldlist, dbcommon.RESPONDENT_FIELDSPECS);
dbcommon.appendRepeatedFieldDef(fieldlist, ENDORSED, 1, nquestions,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, SEVERITY, 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, DISTRESS, 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function NpiQ(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(NpiQ, taskcommon.BaseTask);
lang.extendPrototype(NpiQ, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: NpiQ,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "npiq",
    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER
    getTotalScore: function () {
        return taskcommon.countBooleansByPrefix(this, ENDORSED, 1, nquestions);
    },

    getDistressScore: function () {
        var score = 0,
            q;
        for (q = 1; q <= nquestions; ++q) {
            if (this[ENDORSED + q] && this[DISTRESS + q] !== null) {
                score += this[DISTRESS + q];
            }
        }
        return score;
    },

    getSeverityScore: function () {
        var score = 0,
            q;
        for (q = 1; q <= nquestions; ++q) {
            if (this[ENDORSED + q] && this[SEVERITY + q] !== null) {
                score += this[SEVERITY + q];
            }
        }
        return score;
    },

    questionComplete: function (q) {
        if (this[ENDORSED + q] === null) {
            return false;
        }
        if (this[ENDORSED + q]) {
            if (this[DISTRESS + q] === null ||
                    this[SEVERITY + q] === null) {
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
            "Endorsed: " + this.getTotalScore() + "/12; " +
            "severity " + this.getSeverityScore() + "/36; " +
            "distress " + this.getDistressScore() + "/60" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            msg = "",
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += (this.XSTRING("t" + i) + ": " +
                    uifunc.yesNoNull(this[ENDORSED + i]));
            if (this[ENDORSED + i]) {
                msg += (
                    " (severity " + this[SEVERITY + i] + ", " +
                    "distress " + this[DISTRESS + i] + ")"
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
            options_severity = [
                new KeyValuePair(this.XSTRING('severity_1'), 1),
                new KeyValuePair(this.XSTRING('severity_2'), 2),
                new KeyValuePair(this.XSTRING('severity_3'), 3)
            ],
            options_distress = [
                new KeyValuePair(this.XSTRING('distress_0'), 0),
                new KeyValuePair(this.XSTRING('distress_1'), 1),
                new KeyValuePair(this.XSTRING('distress_2'), 2),
                new KeyValuePair(this.XSTRING('distress_3'), 3),
                new KeyValuePair(this.XSTRING('distress_4'), 4),
                new KeyValuePair(this.XSTRING('distress_5'), 5)
            ],
            pages,
            q,
            questionnaire;

        function makepage(q) {
            var endorsed = self[ENDORSED + q],
                mandatory = endorsed ? true : false,
                visible = mandatory;
            // Use self, not this (closure) for this callback function.
            return {
                title: "NPI-Q (" + q + " / 12): " + self.XSTRING("t" + q),
                pageTag: q,
                elements: [
                    {
                        type: "QuestionText",
                        bold: true,
                        text: self.XSTRING("q" + q)
                    },
                    {
                        type: "QuestionMCQ",
                        field: ENDORSED + q,
                        options: options_yesno,
                        showInstruction: false,
                        horizontal: true,
                        mandatory: true
                    },
                    {
                        elementTag: RATING_STATIC_ELEMENT,
                        type: "QuestionHorizontalRule",
                        visible: visible
                    },
                    {
                        elementTag: RATING_STATIC_ELEMENT,
                        type: "QuestionText",
                        bold: true,
                        text: self.XSTRING("severity_instruction"),
                        visible: visible
                    },
                    {
                        elementTag: RATING_ELEMENT,
                        type: "QuestionMCQ",
                        field: SEVERITY + q,
                        options: options_severity,
                        showInstruction: false,
                        horizontal: false,
                        mandatory: mandatory,
                        visible: visible
                    },
                    {
                        elementTag: RATING_STATIC_ELEMENT,
                        type: "QuestionHorizontalRule",
                        visible: visible
                    },
                    {
                        elementTag: RATING_STATIC_ELEMENT,
                        type: "QuestionText",
                        bold: true,
                        text: self.XSTRING("distress_instruction"),
                        visible: visible
                    },
                    {
                        elementTag: RATING_ELEMENT,
                        type: "QuestionMCQ",
                        field: DISTRESS + q,
                        options: options_distress,
                        showInstruction: false,
                        horizontal: false,
                        mandatory: mandatory,
                        visible: visible
                    }
                ]
            };
        }

        pages = [
            {
                title: L('t_npiq'),
                clinician: false,
                elements: [
                    this.getRespondentQuestionnaireBlock(true),
                    { type: "QuestionText", text: this.XSTRING('instruction_1') },
                    { type: "QuestionText", text: this.XSTRING('instruction_2'), bold: true },
                    { type: "QuestionText", text: this.XSTRING('instruction_3'), bold: true },
                    { type: "QuestionText", text: this.XSTRING('instruction_4') }
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
            fnMakePageOnTheFly: function (pageId, pageTag) {
                return makepage(pageTag);
            },
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: function (field, value) {
                var endorsed,
                    mandatory,
                    visible;
                self.defaultSetFieldFn(field, value);
                if (field.substring(0, ENDORSED.length) === ENDORSED) {
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

module.exports = NpiQ;
