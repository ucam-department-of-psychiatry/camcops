// dbcommon.js

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

/*jslint node: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium */

var DBCONSTANTS = require('common/DBCONSTANTS');
var platform = require('lib/platform');
var dbcore = require('lib/dbcore');
var lang = require('lib/lang');
// var debugfunc = require('lib/debugfunc');

var MODIFICATION_TIMESTAMP_FIELDSPEC = {
    name: DBCONSTANTS.MODIFICATION_TIMESTAMP_FIELDNAME,
    type: DBCONSTANTS.TYPE_DATETIME
};

if (platform.isDatabaseSupported) {
    Titanium.API.info("dbcommon: using SQLite database");
    // Scope rules: http://stackoverflow.com/questions/500431/
    var dbsystem = require('lib/dbsqlite');
} else {
    if (platform.useMockTables) {
        Titanium.API.info("dbcommon: using mock tables");
        var dbsystem = require('lib/dbmocktables');
    } else {
        Titanium.API.info("dbcommon: using webclient database");
        var dbsystem = require('lib/dbwebclient');
    }
}
Titanium.API.info("dbcommon: database subsystem loaded");

// These functions use:
//      tablename - string
//      fieldlist - array of objects with attributes:
//                      name (fieldname)
//                      type (SQL type)
//                      +/- unique (boolean)
//                      +/- mandatory (boolean)
//                      +/- defaultValue (default value)
//                - the first item must be the primary key (PK)
//      object - the row representation object

//=============================================================================
// CORE FUNCTIONS
//=============================================================================

var createTable = dbsystem.createTable; // tablename, fieldlist (ALL fields)
exports.createTable = createTable;
    // If a table doesn't exist: create it.
    // If a table exists:
    // - add any fields that don't exist,
    // - modify any that are wrong,
    // - and drop any that shouldn't be there.

var dropTable = dbsystem.dropTable; // tablename
exports.dropTable = dropTable;

var isInDatabaseByPK = dbsystem.isInDatabaseByPK; // tablename, pkname, pkval
exports.isInDatabaseByPK = isInDatabaseByPK;
    // Is a row in a table, as identified by a primary key?

/*
var insertOrReplaceRow = dbsystem.insertOrReplaceRow;
exports.insertOrReplaceRow = insertOrReplaceRow;
    // INSERT OR REPLACE INTO
*/

var createRow = dbsystem.createRow; // tablename, fieldlist (fields to write), object, pkname
exports.createRow = createRow;

var readFromUniqueField = dbsystem.readFromUniqueField; // tablename, fieldlist (fields to read), object, keyname, keyval
exports.readFromUniqueField = readFromUniqueField;
    // Reads row identified by PK into object

var readFromUniqueFieldCombination = dbsystem.readFromUniqueFieldCombination; // tablename, fieldlist (all fields = fields to read), object, fvpairs
exports.readFromUniqueFieldCombination = readFromUniqueFieldCombination;

var countWhere = dbsystem.countWhere; // tablename, wherefields, wherevalues, wherenotfields, wherenotvalues
exports.countWhere = countWhere;

var updateByPK = dbsystem.updateByPK; // tablename, fieldlist (fields to write), object, pkname, pkval
exports.updateByPK = updateByPK;

var deleteWhere = dbsystem.deleteWhere; // tablename, field, value
exports.deleteWhere = deleteWhere;

var getAllRows = dbsystem.getAllRows; // tablename, fieldlist, objecttype, orderby
exports.getAllRows = getAllRows;

var getAllPKs = dbsystem.getAllPKs; // tablename, pkname, orderby
exports.getAllPKs = getAllPKs;

var getAllPKsByKey = dbsystem.getAllPKsByKey; // tablename, pkname, orderby, keyname, value
exports.getAllPKsByKey = getAllPKsByKey;

var getAllRowsByKey = dbsystem.getAllRowsByKey; // keyname, keyvalue, tablename, fieldlist, objecttype, orderby
exports.getAllRowsByKey = getAllRowsByKey;

var getSingleValueByKey = dbsystem.getSingleValueByKey; // tablename, keyname, keyvalue, field
exports.getSingleValueByKey = getSingleValueByKey;

var setSingleValueByKey = dbsystem.setSingleValueByKey; // tablename, keyname, keyvalue, field, value
exports.setSingleValueByKey = setSingleValueByKey;

var copyDescriptorsToPatients = dbsystem.copyDescriptorsToPatients; // [no params]
exports.copyDescriptorsToPatients = copyDescriptorsToPatients;

var createIndex = dbsystem.createIndex; // indexname, tablename, fieldnamelist
exports.createIndex = createIndex;

//=============================================================================
// HIGHER-LEVEL FUNCTIONS
//=============================================================================

function deleteByPK(tablename, pkfield, object) {
    var pkval = object[pkfield.name];
    deleteWhere(tablename, pkfield, pkval);
    object[pkfield.name] = null;
}
exports.deleteByPK = deleteByPK;

function deleteAnyOwnedBlobs(blobfieldnames, object) {
    var Blob = require('table/Blob'),
        i,
        blobfield,
        blob_id,
        b;
    if (blobfieldnames.length === 0) {
        return;
    }
    for (i = 0; i < blobfieldnames.length; ++i) {
        blobfield = blobfieldnames[i];
        blob_id = object[blobfield];
        b = new Blob(blob_id);
        // ... is OK if it's null, and if it's not, this allows cleanup of
        // previous blob
        b.deleteBlob(); // deletes the blob file and itself
        object[blobfield] = null;
        object.dbstore(blobfield);
    }
}

/*jslint continue:true */
function setMoveOffTabletForAnyOwnedBlobs(blobfieldnames, object, moveoff) {
    var Blob = require('table/Blob'),
        i,
        blobfield,
        blob_id,
        b;
    if (blobfieldnames.length === 0) {
        return;
    }
    for (i = 0; i < blobfieldnames.length; ++i) {
        blobfield = blobfieldnames[i];
        blob_id = object[blobfield];
        if (blob_id === undefined || blob_id === null) {
            continue;
        }
        b = new Blob(blob_id);
        b.setMoveOffTablet(moveoff);
    }
}
/*jslint continue:false */

function storeRow(tablename, fieldlist, object, pkname, justThisField) {
    // INSERT or UPDATE as required
    var moment = require('lib/moment'),
        pkval = object[pkname],
        shortfieldlist = [],
        i;
    object[DBCONSTANTS.MODIFICATION_TIMESTAMP_FIELDNAME] = moment();

    // Method 1: assumed to be in database if pk non-null
    if (pkval !== undefined && pkval !== null) {
        if (justThisField !== undefined) {
            for (i = 0; i < fieldlist.length; ++i) {
                if (fieldlist[i].name === justThisField) {
                    shortfieldlist.push(fieldlist[i]);
                }
            }
            if (shortfieldlist.length === 0) {
                throw new Error("updateByPK called with invalid " +
                                "justThisField = " + justThisField);
            }
            shortfieldlist.push(MODIFICATION_TIMESTAMP_FIELDSPEC);
            // ... always update this as well
            return updateByPK(tablename, shortfieldlist, object, pkname,
                              pkval);
        }
        return updateByPK(tablename, fieldlist, object, pkname, pkval);
    }
    return createRow(tablename, fieldlist, object, pkname);

    /*
    // Method 2: database check on PK existence, skipped for speed if the PK is
    // null (always safe)
    if (pkval != null && isInDatabaseByPK(tablename, pkname, pkval)) {
        return updateByPK(tablename, fieldlist, object, justThisField);
    }
    else {
        return createRow(tablename, fieldlist, object);
    }
    */

    /*
    // Method 3: acceptable if few fields, no BLOBs -- i.e. not suitable for
    // general use
    return insertOrReplaceRow(tablename, fieldlist, object);
    */
}
exports.storeRow = storeRow;

//=============================================================================
// VALID FOR SAVING?
//=============================================================================

function getMandatoryFields(fieldlist) {
    var f = "",
        i;
    for (i = 0; i < fieldlist.length; ++i) {
        if (fieldlist[i].mandatory) {
            if (f.length > 0) {
                f += ", ";
            }
            f += fieldlist[i].name;
        }
    }
    return f;
}
exports.getMandatoryFields = getMandatoryFields;

//=============================================================================
// DATABASE ROW-OBJECT CREATION
//=============================================================================

function appendCommonFields(fieldlist) {
    // Additional rows, always:
    fieldlist.push(MODIFICATION_TIMESTAMP_FIELDSPEC);
    fieldlist.push(DBCONSTANTS.MOVE_OFF_TABLET_FIELDSPEC);
}
exports.appendCommonFields = appendCommonFields;

function appendBasicFieldsFromNameArray(fieldlist, fieldnamearray, fieldtype) {
    var i;
    for (i = 0; i < fieldnamearray.length; ++i) {
        fieldlist.push({ name: fieldnamearray[i], type: fieldtype });
    }
}
exports.appendBasicFieldsFromNameArray = appendBasicFieldsFromNameArray;

function DatabaseObject() {
    // (1) Must derive a class to use it.
    // (2) Derived class must specify in its prototype:
    //      _objecttype
    //      _tablename
    //      _fieldlist
    //      _sortorder

    // Create variables; set to their default, or null if no default specified.
    var name,
        defaultValue,
        i;
    for (i = 0; i < this._fieldlist.length; ++i) {
        // Creates variables in object to match fieldlist
        name = this._fieldlist[i].name;
        defaultValue = this._fieldlist[i].defaultValue;
        this[name] = (
            (defaultValue === undefined) ? null : defaultValue
        );
    }
}

DatabaseObject.prototype = {

    getPkField: function () {
        return this._fieldlist[0];
    },

    getPkFieldName: function () {
        return this._fieldlist[0].name;
    },

    getNonPkFields: function () {
        return this._fieldlist.slice(1);
    },

    getPkValue: function () {
        return this[this._fieldlist[0].name];
    },

    getBlobFieldNames: function () {
        var blobfieldnames = [],
            i;
        for (i = 0; i < this._fieldlist.length; ++i) {
            if (this._fieldlist[i].type === DBCONSTANTS.TYPE_BLOBID) {
                blobfieldnames.push(this._fieldlist[i].name);
            }
        }
        return blobfieldnames;
    },

    isBlobFieldName: function (fieldname) {
        var i;
        for (i = 0; i < this._fieldlist.length; ++i) {
            if (this._fieldlist[i].name === fieldname &&
                    this._fieldlist[i].type === DBCONSTANTS.TYPE_BLOBID) {
                return true;
            }
        }
        return false;
    },

    isFieldName: function (fieldname) {
        var i;
        for (i = 0; i < this._fieldlist.length; ++i) {
            if (this._fieldlist[i].name === fieldname) {
                return true;
            }
        }
        return false;
    },

    defaultGetFieldValueFn: function (fieldname, getBlobsAsFilenames) {
        var Blob,
            b,
            blob_id;
        if (this.isBlobFieldName(fieldname)) {
            // BLOB.
            // Field itself contains a foreign key to the blobs.
            blob_id = this[fieldname];
            if (blob_id === undefined || blob_id === null) {
                Titanium.API.trace("... no blob exists, returning null");
                return null;
            }
            Titanium.API.trace("... blob found");
            Blob = require('table/Blob');
            b = new Blob(blob_id);
            if (getBlobsAsFilenames) {
                // Exceptional, e.g. for QuestionCanvas using Ti.Paint, which
                // needs a filename
                return b.getNativePathFilename();
            }
            // Normal behaviour!
            return b.getBlob();
        }
        return this[fieldname];
    },

    defaultSetFieldFn: function (fieldname, value) {
        if (this.isBlobFieldName(fieldname)) {
            // BLOB.
            var Blob = require('table/Blob'),
                existing_blob_id = this[fieldname],
                b = new Blob(existing_blob_id),
                // ... is OK if it's null, and if it's not, this deals with
                // cleanup of previous blob
                pkval = this.getPkValue();
            if (pkval === undefined || pkval === null) {
                this.dbstore(); // must save it, to get an id, to set a blob
            }
            b.setBlob(this._tablename, this.getPkValue(), fieldname, value);
            this[fieldname] = b.id;
        } else {
            this[fieldname] = value;
        }
        this.dbstore(fieldname);
    },

    dbstore: function (justThisField) {
        return storeRow(this._tablename, this.getNonPkFields(), this,
                        this.getPkFieldName(), justThisField);
    },

    touch: function () {
        this.dbstore(DBCONSTANTS.MODIFICATION_TIMESTAMP_FIELDNAME);
    },

    dbread: function (pkval) {
        return readFromUniqueField(this._tablename, this._fieldlist, this,
                                   this.getPkFieldName(), pkval);
    },

    dbreadUniqueField: function (uniquefield, uniqueval) {
        return readFromUniqueField(this._tablename, this._fieldlist, this,
                                   uniquefield, uniqueval);
    },

    dbreadUniqueFieldCombination: function (fvpairs) {
        return readFromUniqueFieldCombination(this._tablename, this._fieldlist,
                                              this, fvpairs);
    },

    dbdelete: function () {
        deleteAnyOwnedBlobs(this.getBlobFieldNames(), this);
        deleteByPK(this._tablename, this.getPkField(), this);
    },

    // The main method via which anonymous tasks are loaded:
    getAllRows: function () {
        return getAllRows(this._tablename, this._fieldlist, this._objecttype,
                          this._sortorder);
    },

    // The main method via which patient-based tasks are loaded:
    getAllRowsByPatient: function (patient_id) {
        return getAllRowsByKey(DBCONSTANTS.PATIENT_FK_FIELDNAME, patient_id,
                               this._tablename, this._fieldlist,
                               this._objecttype, this._sortorder);
    },

    // Valid for saving?
    canSave: function () {
        var fieldlist = this.getNonPkFields(), // PK can be created by database
            i,
            value;
        for (i = 0; i < fieldlist.length; ++i) {
            if (fieldlist[i].mandatory) {
                value = this[fieldlist[i].name];
                if (value === undefined) {
                    return false;
                }
                if (value === null) {
                    return false;
                }
                if (value === "") {
                    return false;
                    // Blank strings aren't NULL, but we disallow them anyway!
                }
            }
        }
        return true;
    },

    getMandatoryFields: function () {
        return getMandatoryFields(this._fieldlist);
    },

    getPK: function () {
        return this[this.getPkFieldName()];
    },

    getMoveOffTablet: function () {
        return this[DBCONSTANTS.MOVE_OFF_TABLET_FIELDNAME];
    },

    toggleMoveOffTablet: function () {
        this.setMoveOffTablet(!this[DBCONSTANTS.MOVE_OFF_TABLET_FIELDNAME]);
    },

    setMoveOffTablet: function (moveoff) {
        this[DBCONSTANTS.MOVE_OFF_TABLET_FIELDNAME] = moveoff;
        this.dbstore();
        setMoveOffTabletForAnyOwnedBlobs(this.getBlobFieldNames(),
                                         this,
                                         moveoff);
    }
};
exports.DatabaseObject = DatabaseObject;

function standardTaskFields(anonymous) {
    var fieldlist,
        additionals = [
            {name: 'when_created', type: DBCONSTANTS.TYPE_DATETIME},
            {name: 'firstexit_is_finish', type: DBCONSTANTS.TYPE_INTEGER},
            {name: 'firstexit_is_abort', type: DBCONSTANTS.TYPE_INTEGER},
            {name: 'when_firstexit', type: DBCONSTANTS.TYPE_DATETIME},
            {name: 'editing_time_s', type: DBCONSTANTS.TYPE_REAL,
                defaultValue: 0}
        ];
    if (anonymous) {
        fieldlist = [
            {name: 'id', type: DBCONSTANTS.TYPE_PK}
        ];
    } else {
        fieldlist = [
            {name: 'id', type: DBCONSTANTS.TYPE_PK},
            {
                name: DBCONSTANTS.PATIENT_FK_FIELDNAME,
                type: DBCONSTANTS.TYPE_INTEGER,
                mandatory: true
            } // FK to patient
        ];
    }
    fieldlist.push.apply(fieldlist, additionals);
    appendCommonFields(fieldlist);
    return fieldlist;
}
exports.standardTaskFields = standardTaskFields;

function standardAncillaryFields(fkField) {
    var fieldlist = [
        {name: 'id', type: DBCONSTANTS.TYPE_PK}
    ];
    fieldlist.push(fkField);
    appendCommonFields(fieldlist);
    return fieldlist;
}
exports.standardAncillaryFields = standardAncillaryFields;

exports.CLINICIAN_FIELDSPECS = [
    {name: "clinician_specialty", type: DBCONSTANTS.TYPE_TEXT},
    {name: "clinician_name", type: DBCONSTANTS.TYPE_TEXT},
    {name: "clinician_professional_registration", type: DBCONSTANTS.TYPE_TEXT},
    {name: "clinician_post", type: DBCONSTANTS.TYPE_TEXT},
    {name: "clinician_service", type: DBCONSTANTS.TYPE_TEXT},
    {name: "clinician_contact_details", type: DBCONSTANTS.TYPE_TEXT}
];
exports.RESPONDENT_FIELDSPECS = [
    {name: "respondent_name", type: DBCONSTANTS.TYPE_TEXT},
    {name: "respondent_relationship", type: DBCONSTANTS.TYPE_TEXT}
];

function appendRepeatedFieldDef(fieldlist, prefix, start, end, type,
                                mandatory) {
    var i;
    for (i = start; i <= end; ++i) {
        fieldlist.push({
            name: prefix + i,
            type: type,
            mandatory: mandatory
        });
    }
}
exports.appendRepeatedFieldDef = appendRepeatedFieldDef;

function copyFields(fieldlist, from, to, startingfield) {
    var i;
    if (startingfield === undefined) {
        startingfield = 0;
    }
    for (i = startingfield; i < fieldlist.length; ++i) {
        to[fieldlist[i].name] = from[fieldlist[i].name];
    }
}
exports.copyFields = copyFields;

function copyFieldsExceptPK(fieldlist, from, to) {
    // alternative: copyFields(fieldlist, from, to, 1)
    var i;
    for (i = 0; i < fieldlist.length; ++i) {
        if (fieldlist[i].type !== DBCONSTANTS.TYPE_PK) {
            to[fieldlist[i].name] = from[fieldlist[i].name];
        }
    }
}
exports.copyFieldsExceptPK = copyFieldsExceptPK;

function copyRecordArray(srcArray, fieldlist) {
    var destArray = [],
        i,
        newElement;
    for (i = 0; i < srcArray.length; ++i) {
        newElement = {};
        copyFields(fieldlist, srcArray[i], newElement);
        destArray.push(newElement);
    }
    return destArray;
}
exports.copyRecordArray = copyRecordArray;

//=============================================================================
// PRETTIFICATION FOR USERS
//=============================================================================

function userString(object, field) {
    var conversion = require('lib/conversion'),
        value = object[field.name];
    if (value === undefined) {
        return "undefined";
    }
    if (value === null) {
        return "null";
    }
    switch (field.type) {
    case DBCONSTANTS.TYPE_BLOBID:
        return "(BLOB)";
    case DBCONSTANTS.TYPE_DATETIME:
        return conversion.momentToString(value);
    case DBCONSTANTS.TYPE_DATE:
        return conversion.momentToDateOnlyString(value);
    default:
        return value;
    }
}
exports.userString = userString;

function userObjectMultilineSummary(object, fieldlist) {
    var pairs = [],
        i;
    for (i = 0; i < fieldlist.length; ++i) {
        pairs.push(fieldlist[i].name + ": " +
                   userString(object, fieldlist[i]));
    }
    return pairs.join("\n") + "\n";
}
exports.userObjectMultilineSummary = userObjectMultilineSummary;

function userCSVHeader(fieldlist) {
    var names = [],
        i;
    for (i = 0; i < fieldlist.length; ++i) {
        names.push(fieldlist[i].name);
    }
    return names.join(",") + "\n";
}
exports.userCSVHeader = userCSVHeader;

function userObjectCSVLine(object, fieldlist) {
    var values = [],
        i;
    for (i = 0; i < fieldlist.length; ++i) {
        values.push(userString(object, fieldlist[i]));
    }
    return values.join(",") + "\n";
}
exports.userObjectCSVLine = userObjectCSVLine;

function userObjectArrayCSVDescription(array, fieldlist) {
    var msg = userCSVHeader(fieldlist),
        i;
    for (i = 0; i < array.length; ++i) {
        msg += userObjectCSVLine(array[i], fieldlist);
    }
    return msg;
}
exports.userObjectArrayCSVDescription = userObjectArrayCSVDescription;

//=============================================================================
// CONVENIENCE CONSTRUCTOR ASSIST FOR ANCILLARY TABLES
//=============================================================================

function loadOrCreateAncillary(object, props, fkName, otherKeyName) {
    var newprops;
    if (props === undefined) {
        return;
    }
    if (props.id !== undefined) {
        // PK specified
        if (props.id === null) {
            throw new Error("Null PK passed to loadOrCreateAncillary()");
        }
        object.dbread(props.id);
    } else if (props[fkName] !== undefined) {
        // FK specified
        if (props[fkName] === null) {
            throw new Error("No PK and null FK passed to " +
                            "loadOrCreateAncillary(): fkName = " + fkName);
        }
        if (props[otherKeyName] !== undefined) {
            // FK and other key (e.g. trial number) specified. Try fetching.
            if (props[otherKeyName] === null) {
                throw new Error("Null 'other' key passed to " +
                                "loadOrCreateAncillary(): " +
                                "otherKeyName = " + otherKeyName);
            }
            newprops = {};
            newprops[fkName] = props[fkName];
            newprops[otherKeyName] = props[otherKeyName];
            object.dbreadUniqueFieldCombination(newprops);
        } else {
            // FK only specified; will need more detail before saving
            object[fkName] = props[fkName];
        }
    } else {
        // Neither PK not FK specified
        throw new Error("Neither PK nor FK passed to loadOrCreateAncillary()");
    }
}
exports.loadOrCreateAncillary = loadOrCreateAncillary;
