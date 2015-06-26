// IRAC.js

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
    tablename = "irac",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push(
    {name: 'aim', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'achieved', type: DBCONSTANTS.TYPE_INTEGER}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function IRAC(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(IRAC, taskcommon.BaseTask);
lang.extendPrototype(IRAC, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: IRAC,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (this.aim !== null && this.achieved !== null);
    },

    getSummary: function () {
        return (
            L('irac_q_aim') + " " + this.aim +
            " -- " +
            L('irac_q_achieved') + " " + this.getAchievedText() +
            this.isCompleteSuffix()
        );
    },

    getAchievedText: function () {
        if (this.achieved === null || this.achieved < 0 || this.achieved > 2) {
            return "?";
        }
        return L('irac_achieved_' + this.achieved);
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            options_aim = [],
            options_achieved = [],
            i,
            pages,
            questionnaire,
            s;

        for (i = 1; i <= 10; ++i) {
            s = L("irac_aim_" + i);
            options_aim.push(new KeyValuePair(s, s));
        }
        for (i = 0; i <= 2; ++i) {
            options_achieved.push(new KeyValuePair(L("irac_achieved_" + i),
                                                   i));
        }

        pages = [{
            title: L("t_irac"),
            clinician: false,
            elements: [
                {
                    type: "QuestionText",
                    bold: true,
                    text: L("irac_q_aim"),
                },
                {
                    type: "QuestionMCQ",
                    field: "aim",
                    mandatory: true,
                    showInstruction: false,
                    horizontal: true,
                    asTextButton: true,
                    options: options_aim,
                },
                {
                    type: "QuestionText",
                    bold: true,
                    text: L("irac_q_achieved"),
                },
                {
                    type: "QuestionMCQ",
                    field: "achieved",
                    mandatory: true,
                    showInstruction: false,
                    horizontal: true,
                    asTextButton: true,
                    options: options_achieved,
                },
            ],
        }];

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

module.exports = IRAC;
