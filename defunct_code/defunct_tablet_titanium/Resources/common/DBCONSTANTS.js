// DBCONSTANTS.js

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

/*jslint node: true */
/*global Titanium */

module.exports = {
    DEVICE_ID: Titanium.Platform.osname + "_tpi_" + Titanium.Platform.id,
    // Label it so we know what sort of number it is, just in case we have to
    // use others later.

    DBNAME: 'camcops.db', // on iOS, ".sql" is appended
    PATIENT_FK_FIELDNAME: 'patient_id', // standard name for FK to patient
    MODIFICATION_TIMESTAMP_FIELDNAME: 'when_last_modified',

    MOVE_OFF_TABLET_FIELDNAME: "_move_off_tablet",
    // ... must match database.pl on the server
    MOVE_OFF_TABLET_FIELDSPEC: {name: "_move_off_tablet", type: "B"},
    // ... must match MOVE_OFF_TABLET_FIELDNAME above and type BOOLEAN below

    // Internal codes. Must each be unique:
    TYPE_PK: "P",
    TYPE_TEXT: "T",
    TYPE_INTEGER: "I",
    TYPE_BIGINT: "H", // huge
    TYPE_REAL: "R",
    TYPE_DATETIME: "D",
    TYPE_DATE: "d",
    TYPE_BLOBID: "X",
    TYPE_BOOLEAN: "B",

    BLOB_TABLE: "blobs",
    BLOB_PKNAME: "id",
    BLOB_DIRECTORY: Titanium.Filesystem.applicationDataDirectory,
    BLOB_FILENAME_PREFIX: "blob_",

    PATIENT_TABLE: "patient",
    NUMBER_OF_IDNUMS: 8,
    IDDESC_FIELD_PREFIX: "iddesc",
    IDSHORTDESC_FIELD_PREFIX: "idshortdesc",

    EXTRASTRINGS_TABLE: "extrastrings",
    STOREDVARS_TABLE: "storedvars",
    STOREDVARS_PRIVATE_TABLE: "storedvarsprivate"
};
