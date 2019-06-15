// Bdi.js

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
/*global L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // TABLE
    tablename = "bdi",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 21,
    // TASK
    BDI_I = "BDI-I",
    BDI_IA = "BDI-IA",
    BDI_II = "BDI-II";

fieldlist.push({ name: "bdi_scale", type: DBCONSTANTS.TYPE_TEXT });
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Bdi(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Bdi, taskcommon.BaseTask);
lang.extendPrototype(Bdi, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Bdi,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _crippled: true,

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
        return (L('total_score') + " " + this.getTotalScore() + "/63" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            bdi_options = [
                new KeyValuePair("0", 0),
                new KeyValuePair("1", 1),
                new KeyValuePair("2", 2),
                new KeyValuePair("3", 3)
            ],
            qs = [],
            fields = [],
            n,
            pages,
            questionnaire;

        if (self.id === null) {
            // first edit; set default
            self.bdi_scale = BDI_II;
        }

        for (n = 1; n <= nquestions; ++n) {
            qs.push(L("question") + " " + n);
            fields.push("q" + n);
        }

        pages = [
            {
                title: L("t_bdi"),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('data_collection_only'),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: L('bdi_which_scale')
                    },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair("BDI (1961; BDI-I)", BDI_I),
                            new KeyValuePair("BDI-IA (1978)", BDI_IA),
                            new KeyValuePair("BDI-II (1996)", BDI_II)
                        ],
                        field: "bdi_scale",
                        showInstruction: false,
                        horizontal: true
                    },
                    {
                        type: "QuestionText",
                        text: L('enter_the_answers')
                    },
                    {
                        type: "QuestionMCQGrid",
                        options: bdi_options,
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

module.exports = Bdi;
