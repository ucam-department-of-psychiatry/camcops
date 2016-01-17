// Panss.js

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
    tablename = "panss",
    fieldlist = dbcommon.standardTaskFields(),
    np = 7,
    nn = 7,
    ng = 16;

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "p", 1, np,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "n", 1, nn,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "g", 1, ng,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Panss(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Panss, taskcommon.BaseTask);
lang.extendPrototype(Panss, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Panss,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _crippled: true,

    // OTHER

    // Scoring
    getP: function () {
        return taskcommon.totalScoreByPrefix(this, "p", 1, np);
    },

    getN: function () {
        return taskcommon.totalScoreByPrefix(this, "n", 1, nn);
    },

    getG: function () {
        return taskcommon.totalScoreByPrefix(this, "g", 1, ng);
    },

    // Standard task functions
    isComplete: function () {
        return (taskcommon.isCompleteByPrefix(this, "p", 1, np) &&
                taskcommon.isCompleteByPrefix(this, "n", 1, nn) &&
                taskcommon.isCompleteByPrefix(this, "g", 1, ng));
    },

    getSummary: function () {
        var p = this.getP(),
            n = this.getN(),
            g = this.getG(),
            composite = p - n,
            total = p + g + n;
        return L('panss_p') + " " + p + "/49. " +
                L('panss_n') + " " + n + "/49. " +
                L('panss_g') + " " + g + "/112. " +
                L('panss_composite') + " " + composite + ". " +
                L('total_score') + " " + total + "/210." +
                this.isCompleteSuffix();
    },

    getDetail: function () {
        return (
            taskcommon.valueDetail(this, "panss_p", "_s", " ", "p", 1, np) +
            taskcommon.valueDetail(this, "panss_n", "_s", " ", "n", 1, nn) +
            taskcommon.valueDetail(this, "panss_g", "_s", " ", "g", 1, ng) +
            "\n" +
            this.getSummary()
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            panss_options = [
                new KeyValuePair(L('panss_option1'), 1),
                new KeyValuePair(L('panss_option2'), 2),
                new KeyValuePair(L('panss_option3'), 3),
                new KeyValuePair(L('panss_option4'), 4),
                new KeyValuePair(L('panss_option5'), 5),
                new KeyValuePair(L('panss_option6'), 6),
                new KeyValuePair(L('panss_option7'), 7)
            ],
            qs_p = [],
            fields_p = [],
            n,
            qs_n = [],
            fields_n = [],
            qs_g = [],
            fields_g = [],
            pages,
            questionnaire;

        for (n = 1; n <= np; ++n) {
            qs_p.push(L("panss_p" + n + "_s"));
            fields_p.push("p" + n);
        }
        for (n = 1; n <= nn; ++n) {
            qs_n.push(L("panss_n" + n + "_s"));
            fields_n.push("n" + n);
        }
        for (n = 1; n <= ng; ++n) {
            qs_g.push(L("panss_g" + n + "_s"));
            fields_g.push("g" + n);
        }

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        pages = [ self.getClinicianDetailsPage() ]; // Clinician info 3/3
        pages.push({
            title: L("t_panss") + " (P)",
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    text: L('data_collection_only'),
                    bold: true
                },
                {
                    type: "QuestionMCQGrid",
                    options: panss_options,
                    questions: qs_p,
                    fields: fields_p
                }
            ]
        });
        pages.push({
            title: L("t_panss") + " (N)",
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    text: L('data_collection_only'),
                    bold: true
                },
                {
                    type: "QuestionMCQGrid",
                    options: panss_options,
                    questions: qs_n,
                    fields: fields_n
                }
            ]
        });
        pages.push({
            title: L("t_panss") + " (G)",
            clinician: true,
            elements: [
                {
                    type: "QuestionText",
                    text: L('data_collection_only'),
                    bold: true
                },
                {
                    type: "QuestionMCQGrid",
                    options: panss_options,
                    questions: qs_g,
                    fields: fields_g
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

module.exports = Panss;
