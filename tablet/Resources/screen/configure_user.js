// configure_user.js

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
/*global Titanium, L */

exports.configure = function () {

    var storedvars = require('table/storedvars'),
        UICONSTANTS = require('common/UICONSTANTS'),
        taskcommon = require('lib/taskcommon'),
        Questionnaire = require('questionnaire/Questionnaire'),
        rnc_crypto = require('lib/rnc_crypto'),
        doingPassword = storedvars.storeServerPassword.getValue(),
        yn_options = taskcommon.OPTIONS_YES_NO_BOOLEAN,
        passwordElement,
        tempstore,
        pages,
        questionnaire,
        i,
        v,
        varlist = [
            "deviceFriendlyName",
            "serverUser",
            // password has special handling
            "defaultClinicianSpecialty",
            "defaultClinicianName",
            "defaultClinicianProfessionalRegistration",
            "defaultClinicianPost",
            "defaultClinicianService",
            "defaultClinicianContactDetails",
            "offerUploadAfterEdit",
            "multilineTextFixedHeight",
            "multilineDefaultNLines",
        ];

    if (doingPassword) {
        passwordElement = {
            type: "QuestionTypedVariables",
            variables: [ {
                type: UICONSTANTS.TYPEDVAR_TEXT,
                passwordMask: true,
                trim: true,
                field: "tempPassword",
                prompt: L("label_server_password"),
                hint: L('hint_server_password'),
                mandatory: true
            } ],
        };
        tempstore = {
            tempPassword: rnc_crypto.retrieveObscuredPassword(
                storedvars.serverPasswordObscured.getValue()
            ),
        };
    } else {
        passwordElement = {
            type: "QuestionText",
            text: L("label_password_not_being_stored"),
            italic: true,
        };
        tempstore = {};
    }
    pages = [
        {
            title: L("t_configure_user"),
            config: true,
            elements: [
                {
                    type: "QuestionTypedVariables",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "deviceFriendlyName",
                            prompt: L("label_device_friendly_name"),
                            hint: L('hint_device_friendly_name')
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "serverUser",
                            prompt: L("label_server_user"),
                            hint: L('hint_server_user'),
                            mandatory: true
                        },
                    ],
                },
                passwordElement,
                { type: "QuestionHorizontalRule" },
                {
                    type: "QuestionTypedVariables",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "defaultClinicianSpecialty",
                            prompt: L("label_default_clinician_specialty"),
                            hint: L('hint_default_clinician_specialty'),
                            mandatory: false
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "defaultClinicianName",
                            prompt: L("label_default_clinician_name"),
                            hint: L('hint_default_clinician_name'),
                            mandatory: false
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "defaultClinicianProfessionalRegistration",
                            prompt: L("label_default_clinician_professional_registration"),
                            hint: L('hint_default_clinician_professional_registration'),
                            mandatory: false
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "defaultClinicianPost",
                            prompt: L("label_default_clinician_post"),
                            hint: L('hint_default_clinician_post'),
                            mandatory: false
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "defaultClinicianService",
                            prompt: L("label_default_clinician_service"),
                            hint: L('hint_default_clinician_service'),
                            mandatory: false
                        },
                        {
                            type: UICONSTANTS.TYPEDVAR_TEXT,
                            trim: true,
                            field: "defaultClinicianContactDetails",
                            prompt: L("label_default_clinician_contact_details"),
                            hint: L('hint_default_clinician_contact_details'),
                            mandatory: false
                        },
                    ],
                },
                { type: "QuestionHorizontalRule" },
                {
                    type: "QuestionText",
                    text: L('offer_upload_after_edit')
                },
                {
                    type: "QuestionMCQ",
                    field: "offerUploadAfterEdit",
                    options: yn_options,
                    showInstruction: false,
                    horizontal: true,
                    mandatory: false
                },
                {
                    type: "QuestionText",
                    text: L('multiline_text_fixed_height')
                },
                {
                    type: "QuestionMCQ",
                    field: "multilineTextFixedHeight",
                    options: yn_options,
                    showInstruction: false,
                    horizontal: true,
                    mandatory: false
                },
                {
                    type: "QuestionTypedVariables",
                    variables: [
                        {
                            type: UICONSTANTS.TYPEDVAR_INTEGER,
                            min: 3,
                            max: 50,
                            field: "multilineDefaultNLines",
                            prompt: L("multiline_text_default_n_lines"),
                            hint: L('multiline_text_default_n_lines'),
                            mandatory: true
                        },
                    ],
                },
            ],
        },
    ];

    for (i = 0; i < varlist.length; ++i) {
        v = varlist[i];
        tempstore[v] = storedvars[v].getValue();
        //Titanium.API.trace("STORED IN TEMPSTORE: " + v + " = " + tempstore[v]);
    }

    questionnaire = new Questionnaire({
        pages: pages,
        callbackThis: this,
        fnGetFieldValue: function (fieldname) {
            var value = tempstore[fieldname];
            //Titanium.API.trace("configure_user.js: fnGetFieldValue: " +
            //                   "fieldname=" + fieldname + ", value=" + value);
            return value;
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
                if (doingPassword) {
                    storedvars.serverPasswordObscured.setValue(
                        rnc_crypto.obscurePassword(tempstore.tempPassword)
                    );
                }
            } else if (result === UICONSTANTS.ABORTED) {
                // Drop the changes.
                return;
            }
        }
    });

    questionnaire.open();
};
