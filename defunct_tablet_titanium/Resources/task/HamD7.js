// HamD7.js

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
    tablename = "hamd7",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 7,
    NORMAL_N_OPTIONS = 5,
    qlist = [
        {name: "q1", noptions: NORMAL_N_OPTIONS},
        {name: "q2", noptions: NORMAL_N_OPTIONS},
        {name: "q3", noptions: NORMAL_N_OPTIONS},
        {name: "q4", noptions: NORMAL_N_OPTIONS},
        {name: "q5", noptions: NORMAL_N_OPTIONS},
        {name: "q6", noptions: 3}, // this one 3 (0-2), all the rest 5 (0-4)
        {name: "q7", noptions: NORMAL_N_OPTIONS}
    ];

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function HamD7(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(HamD7, taskcommon.BaseTask);
lang.extendPrototype(HamD7, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: HamD7,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    isTaskCrippled: function () {
        return !this.extraStringsPresent();
    },

    // OTHER

    // Scoring
    getTotalScore: function () {
        return taskcommon.totalScoreByPrefix(this, "q", 1, nquestions);
    },

    // Standard task functions
    isComplete: function () {
        return taskcommon.isCompleteByPrefix(this, "q", 1, nquestions);
    },

    getSummary: function () {
        return (L('total_score') + " " + this.getTotalScore() + "/26" +
                this.isCompleteSuffix());
    },

    getDetail: function () {
        var totalscore = this.getTotalScore(),
            severity = (totalscore >= 20 ? L('hamd7_severity_severe')
                         : (totalscore >= 12 ? L('hamd7_severity_moderate')
                            : (totalscore >= 4 ? L('hamd7_severity_mild')
                              : L('hamd7_severity_none')
                              )
                           )
            ),
            msg = "",
            i;
        for (i = 0; i < qlist.length; ++i) {
            msg += (L("hamd7_" + qlist[i].name + "_s") + " " +
                    this[qlist[i].name] + "\n");
        }
        return (msg +
            "\n" +
            this.getSummary() + "\n" +
            "\n" +
            L('hamd7_severity') + " " + severity
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

        function makepage(name, noptions) {
            var options = [],
                j;
            for (j = 0; j < noptions; ++j) {
                options.push(new KeyValuePair(L("hamd7_" + name +
                                                "_option" + j), j));
            }
            return {
                title: L("hamd7_" + name + "_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("hamd7_" + name + "_question")
                    },
                    {
                        type: "QuestionMCQ",
                        field: name,
                        options: options
                    }
                ]
            };
        }
        pages = [ self.getClinicianDetailsPage() ]; // Clinician info 3/3
        for (i = 0; i < qlist.length; ++i) {
            pages.push(makepage(qlist[i].name, qlist[i].noptions));
        }

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

module.exports = HamD7;
