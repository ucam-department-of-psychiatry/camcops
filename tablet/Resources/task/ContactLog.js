// ContactLog.js

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
    tablename = "contactlog",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: "location", type: DBCONSTANTS.TYPE_TEXT},
    {name: "start", type: DBCONSTANTS.TYPE_DATETIME},
    {name: "end", type: DBCONSTANTS.TYPE_DATETIME},
    {name: "patient_contact", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "staff_liaison", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "other_liaison", type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: "comment", type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function ContactLog(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(ContactLog, taskcommon.BaseTask);
lang.extendPrototype(ContactLog, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: ContactLog,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (
            this.clinician_name !== null &&
            // this.location !== null &&
            this.start !== null &&
            this.end !== null &&
            this.patient_contact !== null &&
            this.staff_liaison !== null &&
            this.other_liaison !== null
        );
    },

    getSummary: function () {
        var uifunc = require('lib/uifunc'),
            time_taken_min = null;
        if (this.start !== null && this.end !== null) {
            time_taken_min = this.end.diff(this.start, 'minutes');
        }
        return (
            L('contactlog_start') + " " +
            uifunc.niceDateOrNull(this.start) + ". " +
            L('contactlog_end') + " " +
            uifunc.niceDateOrNull(this.end) +
            " (" + time_taken_min + " " + L('minutes') + ")" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var uifunc = require('lib/uifunc'),
            time_taken_min = null;
        if (this.start !== null && this.end !== null) {
            time_taken_min = this.end.diff(this.start, 'minutes');
        }
        return L('clinician_name') + ": " + this.clinician_name + "\n" +
            L('location') + ": " +
            this.location + "\n" +
            L('contactlog_start') + ": " +
            uifunc.niceDateOrNull(this.start) + "\n" +
            L('contactlog_end') + ": " +
            uifunc.niceDateOrNull(this.end) + "\n" +
            L('contactlog_patient_contact') + ": " +
            uifunc.yesNoNull(this.patient_contact) + "\n" +
            L('contactlog_staff_liaison') + ": " +
            uifunc.yesNoNull(this.staff_liaison) + "\n" +
            L('contactlog_other_liaison') + ": " +
            uifunc.yesNoNull(this.other_liaison) + "\n" +
            L('contactlog_comment') + ": " +
            this.comment + "\n\n" +
            L('contactlog_time_taken') + ": " +
            time_taken_min + " " + L('minutes');
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        pages = [
            {
                title: L('contactlog_title'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "location",
                                prompt: L("location")
                            }
                        ]
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "comment",
                                prompt: L("contactlog_comment")
                            }
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: L('contactlog_start')
                    },
                    {
                        type: "QuestionDateTime",
                        field: "start",
                        showTime: true
                    },
                    {
                        type: "QuestionText",
                        text: L('contactlog_end')
                    },
                    {
                        type: "QuestionDateTime",
                        field: "end",
                        showTime: true
                    },
                    {
                        type: "QuestionBooleanText",
                        text: L('contactlog_patient_contact'),
                        field: "patient_contact",
                        mandatory: true,
                        indicatorOnLeft: true,
                        bigTick: true,
                        valign: UICONSTANTS.ALIGN_CENTRE
                    },
                    {
                        type: "QuestionBooleanText",
                        text: L('contactlog_staff_liaison'),
                        field: "staff_liaison",
                        mandatory: true,
                        indicatorOnLeft: true,
                        bigTick: true,
                        valign: UICONSTANTS.ALIGN_CENTRE
                    },
                    {
                        type: "QuestionBooleanText",
                        text: L('contactlog_other_liaison'),
                        field: "other_liaison",
                        mandatory: true,
                        indicatorOnLeft: true,
                        bigTick: true,
                        valign: UICONSTANTS.ALIGN_CENTRE
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

module.exports = ContactLog;
