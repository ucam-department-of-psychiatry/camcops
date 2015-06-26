// Blob.js

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

/*jslint node: true, nomen: true */
"use strict";
/*global Titanium */

var dbcommon = require('lib/dbcommon'),
    DBCONSTANTS = require('common/DBCONSTANTS'),
    lang = require('lib/lang'),

    // PATIENT TABLE
    tablename = DBCONSTANTS.BLOB_TABLE,
    sortorder = DBCONSTANTS.BLOB_PKNAME,
    fieldlist = [
        // (a) SQL field names; (b) object member variables;
        // (c) PK must be first (assumed by dbcommon.js)
        {name: DBCONSTANTS.BLOB_PKNAME, type: DBCONSTANTS.TYPE_PK},
        {name: 'tablename', type: DBCONSTANTS.TYPE_TEXT, mandatory: true},
        {name: 'tablepk', type: DBCONSTANTS.TYPE_INTEGER, mandatory: true},
        {name: 'fieldname', type: DBCONSTANTS.TYPE_TEXT, mandatory: true},
        {name: 'filename', type: DBCONSTANTS.TYPE_TEXT}
    ];

dbcommon.appendCommonFields(fieldlist);

function getBlobFilename(tablename, tablepk, fieldname) {
    return (DBCONSTANTS.BLOB_FILENAME_PREFIX + tablename + "_" + tablepk +
            "_" + fieldname);
}

function Blob(optional_id) {
    dbcommon.DatabaseObject.call(this); // call base constructor
    if (optional_id !== undefined && optional_id !== null) {
        this.dbread(optional_id);
    }
}

lang.inheritPrototype(Blob, dbcommon.DatabaseObject);
lang.extendPrototype(Blob, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)
    _objecttype: Blob,
    _tablename: tablename,
    _fieldlist: fieldlist,
    _sortorder: sortorder,

    // OTHER

    getBlob: function () {
        if (!this.filename) {
            return null;
        }
        var file = this.getFile(),
            blob;
        if (!file.exists()) {
            Titanium.API.warn("getBlob: file doesn't exist: " + this.filename);
            return null;
        }
        Titanium.API.info("getBlob: file found: " + this.filename);
        blob = file.read();
        Titanium.API.info("getBlob: blob length is " + blob.length);
        return blob;
    },

    getEncodedBlob: function () {
        var conversion = require('lib/conversion'),
            blob = this.getBlob();
        return conversion.blobToMarkedBase64String(blob);
    },

    getFilename: function () {
        return this.filename;
    },

    getFile: function () {
        if (!this.filename) {
            return null;
        }
        return Titanium.Filesystem.getFile(DBCONSTANTS.BLOB_DIRECTORY,
                                           this.filename);
    },

    getNativePathFilename: function () {
        var file = this.getFile();
        if (!file) {
            return null;
        }
        return file.nativePath;
    },

    setBlob: function (tablename, tablepk, fieldname, blob) {
        var file;
        this.deleteBlobFile();
        // ... in case we were already representing a blob file
        this.tablename = tablename;
        this.tablepk = tablepk;
        this.fieldname = fieldname;
        if (blob) {
            this.filename = getBlobFilename(tablename, tablepk, fieldname);
            file = this.getFile();
            Titanium.API.trace("about to write blob; filename = " +
                               this.filename);
            if (file.write(blob)) {
                // Appears to produce an error
                Titanium.API.trace("Wrote blob file. Blob length should be: " +
                                   blob.length);
            } else {
                // Appears to produce an error even when it successfully
                // writes, on iOS
                Titanium.API.warn(
                    "Failed to write blob file! Blob length should be: " +
                        blob.length + ". But if you are on iOS, this error " +
                        "appears even if the write was successful."
                );
            }
        } else {
            // Null blob. Perfectly valid (e.g. deleting a photo).
            this.filename = null;
        }
        this.dbstore();
    },

    deleteBlobFile: function () {
        var file;
        if (this.filename) {
            Titanium.API.info("Deleting blob file: " + this.filename);
            file = this.getFile();
            file.deleteFile();
            this.filename = null;
        }
    },

    deleteBlob: function () {
        this.deleteBlobFile();
        this.dbdelete();
    },

    // Special extra, used by dbsqlite.zapDatabase
    recreateTable: function () {
        dbcommon.createTable(tablename, fieldlist);
    }
});

// CREATE THE TABLE
dbcommon.createTable(tablename, fieldlist);

// RETURN THE OBJECT
module.exports = Blob;
