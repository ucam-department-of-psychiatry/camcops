// ProgressNote.js

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
    tablename = "progressnote",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: "location", type: DBCONSTANTS.TYPE_TEXT},
    {name: "note", type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function ProgressNote(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(ProgressNote, taskcommon.BaseTask);
lang.extendPrototype(ProgressNote, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: ProgressNote,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (this.note !== null);
    },

    getSummary: function () {
        if (this.note === null) {
            return L('incomplete');
        }
        return (this.note.substring(0, 255) +
                (this.note.length >= 255 ? "..." : ""));
    },

    getDetail: function () {
        return (
            L('clinician_specialty') + ": " + this.clinician_specialty + "\n" +
            L('clinician_name') + ": " + this.clinician_name + "\n" +
            L('clinician_professional_registration') + ": " +
            this.clinician_professional_registration + "\n" +
            L('clinician_post') + ": " + this.clinician_post + "\n" +
            L('clinician_contact_details') + ": " +
            this.clinician_contact_details + "\n" +
            L('location') + ": " + this.location + "\n" +
            L('progressnote_note') + ": " + this.note
        );
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
                title: L('progressnote_title'),
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
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "note",
                                prompt: L("progressnote_note")
                            },
                        ],
                    },
                ],
            },
        ];

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

module.exports = ProgressNote;
