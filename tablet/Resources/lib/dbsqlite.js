// dbsqlite.js

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

NOTE: close the database/resultset after each operation.
      http://docs.appcelerator.com/titanium/latest/#!/guide/Working_with_a_SQLite_Database
*/

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var conversion = require('lib/conversion');
var DBCONSTANTS = require('common/DBCONSTANTS');

//=============================================================================
// To/from cursors
//=============================================================================

//-----------------------------------------------------------------------------
// Database to memory:
//-----------------------------------------------------------------------------

function decodeValue(field, value) {
    if (value === undefined || value === null) {
        return null;
    }
    switch (field.type) {
    case DBCONSTANTS.TYPE_DATETIME:
    case DBCONSTANTS.TYPE_DATE:
        if (!value) {
            return null; // e.g. empty string
        }
        return conversion.stringToMoment(value);
    case DBCONSTANTS.TYPE_BOOLEAN:
        return (value !== 0) ? true : false;
    default:
        return value;
    }
}

function setFromCursor(cursor, fieldlist, object) {
    var i,
        field,
        value;
    for (i = 0; i < fieldlist.length; ++i) {
        field = fieldlist[i];
        value = cursor.field(i);
        object[field.name] = decodeValue(field, value);
        /*
        Titanium.API.debug("setFromCursor: field " + field +
                           ", value: " + value +
                           " -> " + object[field.name]);
        */
    }
}

//-----------------------------------------------------------------------------
// Memory to database:
//-----------------------------------------------------------------------------

function encodeValue(field, value) {
    if (value === undefined || value === null) {
        return null;
    }
    switch (field.type) {
    case DBCONSTANTS.TYPE_DATETIME:
        return conversion.momentToString(value);
    case DBCONSTANTS.TYPE_DATE:
        return conversion.momentToDateOnlyString(value);
    case DBCONSTANTS.TYPE_BOOLEAN:
        return value ? 1 : 0;
    case DBCONSTANTS.TYPE_PK: // an integer type
    case DBCONSTANTS.TYPE_INTEGER: // an integer type
    case DBCONSTANTS.TYPE_BIGINT: // an integer type
    case DBCONSTANTS.TYPE_BLOBID: // an integer type
        value = parseInt(value, 10);
        if (isNaN(value)) {
            return null;
        }
        return value;
    case DBCONSTANTS.TYPE_REAL:
        value = parseFloat(value);
        if (isNaN(value)) {
            return null;
        }
        return value;
    default:
        return value;
    }
}

function appendFieldValueArgs(args, fieldlist, object) {
    var i;
    for (i = 0; i < fieldlist.length; ++i) {
        args.push(encodeValue(fieldlist[i],
                              object[fieldlist[i].name]));
    }
}

function getFieldValueArgs(fieldlist, object) {
    var args = [];
    appendFieldValueArgs(args, fieldlist, object);
    return args;
}

//=============================================================================
// Used by what follows
//=============================================================================

function trace_execute(db, query, args) {
    if (args === undefined) {
        Titanium.API.trace(query);
        return db.execute(query);
    }
    Titanium.API.trace(query + " [args = " + JSON.stringify(args) + "]");
    return db.execute(query, args);
    // caller must close recordset
}

function execute(db, query, args) {
    if (args === undefined) {
        return db.execute(query);
    }
    return db.execute(query, args);
    // caller must close recordset
}

function trace_execute_noreturn(db, query, args) {
    var cursor;
    if (args === undefined) {
        Titanium.API.trace(query);
        cursor = db.execute(query);
    } else {
        Titanium.API.trace(query + " [args = " + JSON.stringify(args) + "]");
        cursor = db.execute(query, args);
    }
    if (cursor !== null) {
        // Some execute() calls return a ResultSet (which needs closing);
        // some return null.
        // http://stackoverflow.com/questions/13860514
        cursor.close();
    }
}

function execute_noreturn(db, query, args) {
    var cursor;
    if (args === undefined) {
        cursor = db.execute(query);
    } else {
        cursor = db.execute(query, args);
    }
    if (cursor !== null) {
        cursor.close();
    }
}
exports.execute_noreturn = execute_noreturn;

function standalone_execute_noreturn(query, args) {
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor;
    if (args === undefined) {
        cursor = db.execute(query);
    } else {
        cursor = db.execute(query, args);
    }
    if (cursor !== null) {
        cursor.close();
    }
    db.close();
}

function tableExists(tablename) {
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor = db.execute("SELECT COUNT(*) FROM sqlite_master " +
                            "WHERE type=='table' AND name=?", tablename),
        n = cursor.field(0);
    cursor.close();
    db.close();
    return (n > 0);
}
exports.tableExists = tableExists;

function delimit(f) {
    return '"' + f + '"';
}

function columnDefSQL(field) {
    // IF YOU CHANGE SOMETHING HERE, CHANGE fieldTypeMatches() TOO.
    var s = delimit(field.name) + " ";
    switch (field.type) {
    case DBCONSTANTS.TYPE_PK:
        s += "INTEGER PRIMARY KEY";
        // The "AUTOINCREMENT" keyword is not necessary, and can in principle
        // lead to failure with very old tables:
        // http://www.sqlite.org/faq.html#q1
        break;
    case DBCONSTANTS.TYPE_TEXT:
    case DBCONSTANTS.TYPE_DATETIME:
    case DBCONSTANTS.TYPE_DATE:
        s += "TEXT";
        break;
    // Integers that might need to be big:
    case DBCONSTANTS.TYPE_BIGINT:
        // SQLite uses up to 8 bytes, and integers are signed, so the maximum
        //     is 2^63 - 1 = 9,223,372,036,854,775,807
        // Javascript has a maximum safe integer of 9,007,199,254,740,991
        //     http://stackoverflow.com/questions/307179
        // BUT: Titanium bug in reading large integer values;
        //     https://jira.appcelerator.org/browse/TIMOB-3050
        // So... see reasoning in VERSION_TRACKER.txt
        s += "REAL";
        break;
    // Types for which a short integer will suffice:
    case DBCONSTANTS.TYPE_BLOBID:
    case DBCONSTANTS.TYPE_INTEGER:
    case DBCONSTANTS.TYPE_BOOLEAN:
        // SQLite uses up to 8 bytes, and integers are signed, so the maximum
        //     is 2^63 - 1 = 9,223,372,036,854,775,807
        // Javascript has a maximum safe integer of 9,007,199,254,740,991
        //     http://stackoverflow.com/questions/307179
        // BUT: Titanium bug in reading large integer values;
        //     https://jira.appcelerator.org/browse/TIMOB-3050
        s += "INTEGER";
        break;
    // Actual floating-point values:
    case DBCONSTANTS.TYPE_REAL:
        s += "REAL";
        break;
    }
    if (field.type !== DBCONSTANTS.TYPE_PK) {
        if (field.unique) {
            s += " UNIQUE";
        }
        if (field.mandatory) {
            s += " NOT NULL";
        }
    }
    return s;
}

function getFieldNames(tablename) {
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor = db.execute("PRAGMA table_info(" + delimit(tablename) + ")"),
        fieldnames = [];
    while (cursor.isValidRow()) {
        fieldnames.push(cursor.field(1));
        cursor.next();
    }
    cursor.close();
    db.close();
    return fieldnames;
}
exports.getFieldNames = getFieldNames;

function getFields(tablename) {
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        query = "PRAGMA table_info(" + delimit(tablename) + ")",
        cursor = db.execute(query),
        fields = [];
    while (cursor.isValidRow()) {
        fields.push({
            index: cursor.field(0),
            name: cursor.field(1),
            datatype: cursor.field(2),
            nullAllowed: cursor.field(3),
            defaultValue: cursor.field(4)
        });
        cursor.next();
    }
    cursor.close();
    db.close();
    return fields;
}
exports.getFields = getFields;

function debugFunctionArgs(functionName, args) {
    Titanium.API.debug(functionName + "(" + JSON.stringify(args) + ")");
}

function debugQueryArgs(functionName, query, args) {
    Titanium.API.debug(functionName + ": SQL query: " + query);
    Titanium.API.debug("... args: " + JSON.stringify(args));
}

function fieldnames_from_fieldspecs(fieldlist) {
    var i,
        names = [];
    for (i = 0; i < fieldlist.length; ++i) {
        names.push(fieldlist[i].name);
    }
    return names;
}

/*
function requireTableWithDbOpen(db, tablename, calling_func_arguments) {
    var cursor = db.execute("SELECT COUNT(*) FROM sqlite_master " +
                            "WHERE type=='table' AND name=?", tablename),
        n = cursor.field(0),
        funcname;
    cursor.close();
    if (n > 0) {
        return;
    }
    // http://stackoverflow.com/questions/1013239
    funcname = calling_func_arguments.callee.toString();
    funcname = funcname.substr('function '.length);
    funcname = funcname.substr(0, funcname.indexOf('('));
    throw new Error("Function " + funcname + "() requires table " +
                    tablename + " but it does not exist");
}
*/

//=============================================================================
// SQL generators
//=============================================================================

function getCreateTableSQL(tablename, fieldlist) {
    var s = "CREATE TABLE IF NOT EXISTS " + delimit(tablename) + " (",
        i;
    for (i = 0; i < fieldlist.length; ++i) {
        if (i > 0) {
            s += ",";
        }
        s += columnDefSQL(fieldlist[i]);
    }
    s += ")";
    return s;
}

function getCreateTableSQLFromDatabase(tablename) {
    var query = "SELECT sql FROM sqlite_master WHERE tbl_name = ?",
        args = [tablename],
        db,
        cursor,
        creation_sql;
    if (!tableExists(tablename)) {
        return "";
    }
    // http://www.sqlite.org/lang_altertable.html
    db = Titanium.Database.open(DBCONSTANTS.DBNAME);
    cursor = db.execute(query, args);
    creation_sql = cursor.field(0);
    cursor.close();
    db.close();
    return creation_sql;
    // Will look like: "CREATE TABLE blah (a int, b real, c text)"
}

function getPragmaInfoSQL(tablename) {
    return "PRAGMA TABLE_INFO (" + delimit(tablename) + ")";
}

function addColumnSQL(tablename, field) {
    return (
        "ALTER TABLE " + delimit(tablename) +
        " ADD COLUMN " + columnDefSQL(field)
    );
}

function getFieldsAndValuesSQL(fieldlist) {
    // Returns SQL with "?"s for an INSERT INTO statement
    var s = " (",
        i;
    for (i = 0; i < fieldlist.length; ++i) {
        if (i > 0) {
            s += ",";
        }
        s += delimit(fieldlist[i].name);
    }
    s += ") VALUES (";
    for (i = 0; i < fieldlist.length; ++i) {
        if (i > 0) {
            s += ",";
        }
        s += "?";
    }
    s += ")";
    return s;
}

function getInsertSQL(tablename, fieldlist) {
    // INSERT INTO tablename (field1, field2, ...) VALUES (?, ?, ...)
    return "INSERT INTO " + delimit(tablename) + getFieldsAndValuesSQL(fieldlist);
}
exports.getInsertSQL = getInsertSQL;

function getInsertOrReplaceSQL(tablename, fieldlist) {
    // INSERT OR REPLACE INTO tablename (f1, f2, ...) VALUES (?, ?, ...)
    return "INSERT OR REPLACE INTO " + delimit(tablename) + getFieldsAndValuesSQL(fieldlist);
}
exports.getInsertOrReplaceSQL = getInsertOrReplaceSQL;

function getUpdateByPKSQL(tablename, fieldlist, pkname) {
    // UPDATE tablename SET field1=?, field2=?, ... WHERE primarykey=?
    var s = "UPDATE " + delimit(tablename) + " SET ",
        i;
    if (fieldlist.length <= 0) {
        return null;
    }
    for (i = 0; i < fieldlist.length; ++i) {
        if (i > 0) {
            s += ",";
        }
        s += delimit(fieldlist[i].name) + "=?";
    }
    s += " WHERE " + pkname + "=?"; // PK
    return s;
}
exports.getUpdateByPKSQL = getUpdateByPKSQL;

function getDeleteByKeySQL(tablename, keyname) {
    return (
        "DELETE FROM " + delimit(tablename) +
        " WHERE " + delimit(keyname) + "=?"
    );
}
exports.getDeleteByKeySQL = getDeleteByKeySQL;

function getSelectByKeySQL(tablename, fieldlist, keyname, orderby) {
    var fieldnames = "",
        i,
        s;
    for (i = 0; i < fieldlist.length; ++i) {
        if (i > 0) {
            fieldnames += ",";
        }
        fieldnames += delimit(fieldlist[i].name);
    }
    s = ("SELECT " + fieldnames + " FROM " + delimit(tablename) +
         " WHERE " + delimit(keyname) + "=?");
    if (orderby) {
        s += " ORDER BY " + orderby;
    }
    return s;
}
exports.getSelectByKeySQL = getSelectByKeySQL;

function getSelectByMultipleFieldsSQL(tablename, fieldlist, wherefieldnames, orderby) {
    var fieldnames = "",
        i,
        s;
    for (i = 0; i < fieldlist.length; ++i) {
        if (i > 0) {
            fieldnames += ",";
        }
        fieldnames += delimit(fieldlist[i].name);
    }
    s = "SELECT " + fieldnames + " FROM " + delimit(tablename) + " WHERE ";
    for (i = 0; i < wherefieldnames.length; ++i) {
        if (i > 0) {
            s += " AND ";
        }
        s += delimit(wherefieldnames[i]) + "=?";
    }
    if (orderby) {
        s += " ORDER BY " + orderby;
    }
    return s;
}
exports.getSelectByMultipleFieldsSQL = getSelectByMultipleFieldsSQL;

function getSelectAllRowsSQL(tablename, fieldlist, orderby) {
    var fieldnames = "",
        i,
        s;
    for (i = 0; i < fieldlist.length; ++i) {
        if (i > 0) {
            fieldnames += ",";
        }
        fieldnames += delimit(fieldlist[i].name);
    }
    s = "SELECT " + fieldnames + " FROM " + delimit(tablename);
    if (orderby) {
        s += " ORDER BY " + orderby;
        // don't delimit, or we'll get ORDER BY "surname, forename, id"
        // (with the quotes)
    }
    // Titanium.API.trace("getSelectAllRowsSQL: " + s);
    return s;
}
exports.getSelectAllRowsSQL = getSelectAllRowsSQL;

function countByKeySQL(tablename, keyname) {
    return ("SELECT COUNT(*) FROM " + delimit(tablename) +
            " WHERE " + delimit(keyname) + "=?");
}
exports.countByKeySQL = countByKeySQL;

function countByMultipleFieldsSQL(tablename, wherefieldnames) {
    var s = "SELECT COUNT(*) FROM " + delimit(tablename) + " WHERE ",
        i;
    for (i = 0; i < wherefieldnames.length; ++i) {
        if (i > 0) {
            s += " AND ";
        }
        s += delimit(wherefieldnames[i]) + "=?";
    }
    return s;
}
exports.countByMultipleFieldsSQL = countByMultipleFieldsSQL;

//=============================================================================
// Table creation
//=============================================================================

function fieldTypeValid(fieldspec) {
    switch (fieldspec.type) {
    case DBCONSTANTS.TYPE_PK:
    case DBCONSTANTS.TYPE_INTEGER:
    case DBCONSTANTS.TYPE_BIGINT:
    case DBCONSTANTS.TYPE_BLOBID:
    case DBCONSTANTS.TYPE_BOOLEAN:
    case DBCONSTANTS.TYPE_REAL:
    case DBCONSTANTS.TYPE_TEXT:
    case DBCONSTANTS.TYPE_DATETIME:
    case DBCONSTANTS.TYPE_DATE:
        return true;
    default:
        return false;
    }
}

function fieldTypeMatches(sqliteType, camcopsType) {
    // sqliteType will be one of: ... well, actually, anything;
    //   in SQLite, you can do "CREATE TABLE dummy (a integer, b wotsit);"
    //   and PRAGMA TABLE_INFO(dummy) will return "wotsit".
    //   Affinity is determined by the "declared type" according
    //   to the rules in section 2.1 of http://sqlite.org/datatype3.html
    //   So what's really relevant is what CamCOPS uses as the declared
    //   types when creating fields!
    // camcopsType will be one of: DBCONSTANTS.TYPE_*, which are just
    //   one-letter identifiers.
    //   The critical mapping, therefore, is in columnDefSQL(). What follows
    //   must match it.
    switch (camcopsType) {
    case DBCONSTANTS.TYPE_PK:
    case DBCONSTANTS.TYPE_BOOLEAN:
    case DBCONSTANTS.TYPE_INTEGER:
    case DBCONSTANTS.TYPE_BLOBID:
        return (sqliteType === "INTEGER");

    case DBCONSTANTS.TYPE_BIGINT:
        // Workaround because Titanium doesn't support big integers; see
        // VERSION_TRACKER.txt, and columnDefSQL().
        return (sqliteType === "REAL");

    case DBCONSTANTS.TYPE_REAL:
        return (sqliteType === "REAL");

    case DBCONSTANTS.TYPE_TEXT:
    case DBCONSTANTS.TYPE_DATETIME:
    case DBCONSTANTS.TYPE_DATE:
        return (sqliteType === "TEXT");

    default:
        return false;
    }
}

function createTable(tablename, fieldlist) {
    Titanium.API.info("createTable: " + tablename);
    var plan = [],
        superfluous_fields = [],
        incorrect_type_fields = [],
        i,
        db,
        cursor,
        dummytablename = delimit(tablename + "_temp"),
        origtable = delimit(tablename),
        goodFieldsArray = [],
        goodFieldList,
        superfluous,
        name,
        type,
        s;
    for (i = 0; i < fieldlist.length; ++i) {
        if (!fieldTypeValid(fieldlist[i])) {
            throw new Error("field type invalid: " +
                            JSON.stringify(fieldlist[i]));
        }
        plan.push({
            field: fieldlist[i],
            // then extras:
            exists_in_db: false,
            correct: false,
        });
    }
    db = Titanium.Database.open(DBCONSTANTS.DBNAME);
    execute_noreturn(db, getCreateTableSQL(tablename, fieldlist));
    cursor = db.execute(getPragmaInfoSQL(tablename));
    while (cursor.isValidRow()) {
        superfluous = true;
        // see getPragmaInfo() for full details
        name = cursor.field(1);
        type = cursor.field(2);
        for (i = 0; i < plan.length; ++i) {
            if (name === plan[i].field.name) {
                plan[i].exists_in_db = true;
                plan[i].correct = fieldTypeMatches(type, plan[i].field.type);
                plan[i].dbtype = type;
                superfluous = false;
            }
        }
        if (superfluous) {
            superfluous_fields.push(name);
        }
        cursor.next();
    }
    cursor.close();

    for (i = 0; i < plan.length; ++i) {
        if (!plan[i].exists_in_db) {
            if (plan[i].field.type === DBCONSTANTS.TYPE_PK) {
                Titanium.API.warn("createTable: Cannot add PK. Table=" +
                                  tablename + ", field=" + plan[i].field.name);
            } else {
                s = addColumnSQL(tablename, plan[i].field);
                Titanium.API.trace("createTable: About to execute: " + s);
                execute_noreturn(db, s);
            }
        } else if (!plan[i].correct) {
            Titanium.API.warn("createTable: Field type wrong. Table=" +
                              tablename +
                              ", field=" + plan[i].field.name +
                              ", intended type=" + plan[i].field.type +
                              ", database type=" + plan[i].dbtype);
            incorrect_type_fields.push(plan[i].field.name);
        }
    }

    // Deleting columns: http://www.sqlite.org/faq.html#q11
    // ... also http://stackoverflow.com/questions/8442147/
    // Basically, requires (a) copy data to temporary table; (b) drop original;
    // (c) create new; (d) copy back.
    // Or, another method: (a) rename table; (b) create new; (c) copy data
    // across; (d) drop temporary.
    // We deal with fields of incorrect type similarly (in this case, any
    // conversion occurs as we SELECT back the values into the new, proper
    // fields). Not sure it really is important, though:
    /// http://sqlite.org/datatype3.html
    if (superfluous_fields.length > 0) {
        Titanium.API.info("createTable: Dropping superfluous database " +
                          "fields. Table=" + tablename + ", fields: " +
                          superfluous_fields.join(", "));
    }
    if (incorrect_type_fields.length > 0) {
        Titanium.API.info("createTable: Fixing fields of incorrect type. " +
                          "Table=" + tablename + ", fields: " +
                          superfluous_fields.join(", "));
    }
    if (superfluous_fields.length > 0 || incorrect_type_fields.length > 0) {
        for (i = 0; i < fieldlist.length; ++i) {
            goodFieldsArray.push(delimit(fieldlist[i].name));
        }
        goodFieldList = goodFieldsArray.join(",");
        execute_noreturn(db, "BEGIN TRANSACTION");
        execute_noreturn(db, "ALTER TABLE " + origtable +
                             " RENAME TO " + dummytablename);
        // make a new clean table
        execute_noreturn(db, getCreateTableSQL(tablename, fieldlist));
        // copy data across
        execute_noreturn(db,
                         "INSERT INTO " + origtable + " (" + goodFieldList +
                         ") SELECT " + goodFieldList + " FROM " + dummytablename);
        execute_noreturn(db, "DROP TABLE " + dummytablename);
        execute_noreturn(db, "COMMIT");
    }

    db.close();
}
exports.createTable = createTable;


function createIndex(indexname, tablename, fieldnamelist) {
    var delimitedfields = [],
        i,
        sql;
    for (i = 0; i < fieldnamelist.length; ++i) {
        delimitedfields.push(delimit(fieldnamelist[i]));
    }
    sql = "CREATE INDEX IF NOT EXISTS " + delimit(indexname) + " ON " +
        delimit(tablename) + " (" + delimitedfields.join(", ") + ")";
    Titanium.API.trace(sql);
    standalone_execute_noreturn(sql);
}
exports.createIndex = createIndex;


function renameColumns(tablename, from_to_list) {
    Titanium.API.info("renameColumns()");
    // TRUSTS ITS INPUT, more or less.
    if (!tableExists(tablename)) {
        Titanium.API.warn("renameColumns: nonexistent table: " + tablename);
        return;
    }
    var creation_sql = getCreateTableSQLFromDatabase(tablename),
        old_fieldnames = getFieldNames(tablename),
        new_fieldnames = old_fieldnames.slice(),  // make a copy
        i,
        j,
        oldfieldarray = [],
        newfieldarray = [],
        oldfieldlist,
        newfieldlist,
        db,
        tempsuffix = "_temp",
        dummytablename = delimit(tablename + tempsuffix),
        origtable = delimit(tablename),
        nchanges = 0;
    if (tableExists(tablename + tempsuffix)) {
        throw new Error("renameColumns: temporary table already exists");
    }
    for (i = 0; i < from_to_list.length; ++i) { // For each rename...
        // Check the destination doesn't exist already
        for (j = 0; j < old_fieldnames.length; ++j) {
            if (from_to_list[i].to === old_fieldnames[j]) {
                throw new Error("renameColumns: destination field exists!");
            }
        }
        // Rename the fieldname in the new_fieldnames list, and the SQL
        for (j = 0; j < new_fieldnames.length; ++j) {
            if (new_fieldnames[j] === from_to_list[i].from) {
                new_fieldnames[j] = from_to_list[i].to;
                creation_sql = creation_sql.replace(
                    '"' + old_fieldnames[j] + '"',
                    '"' + new_fieldnames[j] + '"'
                );
                nchanges += 1;
            }
        }
    }
    if (nchanges === 0) {
        Titanium.API.info("nothing to do");
        return;
    }
    Titanium.API.trace("tablename: " + tablename);
    Titanium.API.trace("from_to_list: " + JSON.stringify(from_to_list));
    Titanium.API.trace("old_fieldnames: " + JSON.stringify(old_fieldnames));
    Titanium.API.trace("new_fieldnames: " + JSON.stringify(new_fieldnames));
    // Set up comma-separated list of delimited fieldnames
    for (i = 0; i < old_fieldnames.length; ++i) {
        oldfieldarray.push(delimit(old_fieldnames[i]));
        newfieldarray.push(delimit(new_fieldnames[i]));
    }
    oldfieldlist = oldfieldarray.join(",");
    newfieldlist = newfieldarray.join(",");
    // Right, let's do this.
    db = Titanium.Database.open(DBCONSTANTS.DBNAME);
    trace_execute_noreturn(db, "BEGIN TRANSACTION");
    trace_execute_noreturn(db, "ALTER TABLE " + origtable +
                               " RENAME TO " + dummytablename);
    trace_execute_noreturn(db, creation_sql); // make a new clean table
    trace_execute_noreturn(db,
                           "INSERT INTO " + origtable + " (" + newfieldlist +
                           ") SELECT " + oldfieldlist +
                           " FROM " + dummytablename);
    // ... copy data across
    trace_execute_noreturn(db, "DROP TABLE " + dummytablename);
    trace_execute_noreturn(db, "COMMIT");
    db.close();
}
exports.renameColumns = renameColumns;

function getPragmaInfo(tablename) {
    Titanium.API.trace("getPragmaInfo()");
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor = db.execute(getPragmaInfoSQL(tablename)),
        info = [],
        item;
    while (cursor.isValidRow()) {
        item = {
            cid: cursor.field(0), // numeric
            name: cursor.field(1), // text
            type: cursor.field(2), // text
            notnull: cursor.field(3), // 0 or 1
            dflt_value: cursor.field(4), // may be null
            pk: cursor.field(5), // 0 or 1
        };
        info.push(item);
        cursor.next();
    }
    cursor.close();
    db.close();
    return info;
}

function makeCreationSQLFromPragmaInfo(tablename, info) {
    var sql = "CREATE TABLE IF NOT EXISTS " + delimit(tablename) + " (",
        fieldspecs = [],
        i,
        elements;
    for (i = 0; i < info.length; ++i) {
        elements = [
            delimit(info[i].name),
            info[i].type
        ];
        if (info[i].notnull) {
            elements.push("NOT NULL");
        }
        if (info[i].dflt_value !== null) {
            elements.push("DEFAULT " + info[i].dflt_value);
            // default value already delimited by SQLite
        }
        if (info[i].pk) {
            elements.push("PRIMARY KEY");
        }
        fieldspecs.push(elements.join(" "));
    }
    sql += fieldspecs.join(", ");
    sql += ")";
    return sql;
}

function changeColumnTypes(tablename, changes) {
    // changes: list of {column: X, newtype: Y} objects
    // TRUSTS ITS INPUT, more or less.
    Titanium.API.info("changeColumnTypes()");
    if (!tableExists(tablename)) {
        Titanium.API.warn("changeColumnTypes: nonexistent table: " +
                          tablename);
        return;
    }
    var tableinfo = getPragmaInfo(tablename),
        fieldnames = getFieldNames(tablename),
        origtable = delimit(tablename),
        tempsuffix = "_temp",
        dummytablename = delimit(tablename + tempsuffix),
        nchanges = 0,
        fieldarray = [],
        fieldlist,
        i,
        j,
        db,
        creation_sql;
    if (tableExists(tablename + tempsuffix)) {
        throw new Error("changeColumnTypes: temporary table already exists");
    }
    Titanium.API.info("pragma info: " + JSON.stringify(tableinfo));
    Titanium.API.info("changes: " + JSON.stringify(changes));
    // Things to do?
    for (i = 0; i < changes.length; ++i) {
        for (j = 0; j < tableinfo.length; ++j) {
            if (changes[i].column.toLowerCase() ===
                    tableinfo[j].name.toLowerCase()) {
                tableinfo[j].type = changes[i].newtype;
                nchanges += 1;
            }
        }
    }
    if (nchanges === 0) {
        Titanium.API.info("nothing to do");
        return;
    }
    creation_sql = makeCreationSQLFromPragmaInfo(tablename, tableinfo);
    // Create comma-separated list of delimited fieldnames
    for (i = 0; i < fieldnames.length; ++i) {
        fieldarray.push(delimit(fieldnames[i]));
    }
    fieldlist = fieldarray.join(",");
    // Right, let's do this.
    db = Titanium.Database.open(DBCONSTANTS.DBNAME);
    trace_execute_noreturn(db, "BEGIN TRANSACTION");
    trace_execute_noreturn(db, "ALTER TABLE " + origtable +
                               " RENAME TO " + dummytablename);
    trace_execute_noreturn(db, creation_sql); // make a new clean table
    trace_execute_noreturn(db,
                           "INSERT INTO " + origtable + " (" + fieldlist +
                           ") SELECT " + fieldlist +
                           " FROM " + dummytablename);
    // ... copy data across
    trace_execute_noreturn(db, "DROP TABLE " + dummytablename);
    trace_execute_noreturn(db, "COMMIT");
    db.close();
}
exports.changeColumnTypes = changeColumnTypes;

function renameTable(from, to) {
    // TRUSTS ITS INPUT.
    if (!tableExists(from)) {
        return;
    }
    if (tableExists(to)) {
        throw new Error("renameTable (from " + from + " to " + to + "): " +
                        "destination table already exists!");
    }
    // http://stackoverflow.com/questions/426495
    standalone_execute_noreturn("ALTER TABLE " + from + " RENAME TO " + to);
    // don't COMMIT (error: "cannot commit - no transaction is active")
}
exports.renameTable = renameTable;

//=============================================================================
// Fetch operations
//=============================================================================

function isInDatabaseByPK(tablename, pkname, pkval) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    if (pkval === undefined || pkval === null) {
        return false;
    }
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor,
        isPresent;
    // requireTableWithDbOpen(db, tablename, arguments);
    cursor = db.execute(countByKeySQL(tablename, pkname), pkval);
    // http://stackoverflow.com/questions/1930499/
    // Javascript short-circuits condition checks, so this is safe:
    isPresent = cursor.isValidRow() && (cursor.field(0) > 0);
    cursor.close();
    db.close();
    return isPresent;
}
exports.isInDatabaseByPK = isInDatabaseByPK;

function readFromUniqueField(tablename, fieldlist, object, keyname, keyval) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    if (!isInDatabaseByPK(tablename, keyname, keyval)) {
        return false;
    }
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor,
        success = false;
    // requireTableWithDbOpen(db, tablename, arguments);
    cursor = db.execute(getSelectByKeySQL(tablename, fieldlist, keyname),
                        keyval);
    if (cursor.isValidRow()) {
        setFromCursor(cursor, fieldlist, object);
        success = true;
    }
    cursor.close();
    db.close();
    return success;
}
exports.readFromUniqueField = readFromUniqueField;

function isInDatabaseByUniqueFieldCombination(tablename, wherefields,
                                              wherevalues) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        wherefieldnames = [],
        encodedvalues = [],
        i,
        cursor,
        isPresent;
    // requireTableWithDbOpen(db, tablename, arguments);
    for (i = 0; i < wherefields.length; ++i) {
        wherefieldnames.push(wherefields[i].name);
        encodedvalues.push(encodeValue(wherefields[i], wherevalues[i]));
    }
    cursor = db.execute(countByMultipleFieldsSQL(tablename, wherefieldnames),
                        encodedvalues);
    isPresent = cursor.isValidRow() && (cursor.field(0) > 0);
    cursor.close();
    db.close();
    return isPresent;
}
exports.isInDatabaseByUniqueFieldCombination = isInDatabaseByUniqueFieldCombination;

function readFromUniqueFieldCombination(tablename, fieldlist, object,
                                        fvpairs) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var wherefieldnames = [],
        wherevalues = [],
        fieldname,
        field,
        i,
        db,
        cursor,
        isPresent,
        success;
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
                throw new Error("dbsqlite.readFromUniqueFieldCombination: " +
                                fieldname + " not in fieldlist");
            }
            wherefieldnames.push(fieldname);
            wherevalues.push(encodeValue(field, fvpairs[fieldname]));
        }
    }

    db = Titanium.Database.open(DBCONSTANTS.DBNAME);
    // requireTableWithDbOpen(db, tablename, arguments);
    cursor = db.execute(countByMultipleFieldsSQL(tablename, wherefieldnames),
                        wherevalues);
    isPresent = cursor.isValidRow() && (cursor.field(0) > 0);
    success = isPresent;
    cursor.close();

    if (isPresent) {
        cursor = db.execute(getSelectByMultipleFieldsSQL(tablename,
                                                         fieldlist,
                                                         wherefieldnames),
                            wherevalues);
        if (!cursor.isValidRow()) {
            success = false;
        } else {
            setFromCursor(cursor, fieldlist, object);
        }
        cursor.close();
    }

    db.close();
    return success;
}
exports.readFromUniqueFieldCombination = readFromUniqueFieldCombination;

function getAllRows(tablename, fieldlist, Objecttype, orderby) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var rows = [],
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        sql = getSelectAllRowsSQL(tablename, fieldlist, orderby),
        cursor,
        o;
    // Titanium.API.debug("getAllRows: sql: " + sql);
    // requireTableWithDbOpen(db, tablename, arguments);
    cursor = db.execute(sql);
    while (cursor.isValidRow()) {
        o = new Objecttype();
        setFromCursor(cursor, fieldlist, o);
        // Titanium.API.debug("getAllRows: read: " + JSON.stringify(o));
        rows.push(o);
        cursor.next();
    }
    cursor.close();
    db.close();
    return rows;
}
exports.getAllRows = getAllRows;

function getAllRowsByKey(keyname, keyvalue, tablename, fieldlist, Objecttype,
                         orderby) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    if (keyvalue === null) {
        throw new Error("getAllRowsByKey() called with keyvalue = null");
    }
    //Titanium.API.debug("getAllRowsByKey(" +
    //                   Array.prototype.slice.call(arguments).join(", ")
    //                   + ")");
    var rows = [],
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor,
        o;
    // requireTableWithDbOpen(db, tablename, arguments);
    cursor = db.execute(getSelectByKeySQL(tablename, fieldlist, keyname,
                                          orderby),
                        keyvalue);
    while (cursor.isValidRow()) {
        o = new Objecttype();
        setFromCursor(cursor, fieldlist, o);
        rows.push(o);
        cursor.next();
    }
    cursor.close();
    db.close();
    return rows;
}
exports.getAllRowsByKey = getAllRowsByKey;

function getAllPKs(tablename, pkname, orderby) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var pks = [],
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        sql = "SELECT " + delimit(pkname) + " FROM " + delimit(tablename),
        cursor;
    if (orderby) {
        sql += " ORDER BY " + delimit(orderby); // ***
    }
    // requireTableWithDbOpen(db, tablename, arguments);
    cursor = db.execute(sql);
    while (cursor.isValidRow()) {
        pks.push(cursor.field(0));
        cursor.next();
    }
    cursor.close();
    db.close();
    return pks;
}
exports.getAllPKs = getAllPKs;

function getAllPKsByKey(tablename, pkname, orderby, keyname, keyvalue) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var pks = [],
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        sql = ("SELECT " + delimit(pkname) + " FROM " + delimit(tablename) +
               " WHERE " + delimit(keyname) + "=?"),
        cursor;
    if (orderby) {
        sql += " ORDER BY " + orderby;
    }
    // requireTableWithDbOpen(db, tablename, arguments);
    cursor = db.execute(sql, keyvalue);
    while (cursor.isValidRow()) {
        pks.push(cursor.field(0));
        cursor.next();
    }
    cursor.close();
    db.close();
    return pks;
}
exports.getAllPKsByKey = getAllPKsByKey;

function getPKsAndDates(tablename, pkname, datefieldname) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var pks = [],
        dates = [],
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        sql = ("SELECT " + delimit(pkname) + ", " + delimit(datefieldname) +
               " FROM " + delimit(tablename)),
        cursor;
    // requireTableWithDbOpen(db, tablename, arguments);
    cursor = db.execute(sql);
    while (cursor.isValidRow()) {
        pks.push(cursor.field(0));
        dates.push(cursor.field(1));
        cursor.next();
    }
    cursor.close();
    db.close();
    return {
        pks: pks,
        dates: dates
    };
}
exports.getPKsAndDates = getPKsAndDates;

function getSingleValueByKey(tablename, keyname, keyvalue, field) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var sql = ("SELECT " + delimit(field.name) + " FROM " +
               delimit(tablename) + " WHERE " + delimit(keyname) + "=?"),
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor,
        value = null;
    // requireTableWithDbOpen(db, tablename, arguments);
    cursor = db.execute(sql, keyvalue);
    if (cursor.isValidRow()) {
        value = decodeValue(field, cursor.field(0));
    }
    cursor.close();
    db.close();
    return value;
}
exports.getSingleValueByKey = getSingleValueByKey;

function countWhere(tablename, wherefields, wherevalues, wherenotfields,
                    wherenotvalues) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var whereclauses = [],
        args = [],
        value,
        i,
        sql = "SELECT COUNT(*) FROM " + delimit(tablename),
        db,
        cursor,
        count = null;
    if (wherenotfields === undefined) {
        wherenotfields = [];
    }
    if (wherenotvalues === undefined) {
        wherenotvalues = [];
    }
    if (wherefields.length !== wherevalues.length ||
            wherenotfields.length !== wherenotvalues.length) {
        throw new Error("dbsqlite.countWhere: invalid parameters");
    }
    for (i = 0; i < wherefields.length; ++i) {
        value = encodeValue(wherefields[i], wherevalues[i]);
        if (value === null) {
            whereclauses.push(delimit(wherefields[i].name) + " IS NULL");
        } else {
            whereclauses.push(delimit(wherefields[i].name) + "=?");
            args.push(value);
        }
    }
    for (i = 0; i < wherenotfields.length; ++i) {
        value = encodeValue(wherenotfields[i], wherenotvalues[i]);
        if (value === null) {
            whereclauses.push(delimit(wherenotfields[i].name) +
                              " IS NOT NULL");
        } else {
            whereclauses.push(delimit(wherenotfields[i].name) + "<>?");
            args.push(value);
        }
    }
    if (whereclauses.length > 0) {
        sql += " WHERE " + whereclauses.join(" AND ");
    }
    db = Titanium.Database.open(DBCONSTANTS.DBNAME);
    // requireTableWithDbOpen(db, tablename, arguments);
    //Titanium.API.trace("countWhere: sql: " + sql);
    //Titanium.API.trace("countWhere: args: " + args);
    cursor = db.execute(sql, args);
    if (cursor.isValidRow()) {
        count = cursor.field(0);
    }
    cursor.close();
    db.close();
    return count;
}
exports.countWhere = countWhere;

//=============================================================================
// Insert/update operations
//=============================================================================

/*
function insertOrReplaceRow(tablename, fieldlist, object) {
    if (!dbcore.readyToSave(fieldlist, object)) return false;
    var pkname = fieldlist[0].name;
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME);
    var args = [];
    args.push( getInsertOrReplaceSQL(tablename, fieldlist) );
    appendFieldValueArgs(args, fieldlist, object, 0);
    db.execute.apply(db, args);
    object[pkname] = db.lastInsertRowId;
    db.close();
    return true;
};
exports.insertOrReplaceRow = insertOrReplaceRow;
*/

function createRow(tablename, fieldlist, object, pkname) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        query = getInsertSQL(tablename, fieldlist),
        args = getFieldValueArgs(fieldlist, object);
    // requireTableWithDbOpen(db, tablename, arguments);
    execute_noreturn(db, query, args);
    object[pkname] = db.lastInsertRowId;
    db.close();
    return true;
}
exports.createRow = createRow;

function updateByPK(tablename, fieldlist, object, pkname, pkval) {
    Titanium.API.info("updateByPK: tablename=" + tablename + ", fieldnames=" +
                      fieldnames_from_fieldspecs(fieldlist).join(",") +
                      ", pkname=" + pkname + ", pkval=" + pkval);
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var query = getUpdateByPKSQL(tablename, fieldlist, pkname),
        args = getFieldValueArgs(fieldlist, object);
    args.push(pkval);
    if (fieldlist.length <= 0) {
        Titanium.API.info("... updateByPK: nothing to do");
        return true;
    }
    standalone_execute_noreturn(query, args);
    Titanium.API.info("... updateByPK: done");
    return true;
}
exports.updateByPK = updateByPK;

function setSingleValueByKey(tablename, keyname, keyvalue, field, value) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var query = ("UPDATE " + delimit(tablename) + " SET " +
                 delimit(field.name) + "=? WHERE " + delimit(keyname) + "=?"),
        args = [encodeValue(field, value), keyvalue];
    standalone_execute_noreturn(query, args);
    return true;
}
exports.setSingleValueByKey = setSingleValueByKey;

//=============================================================================
// Delete operations
//=============================================================================

function deleteWhere(tablename, field, value) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    standalone_execute_noreturn(getDeleteByKeySQL(tablename, field.name),
                                encodeValue(field, value));
}
exports.deleteWhere = deleteWhere;

//=============================================================================
// Used for uploading
//=============================================================================

function getMainTables() {
    // We'll upload all tables except certain system ones:
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        query = ("SELECT name, sql FROM sqlite_master WHERE sql NOT NULL " +
                 "AND type=='table' AND name!='sqlite_sequence' " +
                 "AND name!='android_metadata' AND name!=? ORDER BY name"),
        cursor = db.execute(query, DBCONSTANTS.BLOB_TABLE),
        tables = [];
    while (cursor.isValidRow()) {
        tables.push({
            name: cursor.field(0),
            sql: cursor.field(1)
        });
        cursor.next();
    }
    cursor.close();
    db.close();
    return tables;
}
exports.getMainTables = getMainTables;

function getMainTableNames() {
    // We'll upload all tables except certain system ones:
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        query = ("SELECT name FROM sqlite_master WHERE sql NOT NULL " +
                 "AND type=='table' AND name<>'sqlite_sequence' " +
                 "AND name<>'android_metadata' AND name<>? ORDER BY name"),
        cursor = db.execute(query, DBCONSTANTS.BLOB_TABLE),
        tablenames = [];
    while (cursor.isValidRow()) {
        tablenames.push(cursor.field(0));
        cursor.next();
    }
    cursor.close();
    db.close();
    return tablenames;
}
exports.getMainTableNames = getMainTableNames;

function getAllTablesWithRecordCounts() {
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        tablequery = ("SELECT name FROM sqlite_master WHERE sql NOT NULL " +
                      "AND type=='table' AND name<>'sqlite_sequence' " +
                      "AND name<>'android_metadata' ORDER BY name"),
        recordcountqueryprefix = "SELECT COUNT(*) FROM ",
        cursor = db.execute(tablequery),
        table_names = [],
        record_counts = [],
        i;
    while (cursor.isValidRow()) {
        table_names.push(cursor.field(0));
        cursor.next();
    }
    cursor.close();

    for (i = 0; i < table_names.length; ++i) {
        cursor = db.execute(recordcountqueryprefix + table_names[i]);
        record_counts.push(cursor.field(0));
        cursor.close();
    }

    db.close();
    return {
        table_names: table_names,
        record_counts: record_counts
    };
}
exports.getAllTablesWithRecordCounts = getAllTablesWithRecordCounts;

function getNumRecords(tablename) {
    if (!tableExists(tablename)) {
        return 0;
    }
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        query = "SELECT COUNT(*) FROM " + delimit(tablename),
        cursor = db.execute(query),
        n = cursor.field(0);
    cursor.close();
    db.close();
    return n;
}
exports.getNumRecords = getNumRecords;

function getRecords(tablename) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var dbcore = require('lib/dbcore'),
        fieldnames = getFieldNames(tablename),
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        query = "SELECT ",
        i,
        cursor,
        records = [],
        ncols,
        r;
    for (i = 0; i < fieldnames.length; ++i) {
        if (i > 0) {
            query += ",";
        }
        query += "quote(" + delimit(fieldnames[i]) + ")";
    }
    query += " FROM " + delimit(tablename);
    // Titanium.API.trace("getRecords: query = " + query);
    cursor = db.execute(query);
    while (cursor.isValidRow()) {
        ncols = dbcore.getFieldCount(cursor);
        r = "";
        for (i = 0; i < ncols; ++i) {
            if (i > 0) {
                r += ",";
            }
            r += cursor.field(i);
        }
        records.push(r);
        cursor.next();
    }
    cursor.close();
    db.close();
    return records;
}
exports.getRecords = getRecords;

function getRecords_lowmem(tablename, dict, keyprefix, countkey) {
    // Pass-by-reference version
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var dbcore = require('lib/dbcore'),
        fieldnames = getFieldNames(tablename),
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor,
        query = "SELECT ",
        i,
        recordIndex = 0,
        ncols;
    for (i = 0; i < fieldnames.length; ++i) {
        if (i > 0) {
            query += ",";
        }
        query += "quote(" + delimit(fieldnames[i]) + ")";
    }
    query += " FROM " + delimit(tablename);
    // Titanium.API.trace("getRecords_lowmem: query = " + query);
    dict[countkey] = 0; // in case we retrieve no records
    cursor = db.execute(query);
    while (cursor.isValidRow()) {
        dict[countkey] = recordIndex + 1;
        dict[keyprefix + recordIndex] = "";
        ncols = dbcore.getFieldCount(cursor);
        for (i = 0; i < ncols; ++i) {
            if (i > 0) {
                dict[keyprefix + recordIndex] += ",";
            }
            dict[keyprefix + recordIndex] += cursor.field(i);
        }
        ++recordIndex;
        cursor.next();
    }
    cursor.close();
    db.close();
}
exports.getRecords_lowmem = getRecords_lowmem;

function getRecordByPK(tablename, fieldnames, pkname, pkval) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var dbcore = require('lib/dbcore'),
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor,
        query = "SELECT ",
        i,
        r = "",
        ncols;
    for (i = 0; i < fieldnames.length; ++i) {
        if (i > 0) {
            query += ",";
        }
        query += "quote(" + delimit(fieldnames[i]) + ")";
    }
    query += (" FROM " + delimit(tablename) +
              " WHERE " + delimit(pkname) + "=?");
    // Titanium.API.trace("getRecordByPK: query = " + query);
    cursor = db.execute(query, pkval);
    if (cursor.isValidRow()) {
        ncols = dbcore.getFieldCount(cursor);
        for (i = 0; i < ncols; ++i) {
            if (i > 0) {
                r += ",";
            }
            r += cursor.field(i);
        }
    }
    cursor.close();
    db.close();
    return r;
}
exports.getRecordByPK = getRecordByPK;

function getRecordByPK_lowmem(tablename, fieldnames, pkname, pkval, dict,
                              key) {
    // Pass-by-reference version
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var dbcore = require('lib/dbcore'),
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        query = "SELECT ",
        i,
        ncols,
        cursor;
    for (i = 0; i < fieldnames.length; ++i) {
        if (i > 0) {
            query += ",";
        }
        query += "quote(" + delimit(fieldnames[i]) + ")";
    }
    query += (" FROM " + delimit(tablename) +
              " WHERE " + delimit(pkname) + "=?");
    // Titanium.API.trace("getRecordByPK_lowmem: query = " + query);
    cursor = db.execute(query, pkval);
    dict[key] = "";
    if (cursor.isValidRow()) {
        ncols = dbcore.getFieldCount(cursor);
        for (i = 0; i < ncols; ++i) {
            if (i > 0) {
                dict[key] += ",";
            }
            dict[key] += cursor.field(i);
            // Titanium.API.trace("getRecordByPK_lowmem: key = " + key +
            //                    ", dict now = " + dict[key] );
        }
    }
    cursor.close();
    db.close();
}
exports.getRecordByPK_lowmem = getRecordByPK_lowmem;

function getPKs(tablename, pkname) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        query = ("SELECT " + delimit(pkname) +
                 " FROM " + delimit(tablename) +
                 " ORDER BY " + delimit(pkname)),
        cursor = db.execute(query),
        pks = [];
    while (cursor.isValidRow()) {
        pks.push(cursor.field(0));
        cursor.next();
    }
    cursor.close();
    db.close();
    return pks;
}
exports.getPKs = getPKs;

function getFieldOrderedByPK(tablename, fieldname, pkname) {
    // Order must match getPKs
    // WILL CRASH IF TABLE DOESN'T EXIST.
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        query = ("SELECT quote(" + delimit(fieldname) +
                 ") FROM " + delimit(tablename) +
                 " ORDER BY " + delimit(pkname)),
        cursor = db.execute(query),
        dates = [];
    while (cursor.isValidRow()) {
        dates.push(cursor.field(0));
        cursor.next();
    }
    cursor.close();
    db.close();
    return dates;
}
exports.getFieldOrderedByPK = getFieldOrderedByPK;

//=============================================================================
// Table deletion
//=============================================================================

function dropTable(tablename) {
    Titanium.API.info("DROPPING TABLE: " + tablename);
    standalone_execute_noreturn("DROP TABLE IF EXISTS " + delimit(tablename));
}
exports.dropTable = dropTable;

function deleteAllRecordsFromTable(tablename) {
    // WILL CRASH IF TABLE DOESN'T EXIST.
    Titanium.API.info("DELETING ALL FROM TABLE: " + tablename);
    standalone_execute_noreturn("DELETE FROM " + delimit(tablename));
}

function deleteAllBlobs() {
    // clear out blobs individually, so their files are deleted:
    var Blob = require('table/Blob'), // ensures blob table exists first!
        blob_pks = getPKs(DBCONSTANTS.BLOB_TABLE, DBCONSTANTS.BLOB_PKNAME),
        i,
        b;
    Titanium.API.info("deleteAllBlobs()");
    for (i = 0; i < blob_pks.length; ++i) {
        b = new Blob(blob_pks[i]);
        b.deleteBlob(); // ... which will delete the associated file
    }
}
exports.deleteAllBlobs = deleteAllBlobs;

function zapDatabase(drop, leaveStoredVars, leavePatients) {
    var lang = require('lib/lang'),
        Blob,
        dummyblob,
        tablenames = getMainTableNames(),
        i;
    if (drop === undefined) {
        drop = false;
    }
    if (leaveStoredVars === undefined) {
        leaveStoredVars = false;
    }
    if (leavePatients === undefined) {
        leavePatients = false;
    }
    Titanium.API.info("WIPING DATABASE: drop = " + drop +
                      ", leaveStoredVars = " + leaveStoredVars +
                      ", leavePatients = " + leavePatients);
    if (leaveStoredVars) {
        lang.removeFromArrayByValue(tablenames,
                                    DBCONSTANTS.STOREDVARS_TABLE);
        lang.removeFromArrayByValue(tablenames,
                                    DBCONSTANTS.STOREDVARS_PRIVATE_TABLE);
    }
    if (leavePatients) {
        lang.removeFromArrayByValue(tablenames, DBCONSTANTS.PATIENT_TABLE);
    }
    for (i = 0; i < tablenames.length; ++i) {
        if (drop) {
            dropTable(tablenames[i]);
        } else {
            deleteAllRecordsFromTable(tablenames[i]);
        }
    }
    deleteAllBlobs();
    if (drop) {
        dropTable(DBCONSTANTS.BLOB_TABLE);
        // but we must recreate it (and the blob.js may be cached, so it won't
        // redo it automatically)
        Blob = require('table/Blob');
        dummyblob = new Blob();
        dummyblob.recreateTable();
    } else {
        deleteAllRecordsFromTable(DBCONSTANTS.BLOB_TABLE);
    }
}

function dropDatabase() {
    zapDatabase(true, false);
}
exports.dropDatabase = dropDatabase;

function dropDatabaseNotStoredVars() {
    zapDatabase(true, true);
}
exports.dropDatabaseNotStoredVars = dropDatabaseNotStoredVars;

function wipeDatabaseEntirely() {
    zapDatabase(false, false);
}
exports.wipeDatabaseEntirely = wipeDatabaseEntirely;

function wipeDatabaseNotStoredVars() {
    zapDatabase(false, true);
}
exports.wipeDatabaseNotStoredVars = wipeDatabaseNotStoredVars;

function wipeDatabaseNotStoredVarsOrPatients() {
    zapDatabase(false, true, true);
}
exports.wipeDatabaseNotStoredVarsOrPatients = wipeDatabaseNotStoredVarsOrPatients;

function clearMoveOffTabletRecords(tablenames) {
    // Blobs -- ensure we delete the actual BLOB, too...
    var Blob = require('table/Blob'), // ensures blob table exists first!
        blob_pks = getPKs(DBCONSTANTS.BLOB_TABLE, DBCONSTANTS.BLOB_PKNAME),
        i,
        b,
        tablename,
        sql,
        db;
    for (i = 0; i < blob_pks.length; ++i) {
        b = new Blob(blob_pks[i]);
        if (b.getMoveOffTablet()) {
            b.deleteBlob(); // ... which will delete the associated file
        }
    }
    // Everything else
    db = Titanium.Database.open(DBCONSTANTS.DBNAME);
    for (i = 0; i < tablenames.length; ++i) {
        tablename = tablenames[i];
        if (tableExists(tablename)) {
            sql = ("DELETE FROM " + delimit(tablename) +
                   " WHERE " + DBCONSTANTS.MOVE_OFF_TABLET_FIELDNAME);
            execute_noreturn(db, sql);
        }
    }
    db.close();
}
exports.clearMoveOffTabletRecords = clearMoveOffTabletRecords;

//=============================================================================
// Other upload functions
//=============================================================================

function copyDescriptorsToPatients() {
    Titanium.API.trace("dbsqlite.copyDescriptorsToPatients()");
    var storedvars = require('table/storedvars'),
        db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        i,
        sql;
    require('table/Patient'); // ensures patient table exists!
    for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
        sql = ("UPDATE " + DBCONSTANTS.PATIENT_TABLE +
               " SET " + DBCONSTANTS.IDDESC_FIELD_PREFIX + i + " = ?");
        execute_noreturn(db, sql,
                         storedvars["idDescription" + i].getValue());
        sql = ("UPDATE " + DBCONSTANTS.PATIENT_TABLE +
               " SET " + DBCONSTANTS.IDSHORTDESC_FIELD_PREFIX + i + " = ?");
        execute_noreturn(db, sql,
                         storedvars["idShortDescription" + i].getValue());
    }
    db.close();
}
exports.copyDescriptorsToPatients = copyDescriptorsToPatients;
