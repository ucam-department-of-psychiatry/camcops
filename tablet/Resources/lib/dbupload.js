// dbupload.js

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

/*jslint node: true, plusplus: true, newcap: true */
"use strict";
/*global Titanium, L */

var ALLTASKS = require('common/ALLTASKS'),
    DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcore = require('lib/dbcore'),
    netcore = require('lib/netcore'),
    idpolicy = require('lib/idpolicy'),
    storedvars = require('table/storedvars'),
    dbsqlite = require('lib/dbsqlite'),
    conversion = require('lib/conversion'),
    moment = require('lib/moment'),
    lang = require('lib/lang'),
    platform = require('lib/platform'),
    SYSTEM_TABLE_NAMES = [DBCONSTANTS.PATIENT_TABLE,
                          DBCONSTANTS.STOREDVARS_TABLE],
    // ... not blob, not storedvarsprivate, not extrastrings
    UPLOAD_COPY = 1,
    UPLOAD_MOVE_KEEPING_PATIENTS = 2,
    UPLOAD_MOVE = 3,
    WRITE_NEW_DESCRIPTIONS_TO_EXISTING_PATIENTS = true;

exports.UPLOAD_COPY = UPLOAD_COPY;
exports.UPLOAD_MOVE_KEEPING_PATIENTS = UPLOAD_MOVE_KEEPING_PATIENTS;
exports.UPLOAD_MOVE = UPLOAD_MOVE;

function sendEmptyTables(tablenames, callbackSuccess, callbackFailure) {
    Titanium.API.info("sendEmptyTables: " + tablenames);
    if (tablenames.length === 0) {
        callbackSuccess();
        return;
    }
    var dict = {
        operation: "upload_empty_tables",
        tables: tablenames.join(",")
    };
    netcore.sendToServer(dict, callbackSuccess, callbackFailure);
}

function sendTableWhole(tablename, callbackSuccess, callbackFailure) {
    Titanium.API.info("sendTableWhole: " + tablename);
    var fieldnames = dbsqlite.getFieldNames(tablename),
        dict = {
            operation: "upload_table",
            table: tablename,
            fields: fieldnames.join(",")
        };
    dbsqlite.getRecords_lowmem(tablename, dict, "record", "nrecords");
    // We send even empty tables, since this might reflect recent deletion...
    netcore.sendToServer(dict, callbackSuccess, callbackFailure);
}

function sendTableRecordwise(tablename, callbackSuccess, callbackFailure) {
    var fieldnames = dbsqlite.getFieldNames(tablename),
        pkname = "id",
        pks = dbsqlite.getPKs(tablename, pkname),
        currentRecord = -1;

    function sendNextRecord() {
        ++currentRecord;
        if (currentRecord >= pks.length) {
            callbackSuccess(); // End
            return;
        }
        var dict = {
            operation: "upload_record",
            table: tablename,
            fields: fieldnames.join(","),
            pkname: pkname
        };
        dbsqlite.getRecordByPK_lowmem(tablename, fieldnames, pkname,
                                      pks[currentRecord], dict, "values");
        netcore.sendToServer(dict, sendNextRecord, callbackFailure); // Loop
    }

    Titanium.API.info("sendTableRecordwise: " + tablename);
    netcore.sendToServer({
        operation: "delete_where_key_not",
        table: tablename,
        pkname: pkname,
        pkvalues: pks.join(",")
    }, sendNextRecord, callbackFailure); // Start
}

function sendBlobTable(callbackSuccess, callbackFailure) {
    var tablename = DBCONSTANTS.BLOB_TABLE,
        fieldnames = dbsqlite.getFieldNames(tablename),
        pkname = DBCONSTANTS.BLOB_PKNAME,
        Blob = require('table/Blob'),
        currentRecord = -1,
        pks_to_send = [],
        allPKsAndDates = dbsqlite.getPKsAndDates(
            tablename,
            pkname,
            DBCONSTANTS.MODIFICATION_TIMESTAMP_FIELDNAME
        ),
        whichkeysdict = {
            operation: "which_keys_to_send",
            table: tablename,
            pkname: pkname,
            pkvalues: allPKsAndDates.pks.join(","), // all PKs
            datevalues: allPKsAndDates.dates.join(",")
        };

    function sendNextRecord() {
        ++currentRecord;
        if (currentRecord >= pks_to_send.length) {
            callbackSuccess(); // End
            return;
        }
        var b = new Blob(pks_to_send[currentRecord]),
            dict = {
                operation: "upload_record",
                table: tablename,
                fields: fieldnames.join(","),
                pkname: pkname
            };
        dbsqlite.getRecordByPK_lowmem(tablename, fieldnames, pkname,
                                      pks_to_send[currentRecord], dict,
                                      "values");
        dict.fields += ",theblob";
        dict.values += "," + b.getEncodedBlob();
        b = null; // free memory as soon as possible
        netcore.sendToServer(dict, sendNextRecord, callbackFailure); // Loop
    }

    function startSending(reply) {
        if (!reply.result) {
            callbackSuccess();
            return;
        }
        pks_to_send = reply.result.split(",");
        sendNextRecord();
    }

    Titanium.API.info("sendBlobTable");
    if (!dbsqlite.tableExists(tablename)) {
        callbackSuccess();
        return;
    }
    netcore.sendToServer(whichkeysdict, startSending, callbackFailure);
    // ... Start
}

function getTableNamesToUpload() {
    // We upload the intersection of the permissible (what we know about,
    // excepting blobs/other private tables) and the possible (what's in the
    // database). Uploading all the possible tables causes problems during
    // development with "orphan" tables.
    var possibletablenames = dbsqlite.getMainTableNames().sort(),
        permissibletablenames = SYSTEM_TABLE_NAMES,
        t,
        tablenames;
    for (t in ALLTASKS.TASKLIST) {
        if (ALLTASKS.TASKLIST.hasOwnProperty(t)) {
            if (ALLTASKS.TASKLIST[t].tables) {
                permissibletablenames = permissibletablenames.concat(
                    ALLTASKS.TASKLIST[t].tables
                );
            }
        }
    }
    permissibletablenames.sort();
    tablenames = lang.intersect_destructive(possibletablenames,
                                            permissibletablenames);

    if (permissibletablenames.length > 0) {
        Titanium.API.info(
            "getTableNamesToUpload: SKIPPING (not in database): " +
                JSON.stringify(permissibletablenames)
        );
    }
    if (possibletablenames.length > 0) {
        Titanium.API.info(
            "getTableNamesToUpload: SKIPPING (not in permitted list): " +
                JSON.stringify(possibletablenames)
        );
    }
    return tablenames;
}

/*jslint regexp: true */
function getServerIdentificationInfo(reply) {
    var idinfo = {
            databaseTitle: reply.databaseTitle || "",
            idPolicyUpload: reply.idPolicyUpload || "",
            idPolicyFinalize: reply.idPolicyFinalize || "",
            serverCamcopsVersion: reply.serverCamcopsVersion || ""
        },
        idDescriptions = [],
        idShortDescriptions = [],
        i;
    for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
        // OK to assign to array (ignoring index 0) like this
        idDescriptions[i] = reply["idDescription" + i] || "";
        idShortDescriptions[i] = reply["idShortDescription" + i] || "";
    }
    idinfo.idDescriptions = idDescriptions;
    idinfo.idShortDescriptions = idShortDescriptions;
    return idinfo;
}
/*jslint regexp: false */

function storeBasicServerInfo(idinfo) {
    Titanium.API.trace("storeBasicServerInfo");
    storedvars.databaseTitle.setValue(idinfo.databaseTitle);
    storedvars.serverCamcopsVersion.setValue(idinfo.serverCamcopsVersion);
}

function serverVersionOk() {
    var sv = storedvars.serverCamcopsVersion.getValue(),
        VERSION = require('common/VERSION');
    return sv >= VERSION.MINIMUM_SERVER_VERSION;
}

function storePolicies(idinfo) {
    Titanium.API.trace("storePolicies");
    storedvars.idPolicyUpload.setValue(idinfo.idPolicyUpload);
    idpolicy.tokenizeUploadIdPolicy(idinfo.idPolicyUpload);
    storedvars.idPolicyFinalize.setValue(idinfo.idPolicyFinalize);
    idpolicy.tokenizeFinalizeIdPolicy(idinfo.idPolicyFinalize);
}

function storeIdDescriptions(idinfo) {
    Titanium.API.trace("storeIdDescriptions");
    var i,
        dbcommon = require('lib/dbcommon');
    for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
        storedvars["idDescription" + i].setValue(idinfo.idDescriptions[i]);
        storedvars["idShortDescription" + i].setValue(
            idinfo.idShortDescriptions[i]
        );
    }
    if (WRITE_NEW_DESCRIPTIONS_TO_EXISTING_PATIENTS) {
        dbcommon.copyDescriptorsToPatients();
    }
}

function serverDescriptionsMatchTablet(idinfo) {
    var i;
    for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; ++i) {
        if (idinfo.idDescriptions[i] !==
                storedvars["idDescription" + i].getValue()) {
            return false;
        }
        if (idinfo.idShortDescriptions[i] !==
                storedvars["idShortDescription" + i].getValue()) {
            return false;
        }
    }
    return true;
}

function getServerContactNowString() {
    return (storedvars.getServerURL() + " " + L("at") + " " +
            conversion.momentToString(moment()));
}

function markLastSuccessfulUploadAsNow() {
    Titanium.API.trace("markLastSuccessfulUploadAsNow");
    storedvars.lastSuccessfulUpload.setValue(getServerContactNowString());
}

function upload(sourcewindow, method, callbackFn) {
    if (!platform.isDatabaseSupported) {
        throw new Error("Requires SQLite-based platform");
    }

    if (method === undefined) {
        method = UPLOAD_MOVE;
    }
    var uifunc = require('lib/uifunc'),
        cancelled = false,
        wait,
        tablenames = getTableNamesToUpload(),
        currentTable = -1,
        currentTableName = "",
        successTables = [],
        failureTables = tablenames.slice(0), // clone
        serverErrors = [],
        ourErrors = [],
        patientIdsToMoveOffTablet = [],
        emptyTablesToSend = [],
        uploadNextTable; // FUNCTION; defined here to break circular dependency

    // For JSLint, functions defined in reverse order of use:

    function applyPatientMoveOffTabletFlagsToTasks(patient_ids, moveoff) {
        if (method !== UPLOAD_COPY) {
            return;
            // because otherwise, all tasks are going to be moved anyway
        }
        var ALLTASKS = require('common/ALLTASKS'),
            t,
            tasktitle,
            tasktype,
            taskclass,
            i,
            pid,
            taskdata,
            j;
        for (t in ALLTASKS.TASKLIST) {
            if (ALLTASKS.TASKLIST.hasOwnProperty(t)) {
                tasktitle = ALLTASKS.TASKLIST[t].title;
                wait.setMessage(L('scanning_tasks') + "\n\n" + tasktitle);
                tasktype = ALLTASKS.TASKLIST[t].task;
                taskclass = require(tasktype);
                for (i = 0; i < patient_ids.length; ++i) {
                    pid = patient_ids[i];
                    taskdata = new taskclass().getAllRowsByPatient(pid);
                    for (j = 0; j < taskdata.length; ++j) {
                        taskdata[j].setMoveOffTablet(moveoff);
                    }
                }
            }
        }
    }

    function everythingFinished(success, failedEarly) {
        var s,
            t,
            resetPatientSelection = false,
            GV;
        success = success === undefined ? false : success;
        failedEarly = failedEarly === undefined ? false : failedEarly;
        Titanium.API.info("dbupload.upload.everythingFinished");
        wait.setMessage(L('upload_finished'));
        // Finished
        netcore.clearTempServerPassword();
        if (success && failureTables.length === 0) {
            // Success
            markLastSuccessfulUploadAsNow();
            t = L('upload_successful');
            s = L('upload_was_to') + " " + storedvars.getServerURL();
            GV = require('common/GV');
            if (method === UPLOAD_COPY) {
                dbsqlite.clearMoveOffTabletRecords(tablenames);
                resetPatientSelection = (patientIdsToMoveOffTablet.indexOf(
                    GV.selected_patient_id
                ) > -1);
            } else if (method === UPLOAD_MOVE) {
                dbsqlite.wipeDatabaseNotStoredVars();
                resetPatientSelection = true;
            } else if (method === UPLOAD_MOVE_KEEPING_PATIENTS) {
                dbsqlite.wipeDatabaseNotStoredVarsOrPatients();
                dbsqlite.clearMoveOffTabletRecords(tablenames);
                // ... might clear out some patients
                resetPatientSelection = (patientIdsToMoveOffTablet.indexOf(
                    GV.selected_patient_id
                ) > -1);
            }
            if (resetPatientSelection) {
                uifunc.broadcastPatientSelection(null);
            }
        } else {
            // Failure
            applyPatientMoveOffTabletFlagsToTasks(patientIdsToMoveOffTablet,
                                                  false);
            // ... unset them again (in case the user changes their mind about
            // a patient)
            if (cancelled) {
                t = L('upload_cancelled');
                s = "";
            } else {
                t = L('upload_failed');
                s = (
                    L('upload_was_to') + " " + storedvars.getServerURL() +
                    "\n\n" + L('errors') + " " + ourErrors.join() +
                    "\n" +
                    serverErrors.join()
                );
                if (!failedEarly) {
                    s += (
                        "\n\n" +
                        L('failure_tables') + " " + failureTables.join(", ") +
                        "\n\n" +
                        L('would_have_been_success_tables') + " " +
                        successTables.join(", ")
                    );
                }
            }
        }
        wait.hide();
        uifunc.alert(s, t);
        // Callback
        if (typeof callbackFn === "function") {
            callbackFn(); // ------ CHAIN
        }
    }

    function tableSuccess() {
        successTables.push(currentTableName);
        lang.removeFromArrayByValue(failureTables, currentTableName);
        uploadNextTable(); // ------ CHAIN
    }

    function tableFailure(error) {
        serverErrors.push(error);
        ourErrors.push(L('failed_to_upload_table') + " " + currentTableName);
        everythingFinished();
    }

    function completeFailure(ourError, serverError, failedEarly) {
        ourErrors.push(ourError);
        if (serverError !== undefined) {
            serverErrors.push(serverError);
        }
        if (failedEarly === undefined) {
            failedEarly = true;
        }
        everythingFinished(false, failedEarly);
    }

    function endUpload() {
        Titanium.API.trace("dbupload.upload.endUpload");
        wait.setMessage(L('ending_upload'));
        var dict = {
            operation: "end_upload"
        };
        netcore.sendToServer(
            dict,
            function () {
                everythingFinished(true); // ------ CHAIN
            },
            function (error) {
                completeFailure(L('failed_end_upload'), error, false);
            }
        );
    }

    function emptiesFinished() {
        successTables.push.apply(successTables, emptyTablesToSend);
        lang.removeSecondArrayContentsFromFirstArray(failureTables,
                                                     emptyTablesToSend);
        emptyTablesToSend = [];
        endUpload(); // ------ CHAIN
    }

    function emptiesFailed(error) {
        serverErrors.push(error);
        ourErrors.push(L('failed_to_upload_table') + " " +
                       emptyTablesToSend.join(", "));
        everythingFinished();
    }

    uploadNextTable = function () {
        ++currentTable;
        if (cancelled) {
            // Do nothing
            return;
        }
        if (currentTable >= tablenames.length) {
            // All tables finished
            wait.setMessage(L('sending_empty_tables'));
            sendEmptyTables(emptyTablesToSend, emptiesFinished, emptiesFailed);
            return;
            // ------ CHAIN
        }
        // Check a table
        currentTableName = tablenames[currentTable];
        if (dbsqlite.getNumRecords(currentTableName) === 0) {
            // Table is empty; add to the empty list
            emptyTablesToSend.push(currentTableName);
            uploadNextTable(); // ------ CHAIN; recursion (but there's
            // hidden recursion anyway; all these functions call each other)
            return;
        }
        // Send table
        wait.setMessage(L('uploading_table') + ' ' + currentTableName);
        if (currentTableName === DBCONSTANTS.BLOB_TABLE) {
            sendBlobTable(tableSuccess, tableFailure); // ------ CHAIN
        } else {
            sendTableWhole(currentTableName, tableSuccess, tableFailure);
            // ------ CHAIN
            // sendTableRecordwise(currentTableName, uploadNextTable,
            //                     callbackFailure);
        }
    };

    function startTables() {
        Titanium.API.trace("dbupload.upload.startTables");
        if (method !== UPLOAD_COPY) {
            wait.setMessage(L('starting_preservation'));
            var dict = {
                operation: "start_preservation"
            };
            netcore.sendToServer(
                dict,
                uploadNextTable, // ------ CHAIN
                function (error) {
                    completeFailure(L('preservation_start_failed'), error);
                }
            );
        } else {
            uploadNextTable(); // ------ CHAIN
        }
    }

    function startUpload() {
        Titanium.API.trace("dbupload.upload.startUpload");
        wait.setMessage(L('starting_upload'));
        var dict = {
            operation: "start_upload"
        };
        netcore.sendToServer(
            dict,
            startTables, // ------ CHAIN
            function (error) {
                completeFailure(L('failed_start_upload'), error);
            }
        );
    }

    function checkPatientInfoComplete() {
        Titanium.API.trace("dbupload.upload.checkPatientInfoComplete");
        var Patient = require('table/Patient'),
            nfailures_upload = 0,
            nfailures_finalize = 0,
            patientdata = (new Patient()).getAllRows(),
            i;
        // ... creates a dummy Patient object to use its getAllRows() method
        for (i = 0; i < patientdata.length; ++i) {
            if (!patientdata[i].satisfiesUploadIdPolicy()) {
                nfailures_upload++;
            }
            if (!patientdata[i].satisfiesFinalizeIdPolicy()) {
                nfailures_finalize++;
            }
            if (patientdata[i].getMoveOffTablet()) {
                patientIdsToMoveOffTablet.push(patientdata[i].id);
            }
        }
        if (method === UPLOAD_COPY && nfailures_upload > 0) {
            // Copying; we're allowed not to meet the finalizing requirements,
            // but we must meet the uploading requirements
            completeFailure(nfailures_upload + " " +
                            L("patients_do_not_meet_upload_id_policy") + " " +
                            storedvars.idPolicyUpload.getValue());
        } else if (method !== UPLOAD_COPY &&
                    (nfailures_upload + nfailures_finalize > 0)) {
            // Finalizing; must meet all requirements
            completeFailure(
                nfailures_upload + " " +
                    L("patients_do_not_meet_upload_id_policy") + " " +
                    storedvars.idPolicyUpload.getValue() +
                    "\n" +
                    nfailures_finalize + " " +
                    L("patients_do_not_meet_finalize_id_policy") + " " +
                    storedvars.idPolicyFinalize.getValue()
            );
        } else {
            applyPatientMoveOffTabletFlagsToTasks(patientIdsToMoveOffTablet,
                                                  true);
            startUpload(); // ------ CHAIN
        }
    }

    function checkDescriptionsPoliciesVersion(reply) {
        Titanium.API.trace("dbupload.upload.checkDescriptionsPoliciesVersion");
        var idinfo = getServerIdentificationInfo(reply),
            sv,
            VERSION;
        storeBasicServerInfo(idinfo);
        storePolicies(idinfo);
        if (!serverVersionOk()) {
            sv = storedvars.serverCamcopsVersion.getValue();
            VERSION = require('common/VERSION');
            completeFailure(
                "Server CamCOPS version too old: is " + sv +
                    ", need " + VERSION.MINIMUM_SERVER_VERSION
            );
            return;
        }
        if (serverDescriptionsMatchTablet(idinfo)) {
            checkPatientInfoComplete(); // ------ CHAIN
        } else {
            completeFailure(L("server_id_description_mismatch"));
        }
    }

    function fetchDescriptionsAndPolicies() {
        Titanium.API.trace("dbupload.upload.fetchDescriptionsAndPolicies");
        wait.setMessage(L('checking_id_info'));
        var dict = {
            operation: "get_id_info"
        };
        netcore.sendToServer(
            dict,
            checkDescriptionsPoliciesVersion, // ------ CHAIN
            function (error) {
                completeFailure(L('failed_to_fetch_id_info'), error);
            }
        );
    }

    function checkUser() {
        Titanium.API.trace("dbupload.upload.checkUser");
        wait.setMessage(L('checking_user'));
        var dict = {
            operation: "check_upload_user_and_device"
        };
        netcore.sendToServer(
            dict,
            fetchDescriptionsAndPolicies, // ------ CHAIN
            function (error) {
                completeFailure(L('user_not_valid_for_upload'), error);
            }
        );
    }

    function checkDeviceRegistered() {
        Titanium.API.trace("dbupload.upload.checkDeviceRegistered");
        wait.setMessage(L('checking_device_registration'));
        var dict = {
            operation: "check_device_registered"
        };
        netcore.sendToServer(
            dict,
            checkUser, // ------ CHAIN
            function (error) {
                completeFailure(L('registration_check_failed'), error);
            },
            false // special flag: don't supply username
        );
    }

    function checkServerInfoPresent() {
        Titanium.API.trace("dbupload.upload.checkServerInfoPresent");
        if (storedvars.serverInfoPresent()) {
            checkDeviceRegistered(); // ------ CHAIN
        } else {
            completeFailure(L("no_server_info"));
        }
    }

    wait = uifunc.createWait({  // dialogue while we wait
        window: sourcewindow,
        message: L('uploading'),
        title: L('uploading_to') + " " + storedvars.getServerURL(),
        offerCancel: true,
        fnCancel: function () {
            cancelled = true;
            wait.hide();
            // Not a great deal more we can do! The dialogue will have been
            // dismissed.
            everythingFinished();
        }
    });
    wait.show();
    tablenames.push(DBCONSTANTS.BLOB_TABLE);
    Titanium.API.info("TABLENAMES = " + JSON.stringify(tablenames));

    // We split the device check, user check, and table uploads,
    // because whilst Titanium/Android returns a useful server HTTP error
    // message, Titanium/iOS doesn't, so we only know the error
    // by the context.

    // Kickoff
    checkServerInfoPresent();
}
exports.upload = upload;

function markLastRegistrationAsNow() {
    storedvars.lastServerRegistration.setValue(getServerContactNowString());
}

function getRegistrationDictionary() {
    return {
        operation: "register",
        devicefriendlyname: storedvars.deviceFriendlyName.getValue()
    };
}

function getExtraStringRequestDictionary() {
    return {
        operation: "get_extra_strings"
    };
}

function writeExtraStringsFromReply(reply) {
    var extrastrings = require('table/extrastrings'),
        recordlist = netcore.convertResponseToRecordList(reply),
        i;
    // Reply has tuples of task, name, value
    extrastrings.delete_all_strings();
    for (i = 0; i < recordlist.length; ++i) {
        extrastrings.add(recordlist[i][0], recordlist[i][1],
                         recordlist[i][2]);
    }
}

function completeRegistration(idinfo) {
    var uifunc = require('lib/uifunc');
    storeBasicServerInfo(idinfo);
    storePolicies(idinfo);
    markLastRegistrationAsNow();
    // Always sync descriptions; too much chance for cock-up otherwise.
    // MORE DEBATABLE: always write new descriptions to existing patients
    storeIdDescriptions(idinfo);
    uifunc.broadcastPatientSelection(null);
    // ... deselect patient, or its description text may be out of date
}

function register(sourcewindow) {
    var uifunc = require('lib/uifunc'),
        wait = null,
        dict = getRegistrationDictionary();

    if (!storedvars.serverInfoPresent()) {
        uifunc.alert(L("no_server_info"), L("cannot_upload"));
        return;
    }

    function registrationFinished() {
        netcore.clearTempServerPassword();
        if (wait) {
            wait.hide();
        }
    }

    function success_2(reply) {
        Titanium.API.trace("dbupload.register(): get_extra_strings reply = " +
                           JSON.stringify(reply));
        var title = L('registration_successful'),
            message = (
                L('registration_successful') + "\n\n" +
                L('registration_was_with') + " " + storedvars.getServerURL()
            );
        registrationFinished();
        writeExtraStringsFromReply(reply);
        uifunc.alert(message, title);
    }

    function failure_2(error) {
        Titanium.API.warn("dbupload.register(): get_extra_strings failure: "
                          + "error = " + JSON.stringify(error));
        registrationFinished();
        uifunc.alert(
            L('registration_was_with') + " " + storedvars.getServerURL() +
                "\n\n" + L('errors') + " " + error,
            L('registration_succeeded_strings_failed')
        );
    }

    function success_1(reply) {
        Titanium.API.trace("dbupload.register(): reply = " +
                           JSON.stringify(reply));
        var idinfo = getServerIdentificationInfo(reply),
            fetchstringsdict = getExtraStringRequestDictionary();

        // Finished; store
        completeRegistration(idinfo);

        // Fetch strings
        wait.setMessage(L('downloading_extra_strings'));
        netcore.sendToServer(fetchstringsdict, success_2, failure_2);
    }

    function failure_1(error) {
        Titanium.API.warn("dbupload.register(): failure: error = " +
                          JSON.stringify(error));
        registrationFinished();
        uifunc.alert(
            L('registration_was_with') + " " + storedvars.getServerURL() +
                "\n\n" + L('errors') + " " + error,
            L('registration_failed')
        );
    }

    // Dialogue while we wait
    wait = uifunc.createWait({
        window: sourcewindow,
        message: L('registering'),
        title: L('registering_with') + " " + storedvars.getServerURL(),
        offerCancel: true,
        fnCancel: function () {
            wait.hide();
            // Not a great deal more we can do! The dialogue will have been
            // dismissed.
        }
    });
    wait.show();
    // Kickoff
    netcore.sendToServer(dict, success_1, failure_1);
}
exports.register = register;

function registerBlockingForMobileweb() {
    var netcore = require('lib/netcore'),
        dict = getRegistrationDictionary(),
        reply = netcore.getServerResponse(dict),
        idinfo;
    if (!reply.success) {
        Titanium.API.warn("dbupload.registerBlockingForMobileweb(): failure," +
                          "reply = " + JSON.stringify(reply));
        return false;
    }
    idinfo = getServerIdentificationInfo(reply);
    completeRegistration(idinfo);
    return true;
}
exports.registerBlockingForMobileweb = registerBlockingForMobileweb;

function fetch_id_descriptions(sourcewindow) {
    var uifunc = require('lib/uifunc'),
        wait = null,
        dict = {
            operation: "get_id_info"
        };

    function finished() {
        netcore.clearTempServerPassword();
        if (wait) {
            wait.hide();
        }
    }

    function success(reply) {
        var idinfo = getServerIdentificationInfo(reply),
            message = (
                L('get_id_info_success_from') + " " + storedvars.getServerURL()
            ),
            title = L('get_id_info_success');

        // Finished; store
        storeBasicServerInfo(idinfo);
        storePolicies(idinfo);
        finished();
        markLastRegistrationAsNow();
        // Always sync descriptions; too much chance for cock-up otherwise.
        // MORE DEBATABLE: always write new descriptions to existing patients
        storeIdDescriptions(idinfo);

        // Good.
        uifunc.broadcastPatientSelection(null);
        // ... deselect patient, or its description text may be out of date
        uifunc.alert(message, title);
    }

    function failure(error) {
        finished();
        uifunc.alert(
            L('get_id_info_was_from') + " " + storedvars.getServerURL() +
                "\n\n" +
                L('errors') + " " + error,
            L('get_id_info_failed')
        );
    }

    if (!storedvars.serverInfoPresent()) {
        uifunc.alert(L("no_server_info"), L("cannot_upload"));
        return;
    }
    // Dialogue while we wait
    wait = uifunc.createWait({
        window: sourcewindow,
        message: L('getting_id_info'),
        title: L('getting_id_info_from') + " " + storedvars.getServerURL(),
        offerCancel: true,
        fnCancel: function () {
            wait.hide();
            // Not a great deal more we can do! The dialogue will have been
            // dismissed.
        }
    });
    wait.show();
    // Kickoff
    netcore.sendToServer(dict, success, failure);
}
exports.fetch_id_descriptions = fetch_id_descriptions;

function fetch_extrastrings(sourcewindow) {
    var uifunc = require('lib/uifunc'),
        wait = null,
        dict = getExtraStringRequestDictionary();

    function finished() {
        netcore.clearTempServerPassword();
        if (wait) {
            wait.hide();
        }
    }

    function success(reply) {
        var message = (
                L('get_extrastrings_from') + " " + storedvars.getServerURL()
            ),
            title = L('get_extrastrings_success');

        writeExtraStringsFromReply(reply);
        finished();
        uifunc.alert(message, title);
    }

    function failure(error) {
        finished();
        uifunc.alert(
            L('get_extrastrings_was_from') + " " + storedvars.getServerURL() +
                "\n\n" +
                L('errors') + " " + error,
            L('get_extrastrings_failed')
        );
    }

    if (!storedvars.serverInfoPresent()) {
        uifunc.alert(L("no_server_info"), L("cannot_upload"));
        return;
    }
    // Dialogue while we wait
    wait = uifunc.createWait({
        window: sourcewindow,
        message: L('getting_extrastrings'),
        title: L('getting_extrastrings_from') + " " +
            storedvars.getServerURL(),
        offerCancel: true,
        fnCancel: function () {
            wait.hide();
            // Not a great deal more we can do! The dialogue will have been
            // dismissed.
        }
    });
    wait.show();
    // Kickoff
    netcore.sendToServer(dict, success, failure);
}
exports.fetch_extrastrings = fetch_extrastrings;
