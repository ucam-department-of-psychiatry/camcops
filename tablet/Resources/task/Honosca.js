// Honosca.js

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
    tablename = "honosca",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 15;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: 'period_rated', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Honosca(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Honosca, taskcommon.BaseTask);
lang.extendPrototype(Honosca, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Honosca,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getScoreSum: function (start, end) {
        var total = 0,
            i,
            value;
        for (i = start; i <= end; ++i) {
            value = this["q" + i];
            if (value !== 9) { // 9 is "not known"
                total += value;
            }
        }
        return total;
    },

    getTotalScore: function () {
        return this.getScoreSum(1, nquestions);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions) &&
            this.period_rated !== null;
    },

    getSummary: function () {
        return (
            L('total_score') + " " + this.getTotalScore() + "/60" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var section_a = this.getScoreSum(1, 13),
            section_b = this.getScoreSum(14, 15);
            // totalscore = this.getTotalScore();
        return taskcommon.valueDetail(this, "honosca_q", "_s", " ", "q", 1,
                                      nquestions) +
            "\n" +
            L('honosca_section_a_total') + " " + section_a + "\n" +
            L('honosca_section_b_total') + " " + section_b + "\n" +
            "\n" +
            this.getSummary() + "\n";
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            pages,
            questionnaire,
            i;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function makepage(q, prefix) {
            var options = [],
                title = prefix + q,
                j;
            for (j = 0; j <= 4; ++j) {
                options.push(new KeyValuePair(L("honosca_q" + q +
                                                "_option" + j), j));
            }
            options.push(new KeyValuePair(L("honos_option9"), 9)); // common to all
            return {
                title: title,
                clinician: true,
                elements: [
                    { type: "QuestionText", text: L("honosca_q" + q) },
                    {
                        type: "QuestionMCQ",
                        field: "q" + q,
                        options: options,
                    },
                ],
            };
        }

        pages = [
            self.getClinicianDetailsPage(), // Clinician info 3/3
            {
                title: L("honosca_firstpage_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionTypedVariables",
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "period_rated",
                                prompt: L("honos_period_rated"),
                                hint: L("honos_period_rated")
                            },
                        ],
                    },
                ],
            },
            {
                title: L('honosca_section_a_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("honosca_section_a_instructions")
                    },
                ],
            }
        ];
        for (i = 1; i <= 13; ++i) {
            pages.push(makepage(i, L('honosca_section_a_title_prefix')));
        }
        pages.push(
            {
                title: L('honosca_section_b_title'),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("honosca_section_b_instructions")
                    },
                ],
            }
        );
        for (i = 14; i <= nquestions; ++i) {
            pages.push(makepage(i, L('honosca_section_b_title_prefix')));
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

module.exports = Honosca;
