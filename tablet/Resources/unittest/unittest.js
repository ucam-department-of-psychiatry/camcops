// unittest.js

/*
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com)
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

/*jslint node: true */
"use strict";
/*global Titanium */

var jsUnity = require('unittest/jsunity');
var test_suite_1 = {
    suiteName: "CamCOPS unit test suite",
    // setUp
    // tearDown

    // ------------------------------------------------------------------------
    // common
    // ------------------------------------------------------------------------

    test_ALLTASKS: function () {
        var ALLTASKS = require('common/ALLTASKS'),
            item,
            s = "";
        for (item in ALLTASKS.TASKLIST) {
            if (ALLTASKS.TASKLIST.hasOwnProperty(item)) {
                s += ".";
            }
        }
        jsUnity.log(s);
    },

    test_CODES_ICD9CM: function () {
        var CODELIST = require('common/CODES_ICD9CM'),
            item,
            s = "";
        for (item in CODELIST) {
            if (CODELIST.hasOwnProperty(item)) {
                s += ".";
            }
        }
        jsUnity.log(s);
    },

    test_CODES_ICD10: function () {
        var CODELIST = require('common/CODES_ICD10'),
            item,
            s = "";
        for (item in CODELIST) {
            if (CODELIST.hasOwnProperty(item)) {
                s += ".";
            }
        }
        jsUnity.log(s);
    },

    test_COLOURS: function () {
        var COLOURS = require('common/COLOURS'),
            item,
            s = "";
        for (item in COLOURS) {
            if (COLOURS.hasOwnProperty(item)) {
                s += ".";
            }
        }
        jsUnity.log(s);
    },

    test_DBCONSTANTS: function () {
        var DBCONSTANTS = require('common/DBCONSTANTS'),
            item,
            s = "";
        for (item in DBCONSTANTS) {
            if (DBCONSTANTS.hasOwnProperty(item)) {
                s += ".";
            }
        }
        jsUnity.log(s);
    },

    test_EVENTS: function () {
        var EVENTS = require('common/EVENTS'),
            item,
            s = "";
        for (item in EVENTS) {
            if (EVENTS.hasOwnProperty(item)) {
                s += ".";
            }
        }
        jsUnity.log(s);
    },

    test_GV: function () {
        var GV = require('common/GV'),
            item,
            s = "";
        for (item in GV) {
            if (GV.hasOwnProperty(item)) {
                s += ".";
            }
        }
        jsUnity.log(s);
    },

    test_NHS_DD: function () {
        var NHS_DD = require('common/NHS_DD'),
            item,
            s = "";
        for (item in NHS_DD.PERSON_MARITAL_STATUS_CODE_OPTIONS) {
            if (NHS_DD.PERSON_MARITAL_STATUS_CODE_OPTIONS.hasOwnProperty(item)) {
                s += ".";
            }
        }
        for (item in NHS_DD.ETHNIC_CATEGORY_CODE_OPTIONS) {
            if (NHS_DD.ETHNIC_CATEGORY_CODE_OPTIONS.hasOwnProperty(item)) {
                s += ".";
            }
        }
        jsUnity.log(s);
    },

    test_UICONSTANTS: function () {
        var UICONSTANTS = require('common/UICONSTANTS'),
            item,
            s = "";
        for (item in UICONSTANTS) {
            if (UICONSTANTS.hasOwnProperty(item)) {
                s += ".";
            }
        }
        jsUnity.log(s);
    },

    test_VERSION: function () {
        var VERSION = require('common/VERSION');
        jsUnity.log("version: " + VERSION.CAMCOPS_VERSION);
    },
};

function unittest() {
    Titanium.API.info("UNIT TESTING: START");
    jsUnity.run(test_suite_1);
    Titanium.API.info("UNIT TESTING: END");
}

jsUnity.log = function (message) {
    Titanium.API.info(message);
};

exports.unittest = unittest;
