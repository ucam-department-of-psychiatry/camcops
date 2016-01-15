// Honos65.js

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
    tablename = "honos65",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 12,
    QUESTION8 = "QUESTION8",
    ELEMENTTAG_Q8_PROBLEMTYPE = "q8_pt",
    ELEMENTTAG_Q8_OTHER = "q8_o";

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: 'period_rated', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'q8problemtype', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'q8otherproblem', type: DBCONSTANTS.TYPE_TEXT}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Honos65(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Honos65, taskcommon.BaseTask);
lang.extendPrototype(Honos65, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Honos65,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getScoreSum: function (start, end) {
        var total = 0,
            i,
            value;
        for (i = start; i <= end; ++i) {
            value = this["q" + i];
            if (value !== 9) { // 9 is "not known"
                total += value;
            }
        }
        return total;
    },

    getTotalScore: function () {
        return this.getScoreSum(1, nquestions);
    },

    // Standard task functions
    isComplete: function () {
        if (!taskcommon.isCompleteFromPrefix(this, "q", 1, nquestions)) {
            return false;
        }
        if (this.q8 !== 0 && this.q8 !== 9 && this.q8problemtype === null) {
            return false;
        }
        if (this.q8 !== 0 && this.q8 !== 9 && this.q8problemtype === "J" &&
                this.q8otherproblem === null) {
            return false;
        }
        return this.period_rated !== null;
    },

    getSummary: function () {
        return (
            L('total_score') + " " + this.getTotalScore() + "/48" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        // var totalscore = this.getTotalScore();
        return (
            taskcommon.valueDetail(this, "honos65_q", "_s", " ", "q", 1, 8) +
            L("honos65_q8problemtype_s") + " " + this.q8problemtype + "\n" +
            L("honos65_q8otherproblem_s") + " " + this.q8otherproblem + "\n" +
            taskcommon.valueDetail(this, "honos65_q", "_s", " ", "q", 9,
                                   nquestions) +
            "\n" +
            this.getSummary() + "\n"
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            pages,
            questionnaire,
            i;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function makepage(q) {
            var options = [],
                title = L('honos65_title_prefix') + q,
                elements,
                pageTag = "",
                j;
            for (j = 0; j <= 4; ++j) {
                options.push(new KeyValuePair(L("honos65_q" + q +
                                                "_option" + j), j));
            }
            options.push(new KeyValuePair(L("honos_option9"), 9)); // common to all
            elements = [
                {
                    type: "QuestionText",
                    text: L("honos65_q" + q)
                },
                {
                    type: "QuestionMCQ",
                    field: "q" + q,
                    options: options
                }
            ];
            pageTag = "";
            if (q === 8) { // ugly :)
                pageTag = QUESTION8;
                elements.push(
                    {
                        type: "QuestionText",
                        text: L("honos65_q8problemtype_prompt")
                    },
                    {
                        elementTag: ELEMENTTAG_Q8_PROBLEMTYPE,
                        type: "QuestionMCQ",
                        field: "q8problemtype",
                        options: [
                            new KeyValuePair(L("honos65_q8problemtype_option_a"), "A"),
                            new KeyValuePair(L("honos65_q8problemtype_option_b"), "B"),
                            new KeyValuePair(L("honos65_q8problemtype_option_c"), "C"),
                            new KeyValuePair(L("honos65_q8problemtype_option_d"), "D"),
                            new KeyValuePair(L("honos65_q8problemtype_option_e"), "E"),
                            new KeyValuePair(L("honos65_q8problemtype_option_f"), "F"),
                            new KeyValuePair(L("honos65_q8problemtype_option_g"), "G"),
                            new KeyValuePair(L("honos65_q8problemtype_option_h"), "H"),
                            new KeyValuePair(L("honos65_q8problemtype_option_i"), "I"),
                            new KeyValuePair(L("honos65_q8problemtype_option_j"), "J")
                        ]
                    },
                    {
                        elementTag: ELEMENTTAG_Q8_OTHER,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "q8otherproblem",
                                prompt: L("honos65_q8otherproblem_prompt"),
                                hint: L("honos65_q8otherproblem_hint")
                            }
                        ]
                    }
                );
            }
            return {
                title: title,
                clinician: true,
                elements: elements,
                pageTag: pageTag
            };
        }
        pages = [
            self.getClinicianDetailsPage(), // Clinician info 3/3
            {
                title: L("honos65_firstpage_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionTypedVariables",
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "period_rated",
                                prompt: L("honos_period_rated"),
                                hint: L("honos_period_rated")
                            }
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: L("honos65_instructions")
                    }
                ]
            }
        ];
        for (i = 1; i <= nquestions; ++i) {
            pages.push(makepage(i));
        }

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: function (result, editing_time_s) {
                self.defaultFinishedFn(result, editing_time_s);
                questionnaire = null; // for garbage collection, since we have closures referring to questionnaire
            },
            fnShowNext: function (currentPage, pageTag) {
                if (pageTag === QUESTION8) {
                    if ((self.q8 === 0 || self.q8 === 9) &&
                            self.q8problemtype !== null) {
                        // Force the problem type to be blank
                        self.q8problemtype = null;
                        questionnaire.setFromFieldByTag(ELEMENTTAG_Q8_PROBLEMTYPE);
                    }
                    questionnaire.setMandatoryByTag(ELEMENTTAG_Q8_PROBLEMTYPE,
                                                    self.q8 !== null &&
                                                    self.q8 !== 0 &&
                                                    self.q8 !== 9);
                    questionnaire.setMandatoryByTag(ELEMENTTAG_Q8_OTHER,
                                                    self.q8problemtype === "J");
                }
                return { care: false };
            }
        });
        questionnaire.open();
    }

});

module.exports = Honos65;
