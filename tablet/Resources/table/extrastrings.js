// extrastrings.js

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

/*jslint node: true, nomen: true, newcap: true, plusplus: true */
"use strict";
/*global Titanium, L */

var dbcommon = require('lib/dbcommon'),
    DBCONSTANTS = require('common/DBCONSTANTS'),
    tablename = DBCONSTANTS.EXTRASTRINGS_TABLE,
    TASKFIELD = {name: 'task', type: DBCONSTANTS.TYPE_TEXT},
    fieldlist = [
        TASKFIELD,
        {name: 'name', type: DBCONSTANTS.TYPE_TEXT},
        {name: 'value', type: DBCONSTANTS.TYPE_TEXT}
    ],
    IDXNAME_T = "extrastrings_idx_task",
    IDXNAME_N = "extrastrings_idx_name";


function make_table() {
    Titanium.API.trace("Creating extrastrings table");
    dbcommon.createTable(tablename, fieldlist);
    dbcommon.createIndex(IDXNAME_T, tablename, ["task"]);
    dbcommon.createIndex(IDXNAME_N, tablename, ["name"]);
}


function delete_all_strings() {
    Titanium.API.trace("Dropping/recreating extrastrings table");
    dbcommon.dropTable(tablename);  // drops indices too; see SQLite help
    make_table();
}
exports.delete_all_strings = delete_all_strings;


function get(task, name, defaultvalue) {
    // RETURNS THE STRING.
    var object = {},
        fvpairs = {"task": task, "name": name},
        success = dbcommon.readFromUniqueFieldCombination(tablename, fieldlist,
                                                          object, fvpairs);
    if (!success) {
        return defaultvalue;
    }
    return object.value;
}
exports.get = get;


function add(task, name, value) {
    var object = {"task": task, "name": name, "value": value};
    dbcommon.createRow(tablename, fieldlist, object, "dummypk");
}
exports.add = add;


function task_exists(task) {
    return dbcommon.countWhere(tablename, [TASKFIELD], [task]) > 0;
}
exports.task_exists = task_exists;


// CREATE THE TABLE
make_table();
