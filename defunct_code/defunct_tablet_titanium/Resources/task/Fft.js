// FFT.js

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
    tablename = "fft",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push(
    {name: 'service', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'rating', type: DBCONSTANTS.TYPE_INTEGER}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function FFT(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(FFT, taskcommon.BaseTask);
lang.extendPrototype(FFT, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: FFT,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (this.rating !== null);
    },

    getSummary: function () {
        return (
            L('rating') + " " + this.getRatingText() +
            this.isCompleteSuffix()
        );
    },

    getRatingText: function () {
        if (this.rating === null || this.rating < 1 || this.rating > 6) {
            return "";
        }
        return L('fft_a' + this.rating);
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            storedvars = require('table/storedvars'),
            options = [],
            i,
            pages,
            questionnaire;

        if (this.id === undefined || this.id === null) {
            // first edit
            this.service = storedvars.defaultClinicianService.getValue();
        }

        for (i = 1; i <= 6; ++i) {
            options.push(new KeyValuePair(L("fft_a" + i), i));
        }

        pages = [{
            title: L("t_fft"),
            clinician: false,
            elements: [
                {
                    type: "QuestionText",
                    bold: true,
                    text: this.service
                },
                {
                    type: "QuestionText",
                    bold: true,
                    text: L("fft_q")
                },
                {
                    type: "QuestionMCQ",
                    field: "rating",
                    mandatory: true,
                    showInstruction: false,
                    options: options
                }
            ]
        }];

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

module.exports = FFT;
