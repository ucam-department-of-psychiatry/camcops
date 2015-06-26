// configure_server.js

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

    var uifunc = require('lib/uifunc'),
        storedvars = require('table/storedvars'),
        UICONSTANTS = require('common/UICONSTANTS'),
        DBCONSTANTS = require('common/DBCONSTANTS'),
        taskcommon = require('lib/taskcommon'),
        Questionnaire = require('questionnaire/Questionnaire'),
        yn_options = taskcommon.OPTIONS_YES_NO_BOOLEAN,
        idvariables = [],
        varlist = [
            "serverAddress",
            "serverPort",
            "serverPath",
            "serverTimeoutMs",
            "validateSSLCertificates",
            "storeServerPassword",
            "sendAnalytics",
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
            title: L("t_configure_server"),
            config: true,
            elements: [
                {
                    type: "QuestionTypedVariables",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "serverAddress",
                            prompt: L("label_server_address"),
                            hint: L('hint_server_address'),
                            mandatory: true
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            field: "serverPort",
                            prompt: L("label_server_port"),
                            hint: L('hint_server_port'),
                            min: 0
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "serverPath",
                            prompt: L("label_server_path"),
                            hint: L('hint_server_path'),
                            mandatory: true
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            field: "serverTimeoutMs",
                            prompt: L("label_server_timeout"),
                            hint: L('hint_server_timeout'),
                            min: 0
                        },
                    ],

                },
                {
                    type: "QuestionText",
                    text: L("label_validate_ssl_certificates")
                },
                {
                    type: "QuestionMCQ",
                    field: "validateSSLCertificates",
                    mandatory: true,
                    options: yn_options,
                    showInstruction: false,
                    horizontal: true
                },
                {
                    type: "QuestionText",
                    text: L("label_store_server_password")
                },
                {
                    type: "QuestionMCQ",
                    field: "storeServerPassword",
                    mandatory: true,
                    options: yn_options,
                    showInstruction: false,
                    horizontal: true
                },
                {
                    type: "QuestionHorizontalRule"
                },
                {
                    type: "QuestionText",
                    text: L("label_send_analytics")
                },
                {
                    type: "QuestionMCQ",
                    field: "sendAnalytics",
                    mandatory: true,
                    options: yn_options,
                    showInstruction: false,
                    horizontal: true
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
            var netcore,
                serverDetailsChanged = (
                    tempstore.serverAddress !==
                        storedvars.serverAddress.getValue() ||
                    tempstore.serverPort !==
                        storedvars.serverPort.getValue() ||
                    tempstore.serverPath !==
                        storedvars.serverPath.getValue()
                );
            if (result === UICONSTANTS.FINISHED) {
                // Wipe the stored password?
                if (!tempstore.storeServerPassword) {
                    storedvars.serverPasswordObscured.setValue(null);
                }
                // Save the changes.
                for (i = 0; i < varlist.length; ++i) {
                    v = varlist[i];
                    storedvars[v].setValue(tempstore[v]);
                }
                if (serverDetailsChanged) {
                    netcore = require('lib/netcore');
                    netcore.clearTempServerPassword();
                    uifunc.alert(L('registration_advised'),
                                 L('registration_advised_title'));
                }
            } else if (result === UICONSTANTS.ABORTED) {
                // Drop the changes.
                return;
            }
        },
    });

    questionnaire.open();
};
