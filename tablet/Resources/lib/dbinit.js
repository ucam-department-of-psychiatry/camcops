// dbinit.js

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

/*jslint node: true, newcap: true */
/*global Titanium, L */

var platform = require('lib/platform'),
    DBCONSTANTS = require('common/DBCONSTANTS'),
    VERSION = require('common/VERSION'),
    dbsqlite,
    libfile,
    storedvars,
    prevversion,
    colchanges,
    i,
    UPGRADING_TO = "Upgrading database structure to v";

//=============================================================================
// DEBUGGING
//=============================================================================

if (platform.isDatabaseSupported) {
    dbsqlite = require('lib/dbsqlite');
    libfile = require('lib/libfile');

    //dbsqlite.dropDatabase();
    //libfile.deleteAllFilesInAppDataDirectory();

    Titanium.API.info("USING DATABASE: " + DBCONSTANTS.DBNAME);

    var db = Titanium.Database.open(DBCONSTANTS.DBNAME);
    if (platform.ios) {
        // https://wiki.appcelerator.org/m/view-rendered-page.action?abstractPageId=29004901
        db.file.setRemoteBackup(false);
    }

    /*
    // dbsqlite.renameColumns("phq9", [{from:"q1", to:"q1renamed"}]);
    // dbsqlite.execute_noreturn(db, "DROP TABLE clinicalclerking");
    // dbsqlite.execute_noreturn(db, "ALTER TABLE patient ADD COLUMN sex TEXT NOT NULL " +
    //            "DEFAULT 'M' " );
    // dbsqlite.execute_noreturn(db, "UPDATE demoquestionnaire SET date_only=NULL, date_time=NULL");
    // Titanium.API.trace("ABOUT TO DROP BLOBS");
    // dbsqlite.execute_noreturn(db, "DROP TABLE demoquestionnaire");
    // dbsqlite.execute_noreturn(db, "DROP TABLE expectationdetection");
    // dbsqlite.execute_noreturn(db, "DROP TABLE expectationdetection_trialgroupspec");
    // dbsqlite.execute_noreturn(db, "DROP TABLE expectationdetection_trials");
    // dbsqlite.execute_noreturn(db, "DROP TABLE qolsg");
    // dbsqlite.execute_noreturn(db, "CREATE TABLE testtable (testblob BLOB)");
    // dbsqlite.execute_noreturn(db, "INSERT INTO testtable VALUES ( randomblob(20) )");
    // dbsqlite.execute_noreturn(db, "DELETE FROM storedvars WHERE name='useClinical'");
    */
    db.close();
}

//=============================================================================
//ON INITIALIZATION
//=============================================================================

storedvars = require('table/storedvars');
prevversion = storedvars.databaseVersion.getValue();
if (prevversion !== null &&
        prevversion < VERSION.CAMCOPS_VERSION &&
        platform.isDatabaseSupported) {

    // Database is old. We may need to upgrade it.
    Titanium.API.info("Old database version! Is " + prevversion +
                      ", should be " + VERSION.CAMCOPS_VERSION);

    // Apply the change in version number sequence.

    if (prevversion < 1.08) {
        // Changes made at v1.08:
        Titanium.API.info(UPGRADING_TO + 1.08);
        dbsqlite.renameColumns("icd10schizophrenia", [
            {from: "tpah_commentary", to: "hv_commentary"},
            {from: "tpah_discussing", to: "hv_discussing"},
            {from: "tpah_from_body", to: "hv_from_body"},
        ]);
    }

    if (prevversion < 1.12) {
        Titanium.API.info(UPGRADING_TO + 1.12);
        // expdetthreshold
        dbsqlite.renameTable("expdetthreshold",
                             "cardinal_expdetthreshold");
        dbsqlite.renameTable("expdetthreshold_trials",
                             "cardinal_expdetthreshold_trials");
        dbsqlite.renameColumns("cardinal_expdetthreshold_trials", [
            {from: "expdetthreshold_id", to: "cardinal_expdetthreshold_id"},
        ]);

        // expdet
        dbsqlite.renameTable("expectationdetection",
                             "cardinal_expdet");
        dbsqlite.renameTable("expectationdetection_trialgroupspec",
                             "cardinal_expdet_trialgroupspec");
        dbsqlite.renameTable("expectationdetection_trials",
                             "cardinal_expdet_trials");
        dbsqlite.renameColumns("cardinal_expdet_trials", [
            {from: "expectationdetection_id", to: "cardinal_expdet_id"},
        ]);
        dbsqlite.renameColumns("cardinal_expdet_trialgroupspec", [
            {from: "expectationdetection_id", to: "cardinal_expdet_id"},
        ]);
    }

    if (prevversion < 1.15) {
        Titanium.API.info(UPGRADING_TO + 1.15);
        colchanges = [];
        for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; i += 1) {
            colchanges.push({column: "idnum" + i, newtype: "REAL"});
        }
        dbsqlite.changeColumnTypes(DBCONSTANTS.PATIENT_TABLE, colchanges);
    }

    // ... etc.

    Titanium.API.info("Done with any database upgrade steps.");
}
// All done; store the new version.
storedvars.databaseVersion.setValue(VERSION.CAMCOPS_VERSION);
Titanium.API.info("Database version stored.");
