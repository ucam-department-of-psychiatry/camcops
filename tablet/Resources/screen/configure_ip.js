// configure_ip.js

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

/*jslint node: true, newcap: true, plusplus: true */
"use strict";
/*global L */

exports.configure = function () {

    var storedvars = require('table/storedvars'),
        UICONSTANTS = require('common/UICONSTANTS'),
        KeyValuePair = require('lib/KeyValuePair'),
        Questionnaire = require('questionnaire/Questionnaire'),
        ip_options = [
            new KeyValuePair(L('Unknown'), storedvars.USE_TYPE_UNKNOWN),
            new KeyValuePair(L('No'), storedvars.USE_TYPE_FALSE),
            new KeyValuePair(L('Yes'), storedvars.USE_TYPE_TRUE),
        ],
        pages = [
            {
                title: L("t_configure_ip"),
                config: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("label_ip_warning"),
                        warning: true,
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: L("label_ip_disclaimer"),
                        warning: true,
                        italic: true
                    },
                    {
                        type: "QuestionText",
                        text: L("label_ip_preamble")
                    },
                    {
                        type: "QuestionText",
                        text: L("label_ip_clinical"),
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        field: "useClinical",
                        mandatory: true,
                        options: ip_options,
                        showInstruction: false,
                        horizontal: true
                    },

                    {
                        type: "QuestionText",
                        text: L("label_ip_educational"),
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        field: "useEducational",
                        mandatory: true,
                        options: ip_options,
                        showInstruction: false,
                        horizontal: true
                    },

                    {
                        type: "QuestionText",
                        text: L("label_ip_research"),
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        field: "useResearch",
                        mandatory: true,
                        options: ip_options,
                        showInstruction: false,
                        horizontal: true
                    },

                    {
                        type: "QuestionText",
                        text: L("label_ip_commercial"),
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        field: "useCommercial",
                        mandatory: true,
                        options: ip_options,
                        showInstruction: false,
                        horizontal: true
                    },

                ],
            },
        ],
        varlist = [
            "useClinical",
            "useEducational",
            "useResearch",
            "useCommercial",
        ],
        tempstore = {},
        i,
        v,
        questionnaire;

    for (i = 0; i < varlist.length; ++i) {
        v = varlist[i];
        tempstore[v] = storedvars[v].getValue();
    }

    questionnaire = new Questionnaire({
        pages: pages,
        callbackThis: this,
        fnGetFieldValue: function (fieldname) {
            return tempstore[fieldname];
        },
        fnSetField: function (field, value) {
            tempstore[field] = value;
        },
        okIconAtEnd: true,
        fnFinished: function (result) {
            if (result === UICONSTANTS.FINISHED) {
                // Save the changes.
                for (i = 0; i < varlist.length; ++i) {
                    v = varlist[i];
                    storedvars[v].setValue(tempstore[v]);
                }
            } else if (result === UICONSTANTS.ABORTED) {
                // Drop the changes.
                return;
            }
        }
    });

    questionnaire.open();
};
