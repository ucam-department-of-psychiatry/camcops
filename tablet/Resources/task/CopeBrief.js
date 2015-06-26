// CopeBrief.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "cope_brief",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 28,
    RELATIONSHIP_OTHER_CODE = 0,
    RELATIONSHIPS_FIRST = 0,
    RELATIONSHIPS_FIRST_NON_OTHER = 1,
    RELATIONSHIPS_LAST = 9,
    ET_RELATIONSHIP = "rel",
    ET_RELATIONSHIP_OTHER = "rel_other";

fieldlist.push(
    {name: 'completed_by_patient', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'completed_by', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'relationship_to_patient', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'relationship_to_patient_other', type: DBCONSTANTS.TYPE_TEXT}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

/*
    Individual items are scored 0–3 (as in Carver 1997 PMID 16250744), not 1–4
    (as in http://www.psy.miami.edu/faculty/ccarver/sclBrCOPE.html).
*/

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function CopeBrief(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(CopeBrief, taskcommon.BaseTask);
lang.extendPrototype(CopeBrief, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: CopeBrief,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    isCompleteResponder: function () {
        if (this.completed_by_patient === null) {
            return false;
        }
        if (this.completed_by_patient) {
            return true;
        }
        if (!this.completed_by || this.relationship_to_patient === null) {
            return false;
        }
        if (this.relationship_to_patient === RELATIONSHIP_OTHER_CODE &&
                !this.relationship_to_patient_other) {
            return false;
        }
        return true;
    },

    getResponder: function () {
        if (this.completed_by_patient === null) {
            return "?";
        }
        if (this.completed_by_patient) {
            return "Patient";
        }
        var c = this.completed_by || "?",
            r = "?";
        if (this.relationship_to_patient >= RELATIONSHIPS_FIRST &&
                this.relationship_to_patient <= RELATIONSHIPS_LAST) {
            r = L('copebrief_relationship_' + this.relationship_to_patient);
        }
        return c + " (" + r + ")";
    },

    // Standard task functions
    isComplete: function () {
        return this.isCompleteResponder() &&
            taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return this.getResponder() + this.isCompleteSuffix();
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            elements1,
            elements2,
            pages,
            questionnaire,
            main_options = [
                new KeyValuePair(L('copebrief_a0'), 0),
                new KeyValuePair(L('copebrief_a1'), 1),
                new KeyValuePair(L('copebrief_a2'), 2),
                new KeyValuePair(L('copebrief_a3'), 3),
            ],
            relationship_options = [],
            i;

        for (i = RELATIONSHIPS_FIRST_NON_OTHER; i <= RELATIONSHIPS_LAST; ++i) {
            relationship_options.push(
                new KeyValuePair(L('copebrief_relationship_' + i), i)
            );
        }
        i = RELATIONSHIP_OTHER_CODE;
        relationship_options.push(
            new KeyValuePair(L('copebrief_relationship_' + i), i)
        );

        elements1 = [
            {
                type: "QuestionText",
                text: L('copebrief_q_patient') + " (" + this.getPatientName() +
                    ")?",
            },
            {
                type: "QuestionMCQ",
                field: "completed_by_patient",
                showInstruction: false,
                horizontal: true,
                mandatory: true,
                options: taskcommon.OPTIONS_YES_NO_BOOLEAN,
            },
            {
                elementTag: ET_RELATIONSHIP,
                visible: false,
                type: "QuestionTypedVariables",
                mandatory: false,
                useColumns: false,
                variables: [
                    {
                        type: UICONSTANTS.TYPEDVAR_TEXT,
                        field: "completed_by",
                        prompt: L('copebrief_q_completedby')
                    },
                ],
            },
            {
                elementTag: ET_RELATIONSHIP,
                visible: false,
                type: "QuestionText",
                text: L('copebrief_q_relationship'),
            },
            {
                elementTag: ET_RELATIONSHIP,
                visible: false,
                type: "QuestionMCQ",
                field: "relationship_to_patient",
                showInstruction: false,
                mandatory: true,
                options: relationship_options,
            },

            {
                elementTag: ET_RELATIONSHIP_OTHER,
                visible: false,
                type: "QuestionTypedVariables",
                mandatory: false,
                useColumns: false,
                variables: [
                    {
                        type: UICONSTANTS.TYPEDVAR_TEXT,
                        field: "relationship_to_patient_other",
                        prompt: L('copebrief_q_relationship_other')
                    },
                ],
            },
        ];

        elements2 = [
            {
                type: "QuestionText",
                bold: true,
                text: L('copebrief_instructions'),
            },
        ];
        for (i = 1; i <= nquestions; ++i) {
            elements2.push({
                type: "QuestionHorizontalRule",
            });
            elements2.push({
                type: "QuestionText",
                text: "Q" + i + ". " + L("copebrief_q" + i),
                bold: true,
            });
            elements2.push({
                type: "QuestionMCQ",
                field: "q" + i,
                showInstruction: false,
                mandatory: true,
                options: main_options,
            });
        }

        pages = [
            {
                title: L('t_copebrief') + " (1/2)",
                clinician: false,
                elements: elements1,
            },
            {
                title: L('t_copebrief') + " (2/2)",
                clinician: false,
                elements: elements2,
            },
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn,
            fnShowNext: function (currentPage, pageTag) {
                if (currentPage === 0) {
                    questionnaire.setMandatoryAndVisibleByTag(
                        ET_RELATIONSHIP,
                        !self.completed_by_patient &&
                            self.completed_by_patient !== null
                    );
                    questionnaire.setMandatoryAndVisibleByTag(
                        ET_RELATIONSHIP_OTHER,
                        self.relationship_to_patient === RELATIONSHIP_OTHER_CODE
                    );
                    return {
                        care: true,
                        showNext: self.isCompleteResponder()
                    };
                }
                return { care: false };
            },
        });

        questionnaire.open();
    },

});

module.exports = CopeBrief;
