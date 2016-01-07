// Zbi12.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "zbi12",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 12;

fieldlist.push(
    {name: 'responder_name', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'responder_relationship', type: DBCONSTANTS.TYPE_TEXT}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Zbi12(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Zbi12, taskcommon.BaseTask);
lang.extendPrototype(Zbi12, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Zbi12,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "ZBI-12",
    isTaskCrippled: function () {
        var extrastrings = require('table/extrastrings');
        return !extrastrings.task_exists(this._extrastringTaskname);
    },

    // EXTRA STRINGS

    XSTRING: function (name, defaultvalue) {
        defaultvalue = defaultvalue || name;
        return extrastrings.get(EXTRASTRING_TASKNAME, name,
                                "[ZBI: " + defaultvalue + "]");
    },

    get_questions: function () {
        var arr = [],
            i;
        for (i = 1; i <= nquestions; ++i) {
            arr.push(this.XSTRING("q" + i, "Q" + i));
        }
        return arr;
    },

    // OTHER

    isCompleteResponder: function () {
        return this.responder_name && this.responder_relationship;
    },

    isCompleteQuestions: function () {
        return taskcommon.isComplete(this, "q", 1, nquestions);
    },

    getRelationship: function () {
        return this.responder_relationship || "";
    },

    // Standard task functions
    isComplete: function () {
        return this.isCompleteResponder() && this.isCompleteQuestions();
    },

    getSummary: function () {
        return this.getRelationship() + this.isCompleteSuffix();
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            elements,
            pages,
            questionnaire;

        elements = [
            {
                type: "QuestionTypedVariables",
                mandatory: true,
                useColumns: false,
                variables: [
                    {
                        type: UICONSTANTS.TYPEDVAR_TEXT,
                        field: "responder_name",
                        prompt: L('zbi_q_responder_name')
                    },
                    {
                        type: UICONSTANTS.TYPEDVAR_TEXT,
                        field: "responder_relationship",
                        prompt: L('zbi_q_responder_relationship')
                    }
                ]
            },
            {
                type: "QuestionText",
                bold: true,
                text: this.XSTRING('instruction')
            },
            {
                type: "QuestionMCQGrid",
                options: [
                    new KeyValuePair(L('zbi_a0'), 0),
                    new KeyValuePair(L('zbi_a1'), 1),
                    new KeyValuePair(L('zbi_a2'), 2),
                    new KeyValuePair(L('zbi_a3'), 3),
                    new KeyValuePair(L('zbi_a4'), 4)
                ],
                questions: this.get_questions(),
                fields: taskcommon.stringArrayFromSequence("q", 1, nquestions),
                optionsWidthTogether: '65%'
            }
        ];

        pages = [
            {
                title: L('t_zbi12'),
                clinician: false,
                elements: elements
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

module.exports = Zbi12;
