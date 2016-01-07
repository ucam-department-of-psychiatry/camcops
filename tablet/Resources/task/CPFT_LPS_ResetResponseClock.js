// CPFT_LPS_ResetResponseClock.js

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
    tablename = "cpft_lps_resetresponseclock",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'reset_start_time_to', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'reason', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function CPFT_LPS_ResetResponseClock(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(CPFT_LPS_ResetResponseClock, taskcommon.BaseTask);
lang.extendPrototype(CPFT_LPS_ResetResponseClock, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: CPFT_LPS_ResetResponseClock,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return this.reset_start_time_to && this.reason;
    },

    getSummary: function () {
        var UICONSTANTS = require('common/UICONSTANTS'),
            time = (this.reset_start_time_to ?
                    this.reset_start_time_to.format(UICONSTANTS.TASK_DATETIME_FORMAT) :
                    ""
            );
        return (
            L('cpft_lps_rc_to') + ": " +  time + ". " +
            L('cpft_lps_rc_reason') + ": " + this.reason
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            onlypage,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        onlypage = {
            title: L('t_cpft_lps_resetresponseclock'),
            clinician: true,
            elements: [
                self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                {
                    type: "QuestionText",
                    text: L("cpft_lps_rc_to")
                },
                {
                    type: "QuestionDateTime",
                    field: "reset_start_time_to",
                    showTime: true,
                    mandatory: true
                },
                {
                    type: "QuestionTypedVariables",
                    mandatory: true,
                    useColumns: false,
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                            field: "reason",
                            prompt: L("cpft_lps_rc_reason")
                        }
                    ]
                }
            ]
        };

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: [ onlypage ],
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn
        });
        questionnaire.open();
    }

});

module.exports = CPFT_LPS_ResetResponseClock;
