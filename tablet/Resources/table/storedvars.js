// storedvars.js

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

/*jslint node: true, newcap: true, nomen: true */
"use strict";
/*global Titanium, L */


Titanium.API.info("storedvars: Setting up stored variables system...");

// In this file, in particular, be careful not to include anything that will
// read a storedvar -- under mobileweb, we need the user's details first.
var platform = require('lib/platform'),
    DBCONSTANTS = require('common/DBCONSTANTS'),
    VERSION = require('common/VERSION'),
    lang = require('lib/lang'),
    dbcommon = require('lib/dbcommon'),
    // TABLE
    sortorder = "id",
    fieldlist = [
        // (a) SQL field names; (b) object member variables;
        // (c) PK must be first (assumed by dbcommon.js)
        {name: 'id', type: DBCONSTANTS.TYPE_PK},
        {name: 'name', type: DBCONSTANTS.TYPE_TEXT, unique: true, mandatory: true},
        {name: 'type', type: DBCONSTANTS.TYPE_TEXT, mandatory: true},
        {name: 'valueInteger', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'valueText', type: DBCONSTANTS.TYPE_TEXT},
        {name: 'valueReal', type: DBCONSTANTS.TYPE_REAL}
    ],
    SV_TYPE_INTEGER = "integer",
    SV_TYPE_TEXT = "text",
    SV_TYPE_REAL = "real",
    SV_TYPE_BOOLEAN = "boolean";

dbcommon.appendCommonFields(fieldlist);


//=============================================================================
// When database supported: stored variables via SQLite
//=============================================================================

// STRUCTURE

function StoredVariable_db(props) {
    // name, type, defaultValue
    if (props.isPrivate === undefined) {
        props.isPrivate = false;
    }
    if (platform.mobileweb) {
        // no device-local storage or storedvars_private table on mobileweb
        props.isPrivate = false;
    }
    if (props.name === undefined || props.name === null) {
        throw new Error("Attempt to create StoredVariable without name");
    }
    this._tablename = (props.isPrivate ?
            DBCONSTANTS.STOREDVARS_PRIVATE_TABLE :
            DBCONSTANTS.STOREDVARS_TABLE
    ); // per-instance setting overriding class setting
    dbcommon.DatabaseObject.call(this); // call base constructor
    this.name = props.name;
    this.type = props.type;
    // initialize
    if (!this.dbreadUniqueField('name', props.name)) {
        Titanium.API.trace("StoredVariable_db: NOT found in database");
        // Not found in database
        if (props.defaultValue !== undefined) {
            // Not found. Setting default value.
            this.setValue(props.defaultValue);
        } else {
            // Not found. No default value.
            this.dbstore(); // store at least the type choice
        }
    }
    this.type = props.type;
    // just in case it existed with a different type before
}

lang.inheritPrototype(StoredVariable_db, dbcommon.DatabaseObject);
lang.extendPrototype(StoredVariable_db, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)
    _objecttype: StoredVariable_db,
    // OVERRIDDEN, SEE ABOVE // _tablename: tablename,
    _fieldlist: fieldlist,
    _sortorder: sortorder,

    // OTHER

    setValue: function (value) {
        switch (this.type) {
        case SV_TYPE_INTEGER:
            this.valueInteger = parseInt(value, 10); // base 10
            // ... https://developer.mozilla.org/en-US/docs/JavaScript/Reference/Global_Objects/parseInt
            if (isNaN(this.valueInteger)) {
                this.valueInteger = null;
            }
            break;
        case SV_TYPE_BOOLEAN:
            this.valueInteger = value ? 1 : 0;
            break;
        case SV_TYPE_TEXT:
            if (value === null) {
                this.valueText = null;
            } else {
                this.valueText = value.toString();
            }
            break;
        case SV_TYPE_REAL:
            this.valueReal = parseFloat(value);
            if (isNaN(this.valueReal)) {
                this.valueReal = null;
            }
            break;
        default:
            throw new Error("Invalid type passed to StoredVariable: " +
                            this.type);
        }
        this.dbstore();
    },

    // get
    getValue: function () {
        switch (this.type) {
        case SV_TYPE_INTEGER:
            return this.valueInteger;
        case SV_TYPE_BOOLEAN:
            return this.valueInteger ? true : false;
        case SV_TYPE_TEXT:
            return this.valueText;
        case SV_TYPE_REAL:
            return this.valueReal;
        default:
            throw new Error("Invalid type passed to StoredVariable: " +
                            this.type);
        }
    }

});

//=============================================================================
// For when no database supported. Stored variables via
// Titanium.App.Properties. All are private.
//=============================================================================

function StoredVariable_titanium(props) {
    // name, type, defaultValue
    if (props.name === undefined || props.name === null) {
        throw new Error("Attempt to create StoredVariable without name");
    }
    this.name = props.name;
    this.type = props.type;
    this.valueInteger = null;
    this.valueText = null;
    this.valueReal = null;

    // initialize
    if (!Titanium.App.Properties.hasProperty(this.name)) {
        // Not found in storage
        if (props.defaultValue !== undefined) {
            this.setValue(props.defaultValue);
        }
    } else {
        // Read from storage
        switch (this.type) {
        case SV_TYPE_INTEGER:
        case SV_TYPE_BOOLEAN:
            this.valueInteger = Titanium.App.Properties.getInt(this.name);
            break;
        case SV_TYPE_TEXT:
            this.valueText = Titanium.App.Properties.getString(this.name);
            break;
        case SV_TYPE_REAL:
            this.valueReal = Titanium.App.Properties.getDouble(this.name);
            break;
        default:
            throw new Error("Invalid type passed to StoredVariable: " +
                            this.type);
        }
    }
}

StoredVariable_titanium.prototype = {

    // set
    setValue: function (value) {
        switch (this.type) {
        case SV_TYPE_INTEGER:
            this.valueInteger = parseInt(value, 10);
            // https://developer.mozilla.org/en-US/docs/JavaScript/Reference/Global_Objects/parseInt
            if (isNaN(this.valueInteger)) {
                this.valueInteger = null;
            }
            Titanium.App.Properties.setInt(this.name, this.valueInteger);
            break;
        case SV_TYPE_BOOLEAN:
            this.valueInteger = value ? 1 : 0;
            Titanium.App.Properties.setInt(this.name, this.valueInteger);
            break;
        case SV_TYPE_TEXT:
            if (value === null) {
                this.valueText = null;
            } else {
                this.valueText = value.toString();
            }
            Titanium.App.Properties.setString(this.name, this.valueText);
            break;
        case SV_TYPE_REAL:
            this.valueReal = parseFloat(value);
            if (isNaN(this.valueReal)) {
                this.valueReal = null;
            }
            Titanium.App.Properties.setDouble(this.name, this.valueReal);
            break;
        default:
            throw new Error("Invalid type passed to StoredVariable: " +
                            this.type);
        }
    },

    // get
    getValue: function () {
        switch (this.type) {
        case SV_TYPE_INTEGER:
            return this.valueInteger;
        case SV_TYPE_BOOLEAN:
            return this.valueInteger ? true : false;
        case SV_TYPE_TEXT:
            return this.valueText;
        case SV_TYPE_REAL:
            return this.valueReal;
        default:
            throw new Error("Invalid type passed to StoredVariable: " +
                            this.type);
        }
    }

};

//=============================================================================
// Which one to use?
//=============================================================================

if (platform.isDatabaseSupported) {
    var StoredVariable = StoredVariable_db;
    var StoredVariable_special = StoredVariable_db;
    // CREATE THE TABLES
    dbcommon.createTable(DBCONSTANTS.STOREDVARS_TABLE, fieldlist);
    dbcommon.createTable(DBCONSTANTS.STOREDVARS_PRIVATE_TABLE, fieldlist);
} else if (platform.mobileweb) {
    var StoredVariable = StoredVariable_db;
    var StoredVariable_special = StoredVariable_titanium;
} else {
    // not sure what would come here!
    var StoredVariable = StoredVariable_titanium;
    var StoredVariable_special = StoredVariable_titanium;
}

//=============================================================================
// Exports for intellectual property controls
//=============================================================================

var USE_TYPE_UNKNOWN = -1;
var USE_TYPE_FALSE = 0;
var USE_TYPE_TRUE = 1;
exports.USE_TYPE_UNKNOWN = USE_TYPE_UNKNOWN;
exports.USE_TYPE_FALSE = USE_TYPE_FALSE;
exports.USE_TYPE_TRUE = USE_TYPE_TRUE;

//=============================================================================
// EXPORT THE VARIABLES
//=============================================================================

// Under mobileweb, we need all these before we can fetch any others.
exports.storeServerPassword = new StoredVariable_special({
    name: 'storeServerPassword',
    type: SV_TYPE_BOOLEAN,
    defaultValue: platform.mobileweb
}); // default must be true on mobileweb
exports.serverUser = new StoredVariable_special({
    name: 'serverUser',
    type: SV_TYPE_TEXT,
    defaultValue: ''
});
exports.serverPasswordObscured = new StoredVariable_special({
    name: 'serverPasswordObscured',
    type: SV_TYPE_TEXT,
    defaultValue: '',
    isPrivate: true
});
exports.serverTimeoutMs = new StoredVariable_special({
    name: 'serverTimeoutMs',
    type: SV_TYPE_INTEGER,
    defaultValue: 60000 // 5s too short for BLOB uploads; try 60s
});
exports.validateSSLCertificates = new StoredVariable_special({
    name: 'validateSSLCertificates',
    type: SV_TYPE_BOOLEAN,
    defaultValue: true
});
exports.obscuringKey = new StoredVariable_special({
    name: 'obscuringKey',
    type: SV_TYPE_TEXT,
    isPrivate: true
});

// These make more sense locally with mobileweb...

exports.databaseVersion = new StoredVariable_special({
    name: 'databaseVersion',
    type: SV_TYPE_REAL,
    defaultValue: VERSION.CAMCOPS_VERSION
});

// which server?
exports.serverAddress = new StoredVariable_special({
    name: 'serverAddress',
    type: SV_TYPE_TEXT
});
exports.serverPort = new StoredVariable_special({
    name: 'serverPort',
    type: SV_TYPE_INTEGER,
    defaultValue: 443
});
exports.serverPath = new StoredVariable_special({
    name: 'serverPath',
    type: SV_TYPE_TEXT,
    defaultValue: platform.mobileweb ? null : 'camcops/database'
});

exports.createStoredVariables = function () {
    var i,
        dbupload;
    // Under mobileweb, we delay the creation of these until we can communicate
    // with the server's database.
    Titanium.API.trace("createStoredVariables()");

    // device codes
    exports.unlockPasswordHash = new StoredVariable({
        name: 'unlockPasswordHash',
        type: SV_TYPE_TEXT,
        isPrivate: true
    });
    exports.privilegePasswordHash = new StoredVariable({
        name: 'privilegePasswordHash',
        type: SV_TYPE_TEXT,
        isPrivate: true
    });

    // about the device
    exports.deviceFriendlyName = new StoredVariable({
        name: 'deviceFriendlyName',
        type: SV_TYPE_TEXT
    });

    // terms of use
    exports.agreedTermsOfUseAt = new StoredVariable({
        name: 'agreedTermsOfUseAt',
        type: SV_TYPE_TEXT
    });

    // from the server
    exports.databaseTitle = new StoredVariable({
        name: 'databaseTitle',
        type: SV_TYPE_TEXT
    });
    for (i = 1; i <= DBCONSTANTS.NUMBER_OF_IDNUMS; i += 1) {
        exports["idDescription" + i] = new StoredVariable({
            name: 'idDescription' + i,
            type: SV_TYPE_TEXT,
            defaultValue: "(unregistered) ID " + i + " number"
        });
        exports["idShortDescription" + i] = new StoredVariable({
            name: 'idShortDescription' + i,
            type: SV_TYPE_TEXT,
            defaultValue: "(unreg)ID" + i
        });
    }
    exports.idPolicyUpload = new StoredVariable({
        name: 'idPolicyUpload',
        type: SV_TYPE_TEXT
    });
    exports.idPolicyFinalize = new StoredVariable({
        name: 'idPolicyFinalize',
        type: SV_TYPE_TEXT
    });
    exports.serverCamcopsVersion = new StoredVariable({
        name: 'serverCamcopsVersion',
        type: SV_TYPE_REAL
    });

    // also about the server
    exports.lastServerRegistration = new StoredVariable({
        name: 'lastServerRegistration',
        type: SV_TYPE_TEXT,
        defaultValue: "(none)"
    });
    exports.lastSuccessfulUpload = new StoredVariable({
        name: 'lastSuccessfulUpload',
        type: SV_TYPE_TEXT,
        defaultValue: "(none)"
    });

    // clinician details (default settings)
    exports.defaultClinicianSpecialty = new StoredVariable({
        name: 'defaultClinicianSpecialty',
        type: SV_TYPE_TEXT
    });
    exports.defaultClinicianName = new StoredVariable({
        name: 'defaultClinicianName',
        type: SV_TYPE_TEXT
    });
    exports.defaultClinicianProfessionalRegistration = new StoredVariable({
        name: 'defaultClinicianProfessionalRegistration',
        type: SV_TYPE_TEXT
    });
    exports.defaultClinicianPost = new StoredVariable({
        name: 'defaultClinicianPost',
        type: SV_TYPE_TEXT
    });
    exports.defaultClinicianService = new StoredVariable({
        name: 'defaultClinicianService',
        type: SV_TYPE_TEXT
    });
    exports.defaultClinicianContactDetails = new StoredVariable({
        name: 'defaultClinicianContactDetails',
        type: SV_TYPE_TEXT
    });

    // questionnaire configuration
    exports.questionnaireTextSizePercent = new StoredVariable({
        name: 'questionnaireTextSizePercent',
        type: SV_TYPE_INTEGER,
        defaultValue: 100
    });
    exports.offerUploadAfterEdit = new StoredVariable({
        name: 'offerUploadAfterEdit',
        type: SV_TYPE_BOOLEAN,
        defaultValue: false
    });
    exports.multilineTextFixedHeight = new StoredVariable({
        name: 'multilineTextFixedHeight',
        type: SV_TYPE_BOOLEAN,
        defaultValue: true
        // looks nicer when false, but keyboard unpleasantly slow on iPad
        // unless true
    });
    exports.multilineDefaultNLines = new StoredVariable({
        // For when multilineTextFixedHeight is true
        name: 'multilineDefaultNLines',
        type: SV_TYPE_INTEGER,
        defaultValue: 5
    });

    // intellectual property controls
    exports.useClinical = new StoredVariable({
        name: 'useClinical',
        type: SV_TYPE_INTEGER,
        defaultValue: USE_TYPE_UNKNOWN
    });
    exports.useEducational = new StoredVariable({
        name: 'useEducational',
        type: SV_TYPE_INTEGER,
        defaultValue: USE_TYPE_UNKNOWN
    });
    exports.useResearch = new StoredVariable({
        name: 'useResearch',
        type: SV_TYPE_INTEGER,
        defaultValue: USE_TYPE_UNKNOWN
    });
    exports.useCommercial = new StoredVariable({
        name: 'useCommercial',
        type: SV_TYPE_INTEGER,
        defaultValue: USE_TYPE_UNKNOWN
    });

    // analytics
    exports.sendAnalytics = new StoredVariable({
        name: 'sendAnalytics',
        type: SV_TYPE_BOOLEAN,
        defaultValue: true
    });

    exports.whiskerHost = new StoredVariable({
        name: 'whiskerHost',
        type: SV_TYPE_TEXT,
        defaultValue: "localhost"
    });
    exports.whiskerPort = new StoredVariable({
        name: 'whiskerPort',
        type: SV_TYPE_INTEGER,
        defaultValue: 3233
    });
    exports.whiskerTimeoutMs = new StoredVariable_special({
        name: 'whiskerTimeoutMs',
        type: SV_TYPE_INTEGER,
        defaultValue: 5000
    });

    // mobileweb special modifications
    if (platform.mobileweb) {
        Titanium.API.trace("Mobileweb pseudo-registration...");
        dbupload = require('lib/dbupload');
        exports.deviceFriendlyName.setValue("MobileWeb client for user " +
                                            exports.serverUser.getValue());
        dbupload.registerBlockingForMobileweb();
        Titanium.API.trace("... mobileweb pseudo-registration finished.");
    }
};

//=============================================================================
// Functions operating on stored variables
//=============================================================================

exports.askUserForSpecialMobilewebVariables = function (callbackfunction) {
    Titanium.API.trace("askUserForSpecialMobilewebVariables()");
    var AskUsernamePasswordWindow = require('screen/AskUsernamePasswordWindow'),
        win,
        userEnteredDataFn = function (username, password) {
            // ignored: verified, cancelled
            Titanium.API.trace("askUserForSpecialMobilewebVariables() " +
                               "callback");
            var netcore = require('lib/netcore'),
                rnc_crypto = require('lib/rnc_crypto');
            exports.storeServerPassword.setValue(true);
            exports.serverUser.setValue(username);
            exports.serverPasswordObscured.setValue(
                rnc_crypto.obscurePassword(password)
            );
            // Crashes:
            // if (win) {
            //    win.close();
            // }
            win = null;
            netcore.setTempServerPassword(password);
            callbackfunction();
        };
    win = new AskUsernamePasswordWindow({
        askUsername: true,
        captionUsername: L("caption_login_username"),
        hintUsername: L('hint_server_user'),
        captionPassword: L("caption_login_password"),
        hintPassword: L('hint_server_password'),
        verifyAgainstHash: false,
        showCancel: false,
        callbackFn: userEnteredDataFn
    });
    win.open();
};

function getServerURL_genuine() {
    return (
        "https://" + exports.serverAddress.getValue() + ":" +
        exports.serverPort.getValue() + "/" +
        exports.serverPath.getValue()
    );
}

function getServerURL_mobileweb() {
    return "../database"; // *** imperfect URL for getServerURL_mobileweb
    // THIS NEEDS MAKING MORE FLEXIBLE, but it works when
    // the mobileweb script starts at XXX/camcops/mobileweb/index.html
    // and the database handler is XXX/camcops/database

    // IN THIS FILE, FOR MOBILEWEB:
    // - store username/password
    // - when this module first loads, ask for username/password
    //   (?and the "../database" bit?)
    // - redirect all variable requests to the server
}

if (platform.mobileweb) {
    exports.getServerURL = getServerURL_mobileweb;
} else {
    exports.getServerURL = getServerURL_genuine;
}

function serverInfoPresent() {
    return platform.mobileweb || (
        exports.serverAddress.getValue() &&
        exports.serverPort.getValue() &&
        exports.serverPath.getValue()
    );
}
exports.serverInfoPresent = serverInfoPresent;

Titanium.API.info("storedvars: ... done");
