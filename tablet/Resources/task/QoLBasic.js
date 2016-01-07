// QoLBasic.js

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
    tablename = "qolbasic",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push(
    {name: 'tto', type: DBCONSTANTS.TYPE_REAL},
    {name: 'rs', type: DBCONSTANTS.TYPE_REAL}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function QoLBasic(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(QoLBasic, taskcommon.BaseTask);
lang.extendPrototype(QoLBasic, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: QoLBasic,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (this.tto !== null && this.rs !== null);
    },

    getSummary: function () {
        var qol_tto = (this.tto === null) ? null : this.tto / 10,
            qol_rs = (this.rs === null) ? null : this.rs / 100;
        return (
            L("qolbasic_tto_q_s") + " " +
            lang.toFixedOrNull(this.tto, 2) + ". " +
            L("qolbasic_rs_q_s") + " " +
            lang.toFixedOrNull(this.rs, 1) + ". " +
            L("qolbasic_mean_qol") + " " +
            lang.toFixedOrNull(lang.mean(qol_tto, qol_rs), 3) +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire;

        pages = [
            {
                title: L("qolbasic_tto_title"),
                elements: [
                    { type: "QuestionText", text: L("qolbasic_tto_q") },
                    {
                        type: "QuestionSlider",
                        field: "tto",
                        min: 0,
                        max: 10,
                        showCurrentValueNumerically: true,
                        numberFormatDecimalPlaces: 1,
                        labels: [
                            { left: 0, text: "0" },
                            { center: "10%", text: "1" },
                            { center: "20%", text: "2" },
                            { center: "30%", text: "3" },
                            { center: "40%", text: "4" },
                            { center: "50%", text: "5" },
                            { center: "60%", text: "6" },
                            { center: "70%", text: "7" },
                            { center: "80%", text: "8" },
                            { center: "90%", text: "9" },
                            { right: 0, text: "10" }
                        ]
                    }
                ]
            },
            {
                title: L("qolbasic_rs_title"),
                elements: [
                    { type: "QuestionText", text: L("qolbasic_rs_q") },
                    {
                        type: "QuestionSlider",
                        field: "rs",
                        min: 0,
                        max: 100,
                        showCurrentValueNumerically: true,
                        numberFormatDecimalPlaces: 0,
                        labels: [
                            { left: 0, text: L("qolbasic_rs_0") },
                            { right: 0, text: L("qolbasic_rs_100") }
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

module.exports = QoLBasic;
