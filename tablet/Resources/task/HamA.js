// HamA.js

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
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "hama",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 14;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function HamA(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(HamA, taskcommon.BaseTask);
lang.extendPrototype(HamA, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: HamA,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 1, nquestions);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + "/56" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var totalscore = this.getTotalScore(),
            severity = (totalscore >= 31 ? L('very_severe')
                        : (totalscore >= 25 ? L('moderate_to_severe')
                           : (totalscore >= 18 ? L('mild_to_moderate')
                              : L('mild')
                             )
                          )
            );
        // Scoring according to the NINDS datasheet, the www.cnsforum.com
        // source, and a couple of others.
        // There seems to be some disagreement about the exact cutoffs.
        return (
            taskcommon.valueDetail(this, "hama_q", "_s", " ", "q", 1,
                                   nquestions) +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('hama_symptom_severity') + " " + severity
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire,
            n;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function makepage(n) {
            return {
                title: L("hama_q" + n + "_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("hama_q" + n + "_question")
                    },
                    {
                        type: "QuestionMCQ",
                        field: "q" + n,
                        options: [
                            new KeyValuePair(L("hama_q" + n + "_option0"), 0),
                            new KeyValuePair(L("hama_q" + n + "_option1"), 1),
                            new KeyValuePair(L("hama_q" + n + "_option2"), 2),
                            new KeyValuePair(L("hama_q" + n + "_option3"), 3),
                            new KeyValuePair(L("hama_q" + n + "_option4"), 4)
                        ]
                    }
                ]
            };
        }

        pages = [ self.getClinicianDetailsPage() ]; // Clinician info 3/3
        for (n = 1; n <= 14; ++n) {
            pages.push(makepage(n));
        }

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

module.exports = HamA;
