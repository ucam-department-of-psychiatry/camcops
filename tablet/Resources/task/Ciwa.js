// Ciwa.js

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
    // TABLE
    tablename = "ciwa",
    fieldlist = dbcommon.standardTaskFields(),
    nscoredquestions = 10;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nscoredquestions,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: 't', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'hr', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'sbp', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'dbp', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'rr', type: DBCONSTANTS.TYPE_INTEGER}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Ciwa(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Ciwa, taskcommon.BaseTask);
lang.extendPrototype(Ciwa, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Ciwa,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 1, nscoredquestions);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByPrefix(this, "q", 1, nscoredquestions);
    },

    getSummary: function () {
        return L('total_score') + " " + this.getTotalScore() + "/67" +
                this.isCompleteSuffix();
    },

    getDetail: function () {
        var totalscore = this.getTotalScore(),
            severity = (totalscore > 15 ?
                    L('ciwa_category_severe') :
                    (totalscore >= 8 ?
                            L('ciwa_category_moderate') :
                            L('ciwa_category_mild')
                    )
            );
        return (
            taskcommon.valueDetail(this, "ciwa_q", "_s", " ", "q", 1,
                                   nscoredquestions) +
            "\n" +
            L('ciwa_t') + ": " + this.t + "\n" +
            L('ciwa_hr') + ": " + this.hr + "\n" +
            L('ciwa_bp') + ": " + this.sbp + " / " + this.dbp + "\n" +
            L('ciwa_rr') + ": " + this.rr + "\n" +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('ciwa_severity') + " " + severity
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function makepage(n, lastoption) {
            var options = [],
                i;
            for (i = 0; i <= lastoption; ++i) {
                options.push(new KeyValuePair(L("ciwa_q" + n +
                                                "_option" + i), i));
            }
            return {
                title: L("ciwa_q" + n + "_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("ciwa_q" + n + "_question")
                    },
                    {
                        type: "QuestionMCQ",
                        options: options,
                        field: "q" + n
                    }
                ]
            };
        }

        pages = [ self.getClinicianDetailsPage() ]; // Clinician info 3/3
        pages.push(makepage(1, 7));
        pages.push(makepage(2, 7));
        pages.push(makepage(3, 7));
        pages.push(makepage(4, 7));
        pages.push(makepage(5, 7));
        pages.push(makepage(6, 7));
        pages.push(makepage(7, 7));
        pages.push(makepage(8, 7));
        pages.push(makepage(9, 7));
        pages.push(makepage(10, 4));
        pages.push({
            title: L("ciwa_vitals_title"),
            clinician: true,
            elements: [
                { type: "QuestionText", text: L("ciwa_vitals_question") },
                {
                    type: "QuestionTypedVariables",
                    mandatory: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            field: "t",
                            prompt: L("ciwa_t")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            field: "hr",
                            prompt: L("ciwa_hr")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            field: "sbp",
                            prompt: L("ciwa_sbp")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            field: "dbp",
                            prompt: L("ciwa_dbp")
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            field: "rr",
                            prompt: L("ciwa_rr")
                        }
                    ]
                }
            ]
        });

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

module.exports = Ciwa;
