// CgiI.js

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
    tablename = "cgi_i",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'q', type: DBCONSTANTS.TYPE_INTEGER}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function CgiI(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(CgiI, taskcommon.BaseTask);
lang.extendPrototype(CgiI, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: CgiI,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (this.q !== null);
    },

    getRatingText: function () {
        if (this.q === null || this.q < 1 || this.q > 7) {
            return "";
        }
        return L('cgi_q2_option' + this.q);
    },

    getSummary: function () {
        return this.getRatingText() + this.isCompleteSuffix();
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            options = [],
            i,
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        for (i = 1; i <= 7; ++i) {
            options.push(new KeyValuePair(L("cgi_q2_option" + i), i));
        }

        pages = [
            self.getClinicianDetailsPage(),  // Clinician info 3/3
            {
                title: L("t_cgi_i"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("cgi_i_q")
                    },
                    {
                        type: "QuestionMCQ",
                        showInstruction: false,
                        field: "q",
                        options: options
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

module.exports = CgiI;
