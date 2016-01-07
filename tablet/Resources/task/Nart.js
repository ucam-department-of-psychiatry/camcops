// Nart.js

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
    WORDLIST = [
        "chord",
        "ache",
        "depot",
        "aisle",
        "bouquet",
        "psalm",
        "capon",
        "deny",
        "nausea",
        "debt",
        "courteous",
        "rarefy",
        "equivocal",
        "naive", // accent required
        "catacomb",
        "gaoled",
        "thyme",
        "heir",
        "radix",
        "assignate",
        "hiatus",
        "subtle",
        "procreate",
        "gist",
        "gouge",
        "superfluous",
        "simile",
        "banal",
        "quadruped",
        "cellist",
        "facade", // accent required
        "zealot",
        "drachm",
        "aeon",
        "placebo",
        "abstemious",
        "detente", // accent required
        "idyll",
        "puerperal",
        "aver",
        "gauche",
        "topiary",
        "leviathan",
        "beatify",
        "prelate",
        "sidereal",
        "demesne",
        "syncope",
        "labile",
        "campanile"
    ],
    ACCENTED_WORDLIST = WORDLIST.slice(0), // clone
    IQ_DP = 1,
    tablename = "nart",
    fieldlist = dbcommon.standardTaskFields(),
    i;

ACCENTED_WORDLIST[ACCENTED_WORDLIST.indexOf("naive")] = "naïve";
ACCENTED_WORDLIST[ACCENTED_WORDLIST.indexOf("facade")] = "façade";
ACCENTED_WORDLIST[ACCENTED_WORDLIST.indexOf("detente")] = "détente";
// toUpperCase() deals with accents fine

fieldlist.push.apply(fieldlist, dbcommon.CLINICIAN_FIELDSPECS); // Clinician info 1/3
for (i = 0; i < WORDLIST.length; ++i) {
    fieldlist.push(
        {name: WORDLIST[i], type: DBCONSTANTS.TYPE_BOOLEAN}
    );
}

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Nart(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Nart, taskcommon.BaseTask);
lang.extendPrototype(Nart, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Nart,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Scoring
    getErrors: function () {
        var e = 0,
            i;
        for (i = 0; i < WORDLIST.length; ++i) {
            if (this[WORDLIST[i]] !== null && !this[WORDLIST[i]]) {
                ++e;
            }
        }
        return e;
    },

    getFullScaleIQ: function () {
        if (!this.isComplete()) {
            return null;
        }
        return 127.7 - 0.826 * this.getErrors();
    },

    getVerbalIQ: function () {
        if (!this.isComplete()) {
            return null;
        }
        return 129.0 - 0.919 * this.getErrors();
    },

    getPerformanceIQ: function () {
        if (!this.isComplete()) {
            return null;
        }
        return 123.5 - 0.645 * this.getErrors();
    },

    // Standard task functions
    isComplete: function () {
        var i;
        for (i = 0; i < WORDLIST.length; ++i) {
            if (this[WORDLIST[i]] === null) {
                return false;
            }
        }
        return true;
    },

    getSummary: function () {
        return (
            L('total_errors') + ": " +
            this.getErrors() + "/" + WORDLIST.length + ". " +
            L('nart_full_scale_iq') + ": " +
            lang.toFixedOrNull(this.getFullScaleIQ(), IQ_DP) + ". " +
            L('nart_verbal_iq') + ": " +
            lang.toFixedOrNull(this.getVerbalIQ(), IQ_DP) + ". " +
            L('nart_performance_iq') + ": " +
            lang.toFixedOrNull(this.getPerformanceIQ(), IQ_DP) + "." +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var msg = L('nart_words_correct_q') + "\n\n",
            i;
        for (i = 0; i < WORDLIST.length; ++i) {
            msg += WORDLIST[i] + ": " + this[WORDLIST[i]] + "\n";
        }
        return msg + "\n" + this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            options_corr_incorr = taskcommon.OPTIONS_INCORRECT_CORRECT_BOOLEAN,
            table_elements = [],
            i,
            pages,
            questionnaire;

        self.setDefaultClinicianVariablesAtFirstUse(readOnly); // Clinician info 2/3

        for (i = 0; i < WORDLIST.length; ++i) {
            table_elements.push({
                type: "QuestionText",
                text: ACCENTED_WORDLIST[i].toUpperCase(),
                bold: true,
                right: UICONSTANTS.BIGSPACE,
                center: { y: '50%' }
            });
            table_elements.push({
                type: "QuestionMCQ",
                options: options_corr_incorr,
                field: WORDLIST[i],
                showInstruction: false,
                horizontal: true
            });
        }

        pages = [
            {
                title: L('t_nart'),
                clinician: true,
                elements: [
                    self.getClinicianQuestionnaireBlock(), // Clinician info 3/3
                    { type: "QuestionText", text: L('nart_instructions') },
                    {
                        type: "ContainerTable",
                        columns: 2,
                        elements: table_elements
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

module.exports = Nart;
