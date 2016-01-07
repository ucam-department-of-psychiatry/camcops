// Cape42.js

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
    // TABLE
    tablename = "cape42",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 42,
    // TASK
    RATING_ELEMENT = "rating_element",
    RATING_STATIC_ELEMENT = "static_element",
    POSITIVE = [2, 5, 6, 7, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 30, 31, 33,
                34, 41, 42],
    DEPRESSIVE = [1, 9, 12, 14, 19, 38, 39, 40],
    NEGATIVE = [3, 4, 8, 16, 18, 21, 23, 25, 27, 29, 32, 35, 36, 37],
    ALL = [], // see below
    MIN_SCORE_PER_Q = 1,
    MAX_SCORE_PER_Q = 4,
    tmpindex;

for (tmpindex = 1; tmpindex <= nquestions; ++tmpindex) {
    ALL.push(tmpindex);
}

dbcommon.appendRepeatedFieldDef(fieldlist, "frequency", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "distress", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Cape42(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Cape42, taskcommon.BaseTask);
lang.extendPrototype(Cape42, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Cape42,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getDistressScore: function (qlist) {
        var score = 0,
            q,
            i;
        for (i = 0; i < qlist.length; ++i) {
            q = qlist[i];
            if (this["frequency" + q] > MIN_SCORE_PER_Q) {
                score += this["distress" + q];  // n + null === n
            } else {
                score += MIN_SCORE_PER_Q;
                // ... if frequency is 1, score 1 for distress?
            }
        }
        return score;
    },

    getFrequencyScore: function (qlist) {
        var score = 0,
            q,
            i;
        for (i = 0; i < qlist.length; ++i) {
            q = qlist[i];
            score += this["frequency" + q];  // OK to add null
        }
        return score;
    },

    questionComplete: function (q) {
        if (this["frequency" + q] === null) {
            return false;
        }
        if (this["frequency" + q] > MIN_SCORE_PER_Q) {
            if (this["distress" + q] === null) {
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
            "ALL: " +
            "frequency " +
            this.getFrequencyScore(ALL) +
            " (" + MIN_SCORE_PER_Q * ALL.length +
            "–" + MAX_SCORE_PER_Q * ALL.length + ")" +
            ", distress " +
            this.getDistressScore(ALL) +
            " (" + MIN_SCORE_PER_Q * ALL.length +
            "–" + MAX_SCORE_PER_Q * ALL.length + ")" +
            "\nPOSITIVE: " +
            "frequency " +
            this.getFrequencyScore(POSITIVE) +
            " (" + MIN_SCORE_PER_Q * POSITIVE.length +
            "–" + MAX_SCORE_PER_Q * POSITIVE.length + ")" +
            ", distress " +
            this.getDistressScore(POSITIVE) +
            " (" + MIN_SCORE_PER_Q * POSITIVE.length +
            "–" + MAX_SCORE_PER_Q * POSITIVE.length + ")" +
            "\nNEGATIVE: " +
            "frequency " +
            this.getFrequencyScore(NEGATIVE) +
            " (" + MIN_SCORE_PER_Q * NEGATIVE.length +
            "–" + MAX_SCORE_PER_Q * NEGATIVE.length + ")" +
            ", distress " +
            this.getDistressScore(NEGATIVE) +
            " (" + MIN_SCORE_PER_Q * NEGATIVE.length +
            "–" + MAX_SCORE_PER_Q * NEGATIVE.length + ")" +
            "\nDEPRESSIVE: " +
            "frequency " +
            this.getFrequencyScore(DEPRESSIVE) +
            " (" + MIN_SCORE_PER_Q * DEPRESSIVE.length +
            "–" + MAX_SCORE_PER_Q * DEPRESSIVE.length + ")" +
            ", distress " +
            this.getDistressScore(DEPRESSIVE) +
            " (" + MIN_SCORE_PER_Q * DEPRESSIVE.length +
            "–" + MAX_SCORE_PER_Q * DEPRESSIVE.length + ")" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var msg = "",
            i;
        for (i = 1; i <= nquestions; ++i) {
            msg += L("cape42_q" + i) + " F:" + this["frequency" + i];
            if (this["frequency" + i] > MIN_SCORE_PER_Q) {
                msg += " (D:" + this["distress" + i] + ")";
            }
            msg += "\n";
        }
        return (msg + "\n" + this.getSummary());
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            options_distress = [
                new KeyValuePair(L('cape42_distress_option1'), 1),
                new KeyValuePair(L('cape42_distress_option2'), 2),
                new KeyValuePair(L('cape42_distress_option3'), 3),
                new KeyValuePair(L('cape42_distress_option4'), 4)
            ],
            options_frequency = [
                new KeyValuePair(L('cape42_frequency_option1'), 1),
                new KeyValuePair(L('cape42_frequency_option2'), 2),
                new KeyValuePair(L('cape42_frequency_option3'), 3),
                new KeyValuePair(L('cape42_frequency_option4'), 4)
            ],
            pages,
            q,
            questionnaire;

        function makepage(q) {
            var frequency = self["frequency" + q],
                endorsed = (frequency > MIN_SCORE_PER_Q),
                mandatory = endorsed ? true : false,
                visible = mandatory; // (endorsed === null || endorsed);
            return {
                title: "CAPE-42 (" + q + " / 42)",
                pageTag: q,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("cape42_q" + q),
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        field: "frequency" + q,
                        options: options_frequency,
                        showInstruction: false,
                        horizontal: false,
                        mandatory: true
                    },
                    {
                        elementTag: RATING_STATIC_ELEMENT,
                        type: "QuestionText",
                        text: L("cape42_distress_stem"),
                        bold: true,
                        visible: visible
                    },
                    {
                        elementTag: RATING_ELEMENT,
                        type: "QuestionMCQ",
                        field: "distress" + q,
                        options: options_distress,
                        showInstruction: false,
                        horizontal: false,
                        mandatory: mandatory,
                        visible: visible
                    }
                ]
            };
        }

        pages = [];
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
                if (field.substring(0, "frequency".length) === "frequency") {
                    endorsed = (value > MIN_SCORE_PER_Q);
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

module.exports = Cape42;
