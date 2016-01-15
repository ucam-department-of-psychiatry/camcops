// Pdss.js

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
    tablename = "pdss",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 7;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Pdss(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Pdss, taskcommon.BaseTask);
lang.extendPrototype(Pdss, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Pdss,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _extrastringTaskname: "pdss",
    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // EXTRA STRINGS

    get_questions: function () {
        var arr = [],
            i;
        for (i = 1; i <= nquestions; ++i) {
            arr.push(this.XSTRING("q" + i, "Q" + i));
        }
        return arr;
    },

    // OTHER

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteFromPrefix(this, "q", 1, nquestions);
    },

    getTotalScore: function () {
        return taskcommon.totalScoreFromPrefix(this, "q", 1, nquestions);
    },

    getCompositeScore: function () {
        return taskcommon.meanScoreFromPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (
            "Total " + this.getTotalScore() + "/28, " +
            "composite score " + this.getCompositeScore() + "/4 " +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            KeyValuePair = require('lib/KeyValuePair'),
            elements,
            i,
            j,
            options,
            pages,
            questionnaire;

        elements = [
            {
                type: "QuestionText",
                bold: true,
                text: this.XSTRING('instruction')
            }
        ];
        for (i = 1; i <= nquestions; ++i) {
            options = [];
            for (j = 0; j <= 4; ++j) {
                options.push(
                    new KeyValuePair(this.XSTRING('q' + i + '_option' + j), j)
                );
            }
            elements.push({
                type: "QuestionHorizontalRule"
            });
            elements.push({
                type: "QuestionText",
                text: this.XSTRING('q' + i)
            });
            elements.push({
                type: "QuestionMCQ",
                options: options,
                showInstruction: false,
                field: 'q' + i
            });
        }

        pages = [
            {
                title: L('t_pdss'),
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

module.exports = Pdss;
