// dbwebclient.js

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

// The option to have a synchronous (blocking) call on Titanium.Network.HTTPClient.open() is only available on iOS and MobileWeb.
// Which is OK, since we're using MobileWeb for this.

// NEED TO CONSIDER MULTI-USER LOCKING
// ... think the easiest solution is to have the web client operate on a per-user basis,
//     i.e. you can see the records created by your user (only).
// Access-Control-Allow-Origin errors: see http://en.wikipedia.org/wiki/Same_origin_policy



function encodeString(str) {
    str = str.replace(/'/g, "''");
    return "'" + str + "'";
}

function decodeValue(field, value) {
    if (value === undefined || value === null) {
        return null;
    }
    var conversion = require('lib/conversion'),
        DBCONSTANTS = require('common/DBCONSTANTS');
    switch (field.type) {
    case DBCONSTANTS.TYPE_DATETIME:
    case DBCONSTANTS.TYPE_DATE:
        if (!value) {
            return null;
        }
        return conversion.stringToMoment(value);
    case DBCONSTANTS.TYPE_BOOLEAN:
        if (!value) {
            return null;
        }
        return (parseInt(value, 10) !== 0) ? true : false;
    case DBCONSTANTS.TYPE_TEXT:
        return value;
    case DBCONSTANTS.TYPE_REAL:
        return parseFloat(value);
    default:
        return parseInt(value, 10);
    }
}

function encodeValue(field, value) {
    if (value === undefined || value === null) {
        return "NULL";
    }
    var conversion = require('lib/conversion'),
        DBCONSTANTS = require('common/DBCONSTANTS');
    switch (field.type) {
    case DBCONSTANTS.TYPE_DATETIME:
        return encodeString(conversion.momentToString(value));
    case DBCONSTANTS.TYPE_DATE:
        return encodeString(conversion.momentToDateOnlyString(value));
    case DBCONSTANTS.TYPE_BOOLEAN:
        return value ? 1 : 0;
    case DBCONSTANTS.TYPE_TEXT:
        return encodeString(value);
    default:
        // e.g. numeric
        return value.toString();
    }
}

function encodeFieldsAndValues(fieldlist, object) {
    var fields = "",
        values = "",
        i;
    for (i = 0; i < fieldlist.length; ++i) {
        if (i > 0) {
            fields += ",";
            values += ",";
        }
        fields += fieldlist[i].name;
        values += encodeValue(fieldlist[i], object[fieldlist[i].name]);
    }
    return {
        fields: fields,
        values: values
    };
}

function getFields(fieldlist) {
    var fields = "",
        i;
    for (i = 0; i < fieldlist.length; ++i) {
        if (i > 0) {
            fields += ",";
        }
        fields += fieldlist[i].name;
    }
    return fields;
}

function setObjectFromRawValues(values, fieldlist, object) {
    var i;
    if (values.length !== fieldlist.length) {
        throw new Error("values.length != fieldlist.length in " +
                        "setObjectFromRawValues");
    }
    for (i = 0; i < fieldlist.length; ++i) {
        object[fieldlist[i].name] = decodeValue(fieldlist[i], values[i]);
    }
}

function getMultipleObjectsFromRecordList(recordlist, fieldlist, Objecttype) {
    var objects = [],
        r,
        obj;
    for (r = 0; r < recordlist.length; ++r) {
        obj = new Objecttype();
        setObjectFromRawValues(recordlist[r], fieldlist, obj);
        objects.push(obj);
    }
    // Titanium.API.trace("getMultipleObjectsFromRecordList: objects = " +
    //                    JSON.stringify(objects));
    return objects;
}

//=============================================================================
// Table creation
//=============================================================================

/*jslint unparam: true */
function createTable(tablename, fieldlist) {
    Titanium.API.trace("Skipping createTable() call; using server-side " +
                       "database live");
}
/*jslint unparam: false */
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
    Titanium.API.trace("Ignoring dropTable() call on server-side database");
}
/*jslint unparam: false */
exports.dropTable = dropTable;

//=============================================================================
// Fetch operations
//=============================================================================

function isInDatabaseByPK(tablename, pkname, pkval) {
    var netcore = require('lib/netcore'),
        reply = netcore.getServerResponse({
            operation: "count",
            table: tablename,
            wherefields: pkname,
            wherevalues: pkval
        }),
        count;
    if (!reply.success || !reply.result) {
        return false;
    }
    count = parseInt(reply.result, 10);
    return (count > 0);
}
exports.isInDatabaseByPK = isInDatabaseByPK;

function readFromUniqueField(tablename, fieldlist, object, keyname, keyval) {
    //Titanium.API.trace("dbwebclient.readFromUniqueField()");
    var netcore = require('lib/netcore'),
        reply = netcore.getServerResponse({
            operation: "select",
            table: tablename,
            fields: getFields(fieldlist),
            wherefields: keyname,
            wherevalues: keyval
        }),
        recordlist = netcore.convertResponseToRecordList(reply);
    if (recordlist.length === 0) {
        return false;
    }
    // If we get multiple records by mistake, use the first.
    setObjectFromRawValues(recordlist[0], fieldlist, object);
    return true;
}
exports.readFromUniqueField = readFromUniqueField;

function isInDatabaseByUniqueFieldCombination(tablename, wherefields,
                                              wherevalues) {
    var netcore = require('lib/netcore'),
        wherefieldnames = [],
        encodedvalues = [],
        i,
        reply,
        count;
    for (i = 0; i < wherefields.length; ++i) {
        wherefieldnames.push(wherefields[i].name);
        encodedvalues.push(encodeValue(wherefields[i], wherevalues[i]));
    }
    reply = netcore.getServerResponse({
        operation: "count",
        table: tablename,
        wherefields: wherefieldnames.join(","),
        wherevalues: encodedvalues.join(",")
    });
    if (!reply.success || !reply.result) {
        return false;
    }
    count = parseInt(reply.result, 10);
    return (count > 0);
}
exports.isInDatabaseByUniqueFieldCombination = isInDatabaseByUniqueFieldCombination;

function readFromUniqueFieldCombination(tablename, fieldlist, object,
                                        fvpairs) {
    var netcore = require('lib/netcore'),
        wherefieldnames = [],
        wherevalues = [],
        fieldname,
        field,
        i,
        reply,
        recordlist;
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
                throw new Error("dbwebclient.readFromUniqueFieldCombination: " +
                                fieldname + " not in fieldlist");
            }
            wherefieldnames.push(fieldname);
            wherevalues.push(encodeValue(field, fvpairs[fieldname]));
        }
    }

    reply = netcore.getServerResponse({
        operation: "select",
        table: tablename,
        fields: getFields(fieldlist),
        wherefields: wherefieldnames.join(","),
        wherevalues: wherevalues.join(",")
    });
    recordlist = netcore.convertResponseToRecordList(reply);
    if (recordlist.length === 0) {
        return false;
    }
    setObjectFromRawValues(recordlist[0], fieldlist, object);
    return true;
}
exports.readFromUniqueFieldCombination = readFromUniqueFieldCombination;

/*jslint unparam: true */
function getAllRows(tablename, fieldlist, objecttype, orderby) {
    var netcore = require('lib/netcore'),
        reply = netcore.getServerResponse({
            operation: "select",
            table: tablename,
            fields: getFields(fieldlist)
        }),
        recordlist = netcore.convertResponseToRecordList(reply);
    // order by ... ***
    return getMultipleObjectsFromRecordList(recordlist, fieldlist, objecttype);
}
/*jslint unparam: false */
exports.getAllRows = getAllRows;

/*jslint unparam: true */
function getAllRowsByKey(keyname, keyvalue, tablename, fieldlist, objecttype,
                         orderby) {
    var netcore = require('lib/netcore'),
        reply = netcore.getServerResponse({
            operation: "select",
            table: tablename,
            fields: getFields(fieldlist),
            wherefields: keyname,
            wherevalues: keyvalue
        }),
        recordlist = netcore.convertResponseToRecordList(reply);
    // order by ... ***
    return getMultipleObjectsFromRecordList(recordlist, fieldlist, objecttype);
}
/*jslint unparam: false */
exports.getAllRowsByKey = getAllRowsByKey;

/*jslint unparam: true */
function getAllPKs(tablename, pkname, orderby) {
    var netcore = require('lib/netcore'),
        reply = netcore.getServerResponse({
            operation: "select",
            table: tablename,
            fields: pkname
        }),
        recordlist = netcore.convertResponseToRecordList(reply),
        pks = [],
        i;
    for (i = 0; i < recordlist.length; ++i) {
        pks.push(recordlist[i][0]);
    }
    return pks;
    // order by ... ***
}
/*jslint unparam: false */
exports.getAllPKs = getAllPKs;

/*jslint unparam: true */
function getAllPKsByKey(tablename, pkname, orderby, keyname, keyvalue) {
    var netcore = require('lib/netcore'),
        reply = netcore.getServerResponse({
            operation: "select",
            table: tablename,
            fields: pkname,
            wherefields: keyname,
            wherevalues: keyvalue
        }),
        recordlist = netcore.convertResponseToRecordList(reply),
        pks = [],
        i;
    for (i = 0; i < recordlist.length; ++i) {
        pks.push(recordlist[i][0]);
    }
    return pks;
    // order by ... ***
}
/*jslint unparam: false */
exports.getAllPKsByKey = getAllPKsByKey;

function getSingleValueByKey(tablename, keyname, keyvalue, field) {
    var netcore = require('lib/netcore'),
        reply = netcore.getServerResponse({
            operation: "select",
            table: tablename,
            fields: field.name,
            wherefields: keyname,
            wherevalues: keyvalue
        }),
        recordlist = netcore.convertResponseToRecordList(reply);
    if (recordlist.length === 0) {
        return null;
    }
    return recordlist[0][0];
}
exports.getSingleValueByKey = getSingleValueByKey;

function countWhere(tablename, wherefields, wherevalues, wherenotfields,
                    wherenotvalues) {
    var netcore = require('lib/netcore'),
        wherefieldnames = [],
        encodedwherevalues = [],
        wherenotfieldnames = [],
        encodedwherenotvalues = [],
        i,
        reply,
        count;

    if (wherenotfields === undefined) {
        wherenotfields = [];
    }
    if (wherenotvalues === undefined) {
        wherenotvalues = [];
    }
    for (i = 0; i < wherefields.length; ++i) {
        wherefieldnames.push(wherefields[i].name);
        encodedwherevalues.push(encodeValue(wherefields[i],
                                            wherevalues[i]));
    }
    for (i = 0; i < wherenotfields.length; ++i) {
        wherenotfieldnames.push(wherenotfields[i].name);
        encodedwherenotvalues.push(encodeValue(wherenotfields[i],
                                               wherenotvalues[i]));
    }
    reply = netcore.getServerResponse({
        operation: "count",
        table: tablename,
        wherefields: wherefieldnames.join(","),
        wherevalues: encodedwherevalues.join(","),
        wherenotfields: wherenotfieldnames.join(","),
        wherenotvalues: encodedwherenotvalues.join(",")
    });
    if (!reply.success || !reply.result) {
        return false;
    }
    count = parseInt(reply.result, 10);
    return count;
}
exports.countWhere = countWhere;

//=============================================================================
// Insert/update operations
//=============================================================================

/*
function insertOrReplaceRow(tablename, fieldlist, object) {
    // Not implemented; no need.
};
exports.insertOrReplaceRow = insertOrReplaceRow;
*/

function createRow(tablename, fieldlist, object, pkname) {
    var netcore = require('lib/netcore'),
        VERSION = require('common/VERSION'),
        fieldsAndValues = encodeFieldsAndValues(fieldlist, object),
        reply = netcore.getServerResponse({
            operation: "insert",
            camcops_version: VERSION.CAMCOPS_VERSION,
            table: tablename,
            fields: fieldsAndValues.fields,
            values: fieldsAndValues.values,
            pkname: pkname
        }),
        lastInsertRowId;

    if (!reply.success || !reply.result) {
        Titanium.API.warn("dbwebclient.createRow: failure");
        return false;
    }
    lastInsertRowId = parseInt(reply.result, 10);
    Titanium.API.trace(
        "dbwebclient.createRow: success, inserted record id = " +
            lastInsertRowId
    );
    object[pkname] = lastInsertRowId;
    return true;
}
exports.createRow = createRow;

function updateByPK(tablename, fieldlist, object, pkname, pkval) {
    var netcore = require('lib/netcore'),
        VERSION = require('common/VERSION'),
        params = {
            operation: "update",
            camcops_version: VERSION.CAMCOPS_VERSION,
            table: tablename,
            wherefields: pkname,
            wherevalues: pkval
        },
        fieldsAndValues = encodeFieldsAndValues(fieldlist, object),
        reply,
        success;
    params.fields = fieldsAndValues.fields;
    params.values = fieldsAndValues.values;
    reply = netcore.getServerResponse(params);
    if (!reply.success || !reply.result) {
        return false;
    }
    success = parseInt(reply.result, 10);
    return (success !== 0);
}
exports.updateByPK = updateByPK;

function setSingleValueByKey(tablename, keyname, keyvalue, field, value) {
    var netcore = require('lib/netcore'),
        params = {
            operation: "update",
            table: tablename,
            wherefields: keyname,
            wherevalues: keyvalue,
            fields: field.name,
            values: encodeValue(field, value)
        },
        reply = netcore.getServerResponse(params),
        success;

    if (!reply.success || !reply.result) {
        return false;
    }
    success = parseInt(reply.result, 10);
    return (success !== 0);
}
exports.setSingleValueByKey = setSingleValueByKey;

//=============================================================================
// Delete operations
//=============================================================================

function deleteWhere(tablename, field, value) {
    var netcore = require('lib/netcore');
    netcore.getServerResponse({
        operation: "delete",
        table: tablename,
        wherefields: field.name,
        wherevalues: encodeValue(field, value)
    });
}
exports.deleteWhere = deleteWhere;

//=============================================================================
// Other upload functions
//=============================================================================

function copyDescriptorsToPatients() {
    // Rely on the database storage in the Patient class
    Titanium.API.trace("dbwebclient.copyDescriptorsToPatients()");
    var DBCONSTANTS = require('common/DBCONSTANTS'),
        storedvars = require('table/storedvars'),
        Patient = require('table/Patient'),
        patientdata = (new Patient()).getAllRows(),
        record,
        i;
    for (record = 0; record < patientdata.length; ++record) {
        for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
            patientdata[record][DBCONSTANTS.IDDESC_FIELD_PREFIX + i] = (
                storedvars["idDescription" + i].getValue()
            );
            patientdata[record][DBCONSTANTS.IDSHORTDESC_FIELD_PREFIX + i] = (
                storedvars["idShortDescription" + i].getValue()
            );
        }
        patientdata[record].dbstore();
    }
}
exports.copyDescriptorsToPatients = copyDescriptorsToPatients;
