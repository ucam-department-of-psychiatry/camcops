// Phq15.js

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
    tablename = "phq15",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 15;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Phq15(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Phq15, taskcommon.BaseTask);
lang.extendPrototype(Phq15, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Phq15,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScore(this, "q", 1, nquestions);
    },

    getNSevere: function () {
        var total = 0,
            i;
        for (i = 1; i <= nquestions; ++i) {
            total += (this["q" + i] >= 2 ? 1 : 0);
        }
        return total;
    },

    // Standard task functions
    isComplete: function () {
        var female = this.isFemale();
        // Titanium.API.trace("patient - female = " + female);
        if (this.q1 === null ||
                this.q2 === null ||
                this.q3 === null ||
                (female && this.q4 === null) || // women only
                this.q5 === null ||
                this.q6 === null ||
                this.q7 === null ||
                this.q8 === null ||
                this.q9 === null ||
                this.q10 === null ||
                this.q11 === null ||
                this.q12 === null ||
                this.q13 === null ||
                this.q14 === null ||
                this.q15 === null) {
            return false;
        }
        return true;
    },

    getSummary: function () {
        return (
            L('total_score') + " " + this.getTotalScore() + "/30, " +
            L('phq15_n_severe_symptoms') + " " + this.getNSevere() + "/15" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            nsevere = this.getNSevere(),
            somatoform_likely = (nsevere >= 3),
            totalscore = this.getTotalScore(),
            severity = (totalscore >= 15 ? L('severe')
                : (totalscore >= 10 ? L('moderate')
                   : (totalscore >= 5 ? L('mild')
                      : L('none')
                     )
                  )
            );
        return (
            taskcommon.valueDetail(this, "phq15_q", "_s", " ", "q", 1,
                                   nquestions) +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('phq15_exceeds_somatoform_cutoff') + " " +
            uifunc.yesNo(somatoform_likely) + "\n" +
            L('phq15_symptom_severity') + " " + severity
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            female = self.isFemale(),
            qs = [],
            fields = [],
            n,
            pages,
            questionnaire;
        for (n = 1; n <= nquestions; ++n) {
            if (!female && n === 4) {
                continue;
            }
            qs.push(L("phq15_q" + n));
            fields.push("q" + n);
        }
        pages = [
            {
                title: L('phq15_title'),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('phq15_stem'),
                        bold: true
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: [
                            new KeyValuePair(L('phq15_a0'), 0),
                            new KeyValuePair(L('phq15_a1'), 1),
                            new KeyValuePair(L('phq15_a2'), 2)
                        ],
                        questions: qs,
                        fields: fields
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

module.exports = Phq15;
