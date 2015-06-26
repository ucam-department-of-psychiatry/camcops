// dbdump.js

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

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcore = require('lib/dbcore'),
    dbsqlite = require('lib/dbsqlite'),
    NL = "\n", // newline
    DUMP_T_START = ("PRAGMA foreign_keys=OFF;" + NL +
                    "BEGIN TRANSACTION;" + NL),
    DUMP_Q_1 = ("SELECT name, type, sql FROM sqlite_master " +
                "WHERE sql NOT NULL AND type=='table' " +
                "AND name!='sqlite_sequence' ORDER BY name"),
    DUMP_Q_2 = ("SELECT name, type, sql FROM sqlite_master " +
                "WHERE name=='sqlite_sequence'"),
    DUMP_Q_3 = ("SELECT sql FROM sqlite_master WHERE sql NOT NULL " +
                "AND type IN ('index','trigger','view')"),
    DUMP_E_START_1 = "SAVEPOINT dump;",
    DUMP_E_START_2 = "PRAGMA writable_schema=ON;",
    DUMP_E_WSOFF = "PRAGMA writable_schema=OFF;",
    DUMP_E_RELEASE = "RELEASE dump;",
    DUMP_T_WSOFF = "PRAGMA writable_schema=OFF;" + NL,
    DUMP_T_WSON = "PRAGMA writable_schema=ON;" + NL,
    DUMP_T_END_FAILURE = "ROLLBACK; -- due to errors" + NL,
    DUMP_T_END_SUCCESS = "COMMIT;" + NL,
    DUMP_T_SQL_TERMINATOR = ";" + NL,
    TYPE_SEQUENCE = "sqlite_sequence",
    DELETE_SEQUENCES = "DELETE FROM sqlite_sequence;" + NL,
    STAT1 = "sqlite_stat1",
    ANALYSE_MASTER = "ANALYZE sqlite_master;" + NL,
    PREFIX = "sqlite_",
    CREATE_VT = "CREATE VIRTUAL TABLE",
    INSERT_INTO_MASTER = ("INSERT INTO sqlite_master(type,name,tbl_name," +
                        "rootpage,sql) VALUES('table','%','%',0,'%');" + NL),
    PLACEHOLDER = "%",
    // ... we'll replace with a regex-based function, so don't use "?"
    TYPE_TABLE = "table",
    PRAGMA_TABLEINFO = "PRAGMA table_info(\"%\");",
    DATASELECT_1_SELECT_INSERT_INTO_VALUES = (
        "SELECT 'INSERT INTO ' || '\"%\"' || ' VALUES(' || "
    ),
    DATASELECT_2_QUOTE = "quote(\"%\")",
    DATASELECT_3_FROM = "|| ')' FROM \"%\"",
    COMMENT_STARTING = NL + "-- Starting" + NL + NL,
    COMMENT_TABLES = NL + "-- Tables" + NL + NL,
    COMMENT_SEQUENCES = NL + "-- Sequences" + NL + NL,
    COMMENT_OTHER = NL + "-- Indexes, triggers, views" + NL + NL,
    COMMENT_ENDING = NL + "-- Ending" + NL + NL,
    // For comments "-- ", the space isn't standard SQL but some engines need it.
    GET_VERSION = "SELECT sqlite_version() FROM sqlite_master";

function DumpResults() {
    this.result = "";
    this.writableSchema = false;
}

function stringOneBeginsWithStringTwo(one, two) {
    return (one.indexOf(two) === 0);
}

function stringOneContainsStringTwo(one, two) {
    return (one.indexOf(two) !== -1);
}

function run_table_dump_query(db, sql, firstrow) {
    var r = new DumpResults(), // results
        c = db.execute(sql), // cursor
        i,
        ncols;
    if (c.isValidRow()) {
        r.result += firstrow;
        ncols = dbcore.getFieldCount(c);
        do {
            for (i = 0; i < ncols; ++i) {
                if (i > 0) {
                    r.result += ",";
                }
                r.result += c.field(i);
            }
            if (ncols === 1 && stringOneContainsStringTwo(c.field(0), "--")) {
                r.result += NL; // so comments don't subsume the final ";"
            }
            r.result += DUMP_T_SQL_TERMINATOR;
            c.next();
        } while (c.isValidRow());
    }
    c.close();
    return r;
}

/*jslint continue: true */
function run_schema_dump_query(db, query, writableSchema) {
    var r = new DumpResults(),
        c = db.execute(query), // cursor
        firstline,
        table,
        type,
        sql,
        prepstatement,
        tableinfo_query,
        c2,
        rows,
        select,
        first,
        text,
        r2,
        ins;
    r.writableSchema = writableSchema;
    if (c.isValidRow()) {
        firstline = true;
        do {
            table = c.field(0);
            type = c.field(1);
            sql = c.field(2);
            if (!firstline) {
                r.result += NL;
            }
            firstline = false;
            prepstatement = "";
            if (table === TYPE_SEQUENCE) {
                prepstatement = DELETE_SEQUENCES;
            } else if (table === STAT1) {
                r.result += ANALYSE_MASTER;
            } else if (stringOneBeginsWithStringTwo(table, PREFIX)) {
                continue;
            }
            if (stringOneBeginsWithStringTwo(sql, CREATE_VT)) {
                if (!writableSchema) {
                    r.result += DUMP_T_WSON;
                    r.writableSchema = true;
                }
                ins = INSERT_INTO_MASTER;
                ins = ins.replace(PLACEHOLDER, table);
                ins = ins.replace(PLACEHOLDER, table);
                ins = ins.replace(PLACEHOLDER, sql);
                // ... seems to handle e.g. escaped quotes correctly
                r.result += ins + DUMP_T_SQL_TERMINATOR;
                continue;
            }
            r.result += sql + DUMP_T_SQL_TERMINATOR;
            if (type === TYPE_TABLE) {
                tableinfo_query = PRAGMA_TABLEINFO.replace(PLACEHOLDER, table);
                c2 = db.execute(tableinfo_query);
                rows = c2.rowCount;
                if (rows > 0 && c2.isValidRow()) {
                    select = DATASELECT_1_SELECT_INSERT_INTO_VALUES.replace(
                        PLACEHOLDER,
                        table
                    );
                    first = true;
                    do {
                        if (!first) {
                            select += ",";
                        }
                        first = false;
                        text = c2.field(1);
                        select += DATASELECT_2_QUOTE.replace(PLACEHOLDER,
                                                             text);
                        c2.next();
                    } while (c2.isValidRow());
                    select += DATASELECT_3_FROM.replace(PLACEHOLDER, table);
                    r2 = run_table_dump_query(db, select, prepstatement);
                    r.result += r2.result;
                    // Doesn't deal with:
                    // if( rc==SQLITE_CORRUPT ){
                    //  zSelect = appendText(zSelect,
                    //                       " ORDER BY rowid DESC", 0);
                    //  run_table_dump_query(p, zSelect, 0);
                    // }
                }
            }
            c.next();
        } while (c.isValidRow());
    }
    c.close();
    return r;
}
/*jslint continue: false */

function dumpdatabase(dbname) {
    var db = Titanium.Database.open(dbname),
        s = COMMENT_STARTING + DUMP_T_START,
        success = true,
        writableSchema = false,
        dumpresult;
    dbsqlite.execute_noreturn(db, DUMP_E_START_1);
    dbsqlite.execute_noreturn(db, DUMP_E_START_2);

    // Tables
    s += COMMENT_TABLES;
    dumpresult = run_schema_dump_query(db, DUMP_Q_1, writableSchema);
    writableSchema = writableSchema || dumpresult.writableSchema;
    s += dumpresult.result;

    // Sequences
    s += COMMENT_SEQUENCES;
    dumpresult = run_schema_dump_query(db, DUMP_Q_2, writableSchema);
    writableSchema = writableSchema || dumpresult.writableSchema;
    s += dumpresult.result;

    // Indexes, triggers, views
    s += COMMENT_OTHER;
    dumpresult = run_table_dump_query(db, DUMP_Q_3, "");
    writableSchema = writableSchema || dumpresult.writableSchema;
    s += dumpresult.result;

    // Finishing
    s += COMMENT_ENDING;
    if (writableSchema) {
        s += DUMP_T_WSOFF;
    }
    dbsqlite.execute_noreturn(db, DUMP_E_WSOFF);
    dbsqlite.execute_noreturn(db, DUMP_E_RELEASE);
    s += (success ? DUMP_T_END_SUCCESS : DUMP_T_END_FAILURE);
    db.close();
    return s;
}
exports.dumpdatabase = dumpdatabase; // then add it to the exports list

function dump() {
    return dumpdatabase(DBCONSTANTS.DBNAME);
}
exports.dump = dump;

function sqlite_version() {
    var db = Titanium.Database.open(DBCONSTANTS.DBNAME),
        cursor = db.execute(GET_VERSION), // cursor
        version = "unknown";
    if (cursor.isValidRow()) {
        version = cursor.field(0);
    }
    cursor.close();
    db.close();
    return version;
}
exports.sqlite_version = sqlite_version;
