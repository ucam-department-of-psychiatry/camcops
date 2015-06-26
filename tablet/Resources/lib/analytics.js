// analytics.js

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

/*
    NOTE: this function sends information back to the CamCOPS "base" in
    Cambridge, when CamCOPS starts. This is the only information sent from the
    app anywhere except to the user-specified server.
    NO PATIENT-IDENTIFIABLE, PER-PATIENT INFORMATION, OR TASK DETAILS ARE SENT.
    This is what is sent:
    - the fact that CamCOPS has started (allowing us to get an idea of how
      often it's being used)
    - the date/time, including timezone (allowing us to get a rough idea of its
      geographical distribution)
    - the device ID, made up of the operating system type (which platforms are
      popular?) and the Titanium platform identifier (a random device-unique ID
      necessary for the task popularity question)
    - the current server address (allowing us to get a rough idea of
      geographical/institutional distribution)
    - the total number of records in each table (allowing us to get an idea of
      which tasks are popular)
    - the CamCOPS/database version numbers (so we know if old versions are
      still in use, or if we can break them in an upgrade)
*/

/*jslint node: true */
"use strict";
/*global Titanium */

function reportAnalytics() {
    var VERSION = require('common/VERSION'),
        DBCONSTANTS = require('common/DBCONSTANTS'),
        moment = require('lib/moment'),
        conversion = require('lib/conversion'),
        platform = require('lib/platform'),
        storedvars = require('table/storedvars'),
        ANALYTICS_URL = "https://egret.psychol.cam.ac.uk/camcops/analytics",
            // Using a numerical IP address would save the DNS lookup step,
            // but the SSL certificate is name-based, so certificate validation
            // fails.
        ANALYTICS_TIMEOUT = 10000, // ms
        tablesWithCounts = {
            table_names: [],
            record_counts: []
        },
        dbsqlite,
        now = moment(),
        dict,
        client;
    if (platform.isDatabaseSupported) {
        dbsqlite = require('lib/dbsqlite');
        tablesWithCounts = dbsqlite.getAllTablesWithRecordCounts();
    }
    // This dictionary is what's sent:
    dict = {
        source: "app",
        now: conversion.momentToString(now),
        device: DBCONSTANTS.DEVICE_ID,
        camcops_version: VERSION.CAMCOPS_VERSION,
        table_names: tablesWithCounts.table_names.join(),
        record_counts: tablesWithCounts.record_counts.join(),
        server: storedvars.serverAddress.getValue(),
        db_version: storedvars.databaseVersion.getValue(),
        use_clinical: storedvars.useClinical.getValue(),
        use_educational: storedvars.useEducational.getValue(),
        use_research: storedvars.useResearch.getValue(),
        use_commercial: storedvars.useCommercial.getValue(),
    };
    // OK, send it
    Titanium.API.info("Sending analytics...");
    client = Titanium.Network.createHTTPClient({
        // no callbacks: if it fails, it fails silently
        timeout: ANALYTICS_TIMEOUT
    });
    client.open("POST", ANALYTICS_URL, true);
    // ... third parameter (async) defaults to true
    client.send(dict);
}
exports.reportAnalytics = reportAnalytics;
