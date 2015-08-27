// Gaf.js

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
    tablename = "gaf",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push({ name: "score", type: DBCONSTANTS.TYPE_INTEGER });

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Gaf(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Gaf, taskcommon.BaseTask);
lang.extendPrototype(Gaf, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Gaf,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _crippled: true,

    // OTHER

    // Scoring
    getTotalScore: function () {
        if (this.score === 0) {
            return null;
        }
        return this.score;
    },

    // Standard task functions
    isComplete: function () {
        return (this.score !== null &&
                this.score >= 1 &&
                this.score <= 100);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() +
                " (range 1–100)" + this.isCompleteSuffix());
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            pages,
            questionnaire;

        pages = [
            {
                title: L("t_gaf"),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('data_collection_only'),
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: true,
                        useColumns: true,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "score",
                                prompt: L('gaf_score'),
                                min: 0,
                                max: 100
                            }
                        ]
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

module.exports = Gaf;
