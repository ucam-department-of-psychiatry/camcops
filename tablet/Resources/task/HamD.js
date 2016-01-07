// HamD.js

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
    tablename = "hamd",
    fieldlist = dbcommon.standardTaskFields(),
    nscoredquestions = 17,
    qlist = [
        {name: "q1", noptions: 5, mandatory: true },
        {name: "q2", noptions: 5, mandatory: true },
        {name: "q3", noptions: 5, mandatory: true },
        {name: "q4", noptions: 3, mandatory: true },
        {name: "q5", noptions: 3, mandatory: true },
        {name: "q6", noptions: 3, mandatory: true },
        {name: "q7", noptions: 5, mandatory: true },
        {name: "q8", noptions: 5, mandatory: true },
        {name: "q9", noptions: 5, mandatory: true },
        {name: "q10", noptions: 5, mandatory: true },
        {name: "q11", noptions: 5, mandatory: true },
        {name: "q12", noptions: 3, mandatory: true },
        {name: "q13", noptions: 3, mandatory: true },
        {name: "q14", noptions: 3, mandatory: true },
        {name: "q15", noptions: 5, mandatory: true },
        {name: "whichq16", noptions: 2, mandatory: true },
        {name: "q16a", noptions: 4, mandatory: true },
        {name: "q16b", noptions: 4, mandatory: true },
        {name: "q17", noptions: 3, mandatory: true },
        {name: "q18a", noptions: 3, mandatory: false },
        {name: "q18b", noptions: 3, mandatory: false },
        {name: "q19", noptions: 5, mandatory: false },
        {name: "q20", noptions: 4, mandatory: false },
        {name: "q21", noptions: 3, mandatory: false }
    ];

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, 15,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: 'whichq16', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q16a', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q16b', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q17', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q18a', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q18b', type: DBCONSTANTS.TYPE_INTEGER}
);
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 19, 21,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function HamD(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(HamD, taskcommon.BaseTask);
lang.extendPrototype(HamD, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: HamD,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getTotalScore: function () {
        var total = 0,
            rawscore,
            i;
        for (i = 1; i <= nscoredquestions; ++i) {
            if (i === 16) {
                if (this.whichq16 === 0) {
                    rawscore = this.q16a;
                } else {
                    rawscore = this.q16b;
                }
                if (rawscore !== 3) {
                    // For weight questions, '3' means 'not measured' and is
                    // not scored.
                    total += rawscore;
                }
            } else {
                total += this["q" + i];
            }
        }
        return total;
    },

    // Standard task functions
    isComplete: function () {
        var i;
        if (this.q1 === null || this.q9 === null || this.q10 === null) {
            // Always need these three.
            return false;
        }
        if (this.q1 === 0) {
            // Special limited-information completeness
            return true;
        }
        if (this.q2 !== null && this.q3 !== null &&
                (this.q2 + this.q3 === 0)) {
            // Special limited-information completeness
            return true;
        }
        // Otherwise, any null values cause problems
        for (i = 1; i <= nscoredquestions; ++i) {
            if (this.whichq16 === null) {
                return false;
            }
            if (i === 16) {
                if ((this.whichq16 === 0 && this.q16a === null) ||
                        (this.whichq16 === 1 && this.q16b === null)) {
                    return false;
                }
            } else {
                if (this["q" + i] === null) {
                    return false;
                }
            }
        }
        return true;
    },

    getSummary: function () {
        return (L('hamd_total_score') + " " + this.getTotalScore() + "/52" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var totalscore = this.getTotalScore(),
            severity = (totalscore > 23 ? L('hamd_severity_verysevere')
                        : (totalscore >= 19 ? L('hamd_severity_severe')
                           : (totalscore >= 14 ? L('hamd_severity_moderate')
                              : (totalscore >= 8 ? L('hamd_severity_mild')
                                : L('hamd_severity_none')
                                )
                             )
                          )
            ),
            msg = "",
            i;
        for (i = 0; i < qlist.length; ++i) {
            msg += (L("hamd_" + qlist[i].name + "_s") + " " +
                    this[qlist[i].name] + "\n");
        }
        return (msg +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('hamd_severity') + " " + severity
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire,
            i;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function makepage(props) {
            var options = [],
                j;
            for (j = 0; j < props.noptions; ++j) {
                options.push(new KeyValuePair(L("hamd_" + props.name +
                                                "_option" + j), j));
            }
            return {
                title: L("hamd_" + props.name + "_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("hamd_" + props.name + "_question")
                    },
                    {
                        type: "QuestionMCQ",
                        field: props.name,
                        mandatory: props.mandatory,
                        options: options
                    }
                ]
            };
        }
        pages = [ self.getClinicianDetailsPage() ]; // Clinician info 3/3
        for (i = 0; i < qlist.length; ++i) {
            pages.push(makepage(qlist[i]));
        }

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn,
            fnNextPage: function (pageId_zero_based) {
                if (pageId_zero_based === 16) { // the "whichq16" one
                    return self.whichq16 === 0 ? 17 : 18;
                }
                if (pageId_zero_based === 17 || pageId_zero_based === 18) {
                    // the weight ones
                    return 19;
                }
                return pageId_zero_based + 1;
                // by default, move to the next question
            },
            fnPreviousPage: function (pageId_zero_based) {
                if (pageId_zero_based === 17 || pageId_zero_based === 18) {
                    // one of the weight ones
                    return 16; // go to the "whichq16" one
                }
                if (pageId_zero_based === 19) {
                    // the one after the weight one
                    return self.whichq16 === 0 ? 17 : 18;
                }
                return pageId_zero_based - 1;
                // by default, move to the previous question
            }
        });

        questionnaire.open();
    }

});

module.exports = HamD;
