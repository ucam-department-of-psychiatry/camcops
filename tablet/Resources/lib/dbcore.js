// dbcore.js

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

/*jslint node: true */
"use strict";

var platform = require('lib/platform');

function getFieldCount(cursor) {
    /*
    Titanium BUG: https://jira.appcelerator.org/browse/TIMOB-5881
    Briefly (development version of SDK 3) iOS didn't require brackets.
    Then, android supported "fieldCount" and iOS required "fieldCount()".
    Then, as of May 2014, iOS was changed so both use properties, not methods.
    This came into force with 3.3.0GA.
    Docs: see Titanium.Database.ResultSet
    */

    return cursor.fieldCount; // no brackets
}
exports.getFieldCount = getFieldCount;
