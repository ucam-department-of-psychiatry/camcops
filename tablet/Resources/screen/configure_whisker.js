// configure_whisker.js

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

exports.configure = function () { // sourcewindow parameter not used

    var storedvars = require('table/storedvars'),
        UICONSTANTS = require('common/UICONSTANTS'),
        Questionnaire = require('questionnaire/Questionnaire'),
        varlist = [
            "whiskerHost",
            "whiskerPort",
            "whiskerTimeoutMs",
        ],
        i,
        pages,
        tempstore = {},
        v,
        questionnaire;

    pages = [
        {
            title: L("whisker_configure"),
            config: true,
            elements: [
                {
                    type: "QuestionTypedVariables",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "whiskerHost",
                            prompt: L("label_whisker_host"),
                            hint: L('hint_whisker_host'),
                            mandatory: true
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            field: "whiskerPort",
                            prompt: L("label_whisker_port"),
                            hint: L('hint_whisker_port'),
                            min: 0
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            field: "whiskerTimeoutMs",
                            prompt: L("label_server_timeout"),
                            hint: L('hint_server_timeout'),
                            min: 0
                        },
                    ],
                },
            ],
        },
    ];


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
                for (i = 0; i < varlist.length; ++i) {
                    v = varlist[i];
                    storedvars[v].setValue(tempstore[v]);
                }
            }
        },
    });

    questionnaire.open();
};
