/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var DBNAME = "junk.db",
    PKVAL = 1,
    ITERATIONS = 10000,
    REPORT_EVERY = 100,
    i;

// Returns a random number between min (inclusive) and max (exclusive)
function rnd(min, max) {
    return Math.random() * (max - min) + min;
}

function standalone_execute_noreturn(query, args) {
    var db = Titanium.Database.open(DBNAME),
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

function accessdb() {
    standalone_execute_noreturn(
        "UPDATE t SET value = ? WHERE pk = ?",
        [rnd(), PKVAL]
    );
}

function makedb() {
    standalone_execute_noreturn(
        "CREATE TABLE IF NOT EXISTS t (pk INTEGER, value INTEGER)"
    );
}

Titanium.API.info("starting");
makedb();
for (i = 0; i < ITERATIONS; ++i) {
    if (i % REPORT_EVERY === 0) {
        Titanium.API.info("iteration " + i);
    }
    accessdb();
}
Titanium.API.info("done");

// 2015-03-12: works fine.
