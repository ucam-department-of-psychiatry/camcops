// PclM.js

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

/*jslint node: true, nomen: true */
"use strict";

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    PclCommon = require('task/PclCommon'),
    lang = require('lib/lang'),
    tablename = "pclm",
    fieldlist = dbcommon.standardTaskFields(),
    nquestions = 17;

dbcommon.appendRepeatedFieldDef(fieldlist, "q", 1, nquestions,
                                DBCONSTANTS.TYPE_INTEGER);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function PclM(patient_id) {
    PclCommon.call(this, patient_id); // call base constructor
}
lang.inheritPrototype(PclM, PclCommon);
lang.extendPrototype(PclM, {
    _objecttype: PclM,
    _tablename: tablename,
    _fieldlist: fieldlist,

    _nquestions: nquestions,
    _pcltype: "m",
    _specificEvent: false
});
module.exports = PclM;
