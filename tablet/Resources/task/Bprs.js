// Bprs.js

/*
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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
    // TABLE
    tablename = "bprs",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 20,
    // TASK
    nscoredquestions = 18;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK
// Some scales use 9 for "not assessed"; we'll use 0 (as in the original BPRS).

function Bprs(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Bprs, taskcommon.BaseTask);
lang.extendPrototype(Bprs, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Bprs,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScore(this, "q", 1, nscoredquestions);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (L('bprs18_total_score') + " " + this.getTotalScore() + "/126" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        return (
            taskcommon.valueDetail(this, "bprs_q", "_s", " ", "q", 1,
                                   nquestions) +
            "\n" + this.getSummary()
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            n,
            includeNA,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function makepage(n, includeNA) {
            var options = [],
                i;
            for (i = 1; i <= 7; ++i) {
                options.push(new KeyValuePair(L("bprs_q" + n +
                                                "_option" + i), i));
            }
            if (includeNA) {
                options.push(new KeyValuePair(L("bprs_q" + n +
                                                "_option0"), 0));
            }
            return {
                title: L("bprs_q" + n + "_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("bprs_q" + n + "_question")
                    },
                    {
                        type: "QuestionMCQ",
                        field: "q" + n,
                        options: options,
                    },
                ],
            };
        }

        pages = [ self.getClinicianDetailsPage() ]; // Clinician info 3/3
        for (n = 1; n <= nquestions; ++n) {
            includeNA = (n === 1 || n === 2 || n === 5 || n === 8 || n === 9 ||
                             n === 10 || n === 11 || n === 12 || n === 15 ||
                             n === 18 || n === 20);
            pages.push(makepage(n, includeNA));
        }

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn,
        });
        questionnaire.open();
    },
});

module.exports = Bprs;
