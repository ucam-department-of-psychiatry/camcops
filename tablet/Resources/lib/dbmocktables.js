// dbmocktables.js

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

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var moment = require('lib/moment');
var dbcore = require('lib/dbcore');
var DBCONSTANTS = require('common/DBCONSTANTS');

var mocktables = [];
// ... used when no database exists (for MobileWeb testing, at present!)

function copyFields(objfrom, fieldlist, objto) {
    var i,
        fieldname;
    for (i = 0; i < fieldlist.length; ++i) {
        fieldname = fieldlist[i].name;
        objto[fieldname] = objfrom[fieldname];
    }
}

//=============================================================================
// Table creation
//=============================================================================

function createTable(tablename, fieldlist) {
    var f,
        field,
        record;
    if (mocktables[tablename] !== undefined) {
        // add fields to any records that don't have them
        for (f = 0; f < fieldlist.length; ++f) {
            field = fieldlist[f].name;
            for (record = 0; record < mocktables[tablename].length; ++record) {
                if (mocktables[tablename][record][field] === undefined) {
                    mocktables[tablename][record][field] = null;
                    // ... a default
                }
            }
        }
    } else {
        // create empty table
        mocktables[tablename] = [];
    }
    return;
}
exports.createTable = createTable;

/*jslint unparam: true */
function createIndex(indexname, tablename, fieldnamelist) {
    Titanium.API.trace("Skipping createIndex() call");
}
/*jslint unparam: false */
exports.createIndex = createIndex;

//=============================================================================
// Table deletion
//=============================================================================

/*jslint unparam: true */
function dropTable(tablename) {
    Titanium.API.info("Ignoring dropTable() call on mock-table database");
}
/*jslint unparam: false */
exports.dropTable = dropTable;

//=============================================================================
// Fetch operations
//=============================================================================

function isInDatabaseByPK(tablename, pkname, pkval) {
    var record;
    if (pkval === undefined || pkval === null) {
        return false;
    }
    // Silly code if no real database
    if (mocktables[tablename] === undefined) {
        return false;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        if (mocktables[tablename][record][pkname] === pkval) {
            return true;
        }
    }
    return false;
}
exports.isInDatabaseByPK = isInDatabaseByPK;

function readFromUniqueField(tablename, fieldlist, object, keyname, keyval) {
    // Silly code
    var record;
    if (mocktables[tablename] === "undefined") {
        return false;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        if (mocktables[tablename][record][keyname] === keyval) {
            // found it
            copyFields(mocktables[tablename][record], fieldlist, object);
            return true;
        }
    }
    return false; // didn't find it
}
exports.readFromUniqueField = readFromUniqueField;

function isInDatabaseByUniqueFieldCombination(tablename, wherefields,
                                              wherevalues) {
    // No checking of bad fieldnames.
    var record,
        candidate = false,  // is the current record in the running?
        fieldname,
        i;
    if (mocktables[tablename] === undefined) {
        return false;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        candidate = true;
        for (i = 0; i < wherefields.length; ++i) {
            fieldname = wherefields[i].name;
            if (mocktables[tablename][record][fieldname] !== wherevalues[i]) {
                candidate = false;
            }
        }
        if (candidate) {
            // found it
            return true;
        }
    }
    return false;
}
exports.isInDatabaseByUniqueFieldCombination = isInDatabaseByUniqueFieldCombination;

function readFromUniqueFieldCombination(tablename, fieldlist, object,
                                        fvpairs) {
    var wherefieldnames = [],
        wherevalues = [],
        fieldname,
        field,
        record,
        candidate = false,  // is the current record in the running?
        i;
    for (fieldname in fvpairs) {
        if (fvpairs.hasOwnProperty(fieldname)) {
            field = null;
            for (i = 0; i < fieldlist.length; ++i) {
                if (fieldlist[i].name === fieldname) {
                    field = fieldlist[i];
                    break;
                }
            }
            if (field === null) {
                throw new Error("dbmocktables.readFromUniqueFieldCombination: " +
                                fieldname + " not in fieldlist");
            }
            wherefieldnames.push(fieldname);
            wherevalues.push(fvpairs[fieldname]);
        }
    }

    for (record = 0; record < mocktables[tablename].length; ++record) {
        candidate = true;
        for (i = 0; i < wherefieldnames.length; ++i) {
            fieldname = wherefieldnames[i];
            if (mocktables[tablename][record][fieldname] !== wherevalues[i]) {
                candidate = false;
            }
        }
        if (candidate) {
            // found it
            copyFields(mocktables[tablename][record], fieldlist, object);
            return true;
        }
    }
    return false;
}
exports.readFromUniqueFieldCombination = readFromUniqueFieldCombination;

/*jslint unparam: true */
function getAllRows(tablename, fieldlist, Objecttype, orderby) {
    var rows = [],
        record,
        o;
    if (mocktables[tablename] === undefined) {
        return rows;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        o = new Objecttype();
        copyFields(mocktables[tablename][record], fieldlist, o);
        rows.push(o);
    }
    // Skip "order by" for the moment... ***
    return rows;
}
/*jslint unparam: false */
exports.getAllRows = getAllRows;

/*jslint unparam: true */
function getAllRowsByKey(keyname, keyvalue, tablename, fieldlist, Objecttype,
                         orderby) {
    var rows = [],
        record,
        o;
    if (mocktables[tablename] === undefined) {
        return rows;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        if (mocktables[tablename][record][keyname] === keyvalue) {
            o = new Objecttype();
            copyFields(mocktables[tablename][record], fieldlist, o);
            rows.push(o);
        }
    }
    // Skip "order by" for the moment... ***
    return rows;
}
/*jslint unparam: false */
exports.getAllRowsByKey = getAllRowsByKey;

/*jslint unparam: true */
function getAllPKs(tablename, pkname, orderby) {
    var pks = [],
        record;
    if (mocktables[tablename] === undefined) {
        return pks;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        pks.push(mocktables[tablename][record][pkname]);
    }
    // Skip "order by" for the moment... ***
    return pks;
}
/*jslint unparam: false */
exports.getAllPKs = getAllPKs;

/*jslint unparam: true */
function getAllPKsByKey(tablename, pkname, orderby, keyname, keyvalue) {
    var pks = [],
        record;
    if (mocktables[tablename] === undefined) {
        return pks;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        if (mocktables[tablename][record][keyname] === keyvalue) {
            pks.push(mocktables[tablename][record][pkname]);
        }
    }
    return pks;
}
/*jslint unparam: false */
exports.getAllPKsByKey = getAllPKsByKey;

function getSingleValueByKey(tablename, keyname, keyvalue, field) {
    var record;
    if (mocktables[tablename] === undefined) {
        return null;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        if (mocktables[tablename][record][keyname] === keyvalue) {
            return mocktables[tablename][record][field.name];
        }
    }
    return null;
}
exports.getSingleValueByKey = getSingleValueByKey;

function countWhere(tablename, wherefields, wherevalues, wherenotfields,
                    wherenotvalues) {
    var count = 0,
        i,
        failed,
        record;
    if (mocktables[tablename] === undefined) {
        return null;
    }
    if (wherenotfields === undefined) {
        wherenotfields = [];
    }
    if (wherenotvalues === undefined) {
        wherenotvalues = [];
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        failed = false;
        for (i = 0; i < wherenotfields.length && !failed; ++i) {
            if (mocktables[tablename][record][wherenotfields[i].name] ===
                    wherenotvalues[i]) {
                // fails "where not" clause
                failed = true;
            }
        }
        for (i = 0; i < wherefields.length && !failed; ++i) {
            if (mocktables[tablename][record][wherefields[i].name] ===
                    wherevalues[i]) {
                // fails "where" clause
                failed = true;
            }
        }
        if (!failed) {
            // passed both stages
            ++count;
        }
    }
    return count;
}
exports.countWhere = countWhere;

//=============================================================================
// Insert/update operations
//=============================================================================

/*
function insertOrReplaceRow(tablename, fieldlist, object) {
    var pkname = fieldlist[0].name;
    if (typeof mocktables[tablename] === "undefined") { return false; }
    var pkval = object[pkname];
    if (pkval != null) {
        // it may exist already
        var existingrecord = null;
        for (var record = 0; record < mocktables[tablename].length; ++record) {
            if (mocktables[tablename][record][pkname] == pkval) {
                existingrecord = record;
                break;
            }
        }
    }
    if (existingrecord != null) {
        // exists: replace
        for (var i = 0; i < fieldlist.length; ++i) {
            mocktables[tablename][existingrecord][ fieldlist[i].name ] = object[ fieldlist[i].name ];
        }
    }
    else {
        // doesn't exist; add
        var maxpk = 0;
        for (var record = 0; record < mocktables[tablename].length; ++record) {
            maxpk = Math.max(maxpk, mocktables[tablename][record][pkname]);
        }
        var newrecord;
        for (var i = 0; i < fieldlist.length; ++i) {
            newrecord[ fieldlist[i].name ] = object[ fieldlist[i].name ];
        }
        newrecord[pkname] = maxpk + 1;
        mocktables[tablename].push(newrecord);
    }
    return true;
};
exports.insertOrReplaceRow = insertOrReplaceRow;
*/

function createRow(tablename, fieldlist, object, pkname) {
    // Silly code
    var maxpk = 0,
        record,
        i,
        newrecord = [];
    if (mocktables[tablename] === undefined) {
        return false;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        maxpk = Math.max(maxpk, mocktables[tablename][record][pkname]);
    }
    for (i = 0; i < fieldlist.length; ++i) {
        newrecord[fieldlist[i].name] = object[fieldlist[i].name];
    }
    newrecord[pkname] = maxpk + 1;
    mocktables[tablename].push(newrecord);
    return true;
}
exports.createRow = createRow;

function updateByPK(tablename, fieldlist, object, pkname, pkval) {
    var record;
    if (fieldlist.length <= 0) {
        return true; // nothing to do
    }
    // Silly code
    if (mocktables[tablename] === undefined) {
        return false;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        if (mocktables[tablename][record][pkname] === pkval) {
            // found it
            copyFields(object, fieldlist, mocktables[tablename][record]);
            return true;
        }
    }
    return false; // didn't find it
}
exports.updateByPK = updateByPK;

function setSingleValueByKey(tablename, keyname, keyvalue, field, value) {
    var record;
    if (mocktables[tablename] === undefined) {
        return false;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        if (mocktables[tablename][record][keyname] === keyvalue) {
            // found it
            mocktables[tablename][record][field.name] = value;
            return true;
        }
    }
    return false; // didn't find it
}
exports.setSingleValueByKey = setSingleValueByKey;

//=============================================================================
// Delete operations
//=============================================================================

function deleteWhere(tablename, field, value) {
    var record;
    if (mocktables[tablename] === undefined) {
        return false;
    }
    for (record = 0; record < mocktables[tablename].length; ++record) {
        if (mocktables[tablename][record][field.name] === value) {
            // found it
            mocktables[tablename].splice(record, 1); // delete element
            return true;
        }
    }
    // didn't find it
    return false;
}
exports.deleteWhere = deleteWhere;

//=============================================================================
// Other upload functions
//=============================================================================

function copyDescriptorsToPatients() {
    Titanium.API.trace("dbmocktables.copyDescriptorsToPatients()");
    var storedvars = require('table/storedvars'),
        record,
        i,
        table = DBCONSTANTS.PATIENT_TABLE,
        dp = DBCONSTANTS.IDDESC_FIELD_PREFIX,
        sdp = DBCONSTANTS.IDSHORTDESC_FIELD_PREFIX;
    for (record = 0; record < mocktables[table].length;
            ++record) {
        for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
            mocktables[table][record][dp + i] = (
                storedvars["idDescription" + i].getValue()
            );
            mocktables[table][record][sdp + i] = (
                storedvars["idShortDescription" + i].getValue()
            );
        }
    }
}
exports.copyDescriptorsToPatients = copyDescriptorsToPatients;
