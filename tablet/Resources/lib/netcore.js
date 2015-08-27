// netcore.js

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

var serverpassword = "",
    session_id = "",
    session_token = "";

/*jslint unparam: true */
function setTempServerPasswordAndCall(successfunction, failurefunction) {
    var storedvars = require('table/storedvars'),
        AskUsernamePasswordWindow,
        rnc_crypto,
        win;

    // Do we have the password already?
    if (storedvars.storeServerPassword.getValue() &&
            storedvars.serverPasswordObscured.getValue()) {
        // Yes.
        rnc_crypto = require('lib/rnc_crypto');
        serverpassword = rnc_crypto.retrieveObscuredPassword(
            storedvars.serverPasswordObscured.getValue()
        );
        successfunction();
        return;
    }
    // No.
    AskUsernamePasswordWindow = require('screen/AskUsernamePasswordWindow');
    win = new AskUsernamePasswordWindow({
        askUsername: false,
        captionPassword: (L('enter_server_password_for_user') + " " +
                          storedvars.serverUser.getValue() + ":"),
        hintPassword: L('hint_password'),
        showCancel: true,
        verifyAgainstHash: false,
        callbackFn: function (username, password, verified, cancelled) {
            // ignored: username, verified
            if (cancelled) {
                if (typeof failurefunction === "function") {
                    failurefunction();
                }
            } else {
                serverpassword = password;
                if (typeof successfunction === "function") {
                    successfunction();
                }
            }
        }
    });
    win.open();
}
/*jslint unparam: false */
exports.setTempServerPasswordAndCall = setTempServerPasswordAndCall;

function clearSession() {
    session_id = null;
    session_token = null;
}
exports.clearSession = clearSession;

function clearTempServerPassword() {
    var platform = require('lib/platform');
    if (platform.mobileweb) {
        return;
    }
    serverpassword = "";
    clearSession();
}
exports.clearTempServerPassword = clearTempServerPassword;

function setTempServerPassword(password) {
    // used on mobileweb; see storedvars.js
    serverpassword = password;
}
exports.setTempServerPassword = setTempServerPassword;

function parseServerReply(text) {
    //Titanium.API.trace("SERVER REPLY:" + text);
    // As of 2014-09-13: reply is always a series of "key:value" pairs, one per
    // line.
    var reply = {},
        i,
        lines = text.split("\n"),
        nvp_regex = /^([\S]+?):\s*([\s\S]*)/,
        // ? makes the + lazy, not greedy:
        // http://www.regular-expressions.info/repeat.html
        name,
        value,
        searchresult;
        // \s whitespace, \S non-whitespace
        // test with:
        //      teststr = "name: value1 value2";
        //      teststr = "record1:2blah2";
        //      nvp_regex.exec(teststr);
    for (i = 0; i < lines.length; i += 1) {
        //Titanium.API.trace("parseServerReply: line " + i + " = " +
        //                   lines[i]);
        searchresult = nvp_regex.exec(lines[i]);
        if (searchresult !== null) { // match "name: value"
            name = searchresult[1];
            value = searchresult[2];
            reply[name] = value;
        }
    }
    // Some special processing:
    if (reply.hasOwnProperty("success")) {
        reply.success = parseInt(reply.success, 10) ? true : false;
    } else {
        reply.success = false;
    }
    if (!reply.hasOwnProperty("error")) {
        reply.error = null;
    }
    if (!reply.hasOwnProperty("result")) { // for simple results
        reply.result = null;
    }
    if (reply.hasOwnProperty("session_id") &&
            reply.hasOwnProperty("session_token")) {
        session_id = reply.session_id;
        session_token = reply.session_token;
    } else {
        session_id = null;
        session_token = null;
    }
    // Done
    return reply;
}

function convertResponseToRecordList(response) {
    // Multiline regexs: http://stackoverflow.com/questions/1068280/
    var recordlist = [],
        conversion = require('lib/conversion'),
        nrecords,
        nfields,
        name,
        r,
        valuelist,
        rawvalues;

    if (!response ||
            !response.hasOwnProperty("nrecords") ||
            !response.hasOwnProperty("nfields") ||
            !response.hasOwnProperty("fields")) {
        Titanium.API.warn("convertResponseToRecordList: bad response");
        return []; // return empty list upon failure
    }
    nrecords = parseInt(response.nrecords, 10);
    nfields = parseInt(response.nfields, 10);
    if (isNaN(nrecords) || isNaN(nfields)) {
        Titanium.API.warn("convertResponseToRecordList: bad nrecords or " +
                          "nfields");
        return []; // return empty list upon failure
    }
    for (r = 0; r < nrecords; ++r) {
        name = "record" + r;
        if (!response.hasOwnProperty(name)) {
            Titanium.API.warn("convertResponseToRecordList: missing record");
            return [];
        }
        valuelist = response[name];
        if (!valuelist) {
            Titanium.API.warn("convertResponseToRecordList: missing values");
            return [];
        }
        rawvalues = conversion.CSVSQLtoArray(valuelist);
        if (rawvalues.length !== nfields) {
            Titanium.API.warn("convertResponseToRecordList: #values not " +
                              "equal to #fields");
            return [];
        }
        recordlist.push(rawvalues);
    }
    //Titanium.API.trace("convertResponseToRecordList: returning: " +
    //                   JSON.stringify(recordlist));
    return recordlist;
}
exports.convertResponseToRecordList = convertResponseToRecordList;

function setBasicNetworkDictionaryProperties(dict, includeUser) {
    var storedvars = require('table/storedvars'),
        DBCONSTANTS = require('common/DBCONSTANTS'),
        platform = require('lib/platform'),
        VERSION = require('common/VERSION');
    dict.camcops_version = VERSION.CAMCOPS_VERSION;
    if (platform.mobileweb) {
        dict.device = "mobileweb_" + storedvars.serverUser.getValue();
    } else {
        dict.device = DBCONSTANTS.DEVICE_ID;
    }
    if (includeUser) {
        dict.user = storedvars.serverUser.getValue();
        dict.password = serverpassword;
    }
    if (session_id && session_token) {
        dict.session_id = session_id;
        dict.session_token = session_token;
    }
}

function getBlankResponseDict() {
    return {
        success: false,
        response: null,
        error: null
    };
}

function announceError(error, url) {
    var uifunc = require('lib/uifunc');
    Titanium.API.warn("WEBCLIENT SERVER ERROR: " + error);
    uifunc.alert(
        L('webclient_failed') + "\n\n" +
            L('webclient_was_to') + " " + url + "\n\n" +
            L('errors') + " " + error
    );
}

function getServerResponse(dict, includeUser) { // Blocking
    var platform = require('lib/platform'),
        storedvars = require('table/storedvars'),
        result = getBlankResponseDict(),
        url = storedvars.getServerURL(),
        uifunc,
        client;

    if (!platform.isBlockingHttpSupported) {
        uifunc = require('lib/uifunc');
        uifunc.alert("Bug: Blocking HTTP call made on unsupported platform!");
        return result;
    }

    if (includeUser === undefined) {
        includeUser = true;
    }
    setBasicNetworkDictionaryProperties(dict, includeUser);
    client = Titanium.Network.createHTTPClient({
        // function called when the response data is available
        onload: function () {
            result = parseServerReply(this.responseText);
            if (!result.success) {
                announceError(result.error, url);
            }
        },
        // function called when an error occurs, including a timeout
        onerror: function (e) {
            result.success = false;
            result.error = e.error;
            announceError(result.error, url);
        },
        timeout: storedvars.serverTimeoutMs.getValue(), // in milliseconds
        validatesSecureCertificate: storedvars.validateSSLCertificates.getValue()
    });
    // Titanium.API.trace("SENDING TO SERVER: " + JSON.stringify(dict));
    // Prepare the connection. SYNCHRONOUS (BLOCKING) MODE.
    client.open("POST", url, false); // third parameter (async) defaults to true
    // Send the request.
    //Titanium.API.trace("getServerResponse: outbound dict: " +
    //                   JSON.stringify(dict));
    client.send(dict);
    // Shouldn't arrive here until result has been written by the onload/onerror function...
    //Titanium.API.trace("getServerResponse: inbound result: " +
    //                   JSON.stringify(result));
    return result;
}
exports.getServerResponse = getServerResponse;

function sendToServer(dict, callbackSuccess, callbackFailure, includeUser) {
    // non-blocking; asynchronous
    var storedvars = require('table/storedvars'),
        result = getBlankResponseDict(),
        url = storedvars.getServerURL(),
        client;

    if (includeUser === undefined) {
        includeUser = true;
    }
    setBasicNetworkDictionaryProperties(dict, includeUser);
    client = Titanium.Network.createHTTPClient({
        // function called when the response data is available
        onload: function () {
            // Titanium.API.debug("SERVER REPLY: " + this.responseText);
            result = parseServerReply(this.responseText);
            if (result.success) {
                callbackSuccess(result);
            } else {
                Titanium.API.warn("SERVER SAYS CLIENT-SIDE ERROR: " +
                                  result.error);
                callbackFailure(result.error);
            }
        },
        // function called when an error occurs, including a timeout
        onerror: function (e) {
            // on iOS: e = {"source":{"cache":false},"type":"error"}
            // ... i.e. e.error is undefined
            // on Android, it works fine
            //Titanium.API.trace("SERVER RESPONSE:" + JSON.stringify(e));
            result.success = false;
            result.error = e.error;
            Titanium.API.warn("sendToServer: ERROR: " + result.error);
            callbackFailure(result.error);
        },
        timeout: storedvars.serverTimeoutMs.getValue(), // in milliseconds
        validatesSecureCertificate: storedvars.validateSSLCertificates.getValue()
    });
    // Titanium.API.trace("SENDING TO SERVER: " + JSON.stringify(dict));
    // Prepare the connection.
    client.open("POST", url, true); // third parameter (async) defaults to true
    // Send the request.
    client.send(dict);
}
exports.sendToServer = sendToServer;
