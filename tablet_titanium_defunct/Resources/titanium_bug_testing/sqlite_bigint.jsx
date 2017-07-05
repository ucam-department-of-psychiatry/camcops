/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var DBNAME = "junk.db",
    TESTVAL = 9876543210, // big enough to cause the bug
    db = Titanium.Database.open(DBNAME),
    cursor,
    x,
    workaround = false;

db.execute("DROP TABLE IF EXISTS t"); // so we can run this more than once
if (workaround) {
    db.execute("CREATE TABLE t (bignum)");
} else {
    db.execute("CREATE TABLE t (bignum INTEGER)");
}
db.execute("INSERT INTO t (bignum) VALUES (?)", TESTVAL);
// Check the database using the SQLite command line. Confirms: 9876543210.
cursor = db.execute("SELECT bignum FROM t");
x = cursor.field(0);
if (x === TESTVAL) {
    Titanium.API.debug("happy");
} else {
    Titanium.API.debug("oh dear; Titanium bug; x is now " + x);
}
// Check the database using the SQLite command line. Confirms: 9876543210.

// FIXED as of Titanium SDK 3.5.0 alpha (27 Nov 2014).
