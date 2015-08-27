// Cgi.js

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
    // TABLE
    tablename = "cgi",
    fieldlist = dbcommon.standardTaskFields();

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
fieldlist.push(
    {name: 'q1', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q2', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q3t', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q3s', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'q3', type: DBCONSTANTS.TYPE_INTEGER}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Cgi(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Cgi, taskcommon.BaseTask);
lang.extendPrototype(Cgi, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Cgi,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    setEfficacyIndex: function () {
        if (this.q3t === null ||
                this.q3t <= 0 ||
                this.q3t > 4 ||
                this.q3s === null ||
                this.q3s <= 0 ||
                this.q3s > 4) {
            this.q3 = 0; // not assessed, or silly values
        } else {
            this.q3 = (this.q3t - 1) * 4 + this.q3s;
            // that's the CGI algorithm for the efficacy index
        }
    },

    getTotalScore: function () {
        return this.q1 + this.q2 + this.q3;
    },

    // Standard task functions
    isComplete: function () {
        if (this.q1 === null ||
                this.q2 === null ||
                this.q3t === null ||
                this.q3s === null) {
            return false;
        }
        return true;
    },

    getSummary: function () {
        return (
            L('total_score') + " " + this.getTotalScore() + "/30" +
            ": " + L('cgi_severity') + " " + this.q1 + "/7, " +
            L('cgi_improvement') + " " + this.q2 + "/7, " +
            L('cgi_efficacy') + " " + this.q3 + "/16" +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        return (
            L('cgi_q1_s') + " " + this.q1 + "\n" +
            L('cgi_q2_s') + " " + this.q2 + "\n" +
            L('cgi_q3t_s') + " " + this.q3t + "\n" +
            L('cgi_q3s_s') + " " + this.q3s + "\n" +
            L('cgi_q3_s') + " " + this.q3 + "\n" +
            "\n" +
            this.getSummary()
        );
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        function makepage(qname, lastoption) {
            var options = [],
                j;
            for (j = 0; j <= lastoption; ++j) {
                options.push(new KeyValuePair(L("cgi_" + qname +
                                                "_option" + j), j));
            }
            return {
                title: L("cgi_" + qname + "_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("cgi_" + qname + "_question")
                    },
                    {
                        type: "QuestionMCQ",
                        field: qname,
                        options: options
                    }
                ]
            };
        }

        pages = [ self.getClinicianDetailsPage() ]; // Clinician info 3/3
        pages.push(makepage("q1", 7));
        pages.push(makepage("q2", 7));
        pages.push(makepage("q3t", 4));
        pages.push(makepage("q3s", 4));

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: function (field, value) {
                self[field] = value;
                self.setEfficacyIndex();
                self.dbstore();
            },
            fnFinished: self.defaultFinishedFn
        });
        questionnaire.open();
    }

});

module.exports = Cgi;
