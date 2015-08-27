// show_server_info.js

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

exports.configure = function () { // param sourcewindow ignored

    var storedvars = require('table/storedvars'),
        UICONSTANTS = require('common/UICONSTANTS'),
        DBCONSTANTS = require('common/DBCONSTANTS'),
        Questionnaire = require('questionnaire/Questionnaire'),
        idvariables = [],
        varlist = [
            "serverAddress",
            "serverPort",
            "serverPath",
            "serverTimeoutMs",
            "databaseTitle",
            "idPolicyUpload",
            "idPolicyFinalize",
            "serverCamcopsVersion",
            "lastServerRegistration",
            "lastSuccessfulUpload"
        ],
        i,
        pages,
        tempstore = {},
        v,
        questionnaire;

    for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
        varlist.push("idDescription" + i);
        varlist.push("idShortDescription" + i);
        idvariables.push({
            type: UICONSTANTS.TYPEDVAR_TEXT,
            trim: true,
            field: "idDescription" + i,
            prompt: L('label_idDescription') + " " + i
        });
        idvariables.push({
            type: UICONSTANTS.TYPEDVAR_TEXT,
            trim: true,
            field: "idShortDescription" + i,
            prompt: L('label_idShortDescription') + " " + i
        });
    }
    pages = [
        {
            title: L("t_server_info"),
            config: true,
            elements: [
                { type: "QuestionText", text: L("label_server_address") },
                { type: "QuestionText", field: "serverAddress" },
                { type: "QuestionText", text: L("label_server_port") },
                { type: "QuestionText", field: "serverPort" },
                { type: "QuestionText", text: L("label_server_path") },
                { type: "QuestionText", field: "serverPath" },
                { type: "QuestionText", text: L("label_server_timeout") },
                { type: "QuestionText", field: "serverTimeoutMs" },

                { type: "QuestionHorizontalRule" },

                { type: "QuestionText", text: L("label_last_server_registration") },
                { type: "QuestionText", field: "lastServerRegistration" },
                { type: "QuestionText", text: L("label_last_successful_upload") },
                { type: "QuestionText", field: "lastSuccessfulUpload" },
                { type: "QuestionText", text: L("label_dbtitle") },
                { type: "QuestionText", field: "databaseTitle" },
                { type: "QuestionText", text: L("policy_label_upload") },
                { type: "QuestionText", field: "idPolicyUpload" },
                { type: "QuestionText", text: L("policy_label_finalize") },
                { type: "QuestionText", field: "idPolicyFinalize" },
                { type: "QuestionText", text: L("label_server_camcops_version") },
                { type: "QuestionText", field: "serverCamcopsVersion" },

                { type: "QuestionHorizontalRule" },

                // Make the ID descriptions read-only (saves a lot of potential for ID cock-ups).
                {
                    type: "QuestionTypedVariables",
                    readOnly: true,
                    variables: idvariables
                }
            ]
        }
    ];


    for (i = 0; i < varlist.length; ++i) {
        v = varlist[i];
        tempstore[v] = storedvars[v].getValue();
    }

    questionnaire = new Questionnaire({
        readOnly: true, // always
        pages: pages,
        callbackThis: this,
        fnGetFieldValue: function (fieldname) {
            return tempstore[fieldname];
        },
        fnSetField: function (field, value) {
            tempstore[field] = value;
        },
        okIconAtEnd: true,
        fnFinished: function () {
            // Do nothing
            return;
        }
    });

    questionnaire.open();
};
