// taskcommon.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium, L, escape */

var uifunc = require('lib/uifunc'),
    dbcommon = require('lib/dbcommon'),
    DBCONSTANTS = require('common/DBCONSTANTS'),
    lang = require('lib/lang'),
    KeyValuePair = require('lib/KeyValuePair'),
    yesChar = "Y",
    noChar = "N";

function BaseTask(patient_id) {
    var moment = require('lib/moment');
    dbcommon.DatabaseObject.call(this); // call base constructor
    // ... which will write nulls/default values to all fields
    this.when_created = moment();
    if (!this._anonymous) {
        this[DBCONSTANTS.PATIENT_FK_FIELDNAME] = patient_id;
    }
}
lang.inheritPrototype(BaseTask, dbcommon.DatabaseObject);
lang.extendPrototype(BaseTask, {
    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    // OVERRIDE IN DERIVED CLASS: // _objecttype: Patient,
    // OVERRIDE IN DERIVED CLASS: // _tablename: tablename,
    // OVERRIDE IN DERIVED CLASS: // _fieldlist: fieldlist,
    _sortorder: "id", // default sort order

    // KEY CLASS FIELDS (default values, may be overridden by derived class)

    _anonymous: false,
    _crippled: false,
    _editable: true,
    _prohibitCommercial: false,
    _prohibitResearch: false,
    _extrastringTaskname: "",

    // OTHER

    getPatientID: function () {
        if (this._anonymous) {
            return null;
        }
        return this[DBCONSTANTS.PATIENT_FK_FIELDNAME];
    },

    getPatientName: function () {
        var Patient = require('table/Patient'),
            patient = new Patient(this.getPatientID());
        return patient.getLine1();
    },

    isTaskPermissible: function () {
        var storedvars = require('table/storedvars');
        if (this._prohibitCommercial && storedvars.useCommercial.getValue() !==
                storedvars.USE_TYPE_FALSE) {
            return false;
        }
        if (this._prohibitResearch && storedvars.useResearch.getValue() !==
                storedvars.USE_TYPE_FALSE) {
            return false;
        }
        return true;
    },

    isTaskCrippled: function () {
        return this._crippled;
    },

    whyNotPermissible: function () {
        var storedvars = require('table/storedvars');
        if (this._prohibitCommercial) {
            if (storedvars.useCommercial.getValue() ===
                    storedvars.USE_TYPE_TRUE) {
                return (L('task_prohibits_commercial') + " " +
                        L('app_commercial_true') + " " +
                        L('ask_the_copyright_holder'));
            }
            if (storedvars.useCommercial.getValue() !==
                    storedvars.USE_TYPE_FALSE) {
                return (L('task_prohibits_commercial') + " " +
                        L('app_commercial_unknown'));
            }
        }
        if (this._prohibitResearch) {
            if (storedvars.useResearch.getValue() ===
                    storedvars.USE_TYPE_TRUE) {
                return (L('task_prohibits_research') + " " +
                        L('app_research_true') + " " +
                        L('ask_the_copyright_holder'));
            }
            if (storedvars.useResearch.getValue() !==
                    storedvars.USE_TYPE_FALSE) {
                return (L('task_prohibits_research') + " " +
                        L('app_research_unknown'));
            }
        }
        return L('task_permissible');
    },

    isEditable: function () {
        return this._editable;
    },

    isAnonymous: function () {
        return this._anonymous;
    },

    getCreationDateTime: function () {
        return this.when_created;
    },

    getCreationDateTimeNice: function () {
        if (!this.when_created) {
            return "";
        }
        var UICONSTANTS = require('common/UICONSTANTS');
        return this.when_created.format(UICONSTANTS.TASK_DATETIME_FORMAT);
    },

    getSummaryView: function () {
        var UICONSTANTS = require('common/UICONSTANTS');
        return Titanium.UI.createLabel({
            text: this.getSummary(),
            font: UICONSTANTS.TASK_SUMMARY_FONT,
            color: (
                this.isComplete() ?
                        UICONSTANTS.TASK_SUMMARY_COLOUR_COMPLETE :
                        UICONSTANTS.TASK_SUMMARY_COLOUR_INCOMPLETE
            ),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
            top: 0,
            left: 0,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.SIZE
        });
    },

    defaultFinishedFn: function (result, editing_time_s) {
        var UICONSTANTS = require('common/UICONSTANTS'),
            EVENTS = require('common/EVENTS'),
            moment,
            store = false;
        if (result !== UICONSTANTS.READONLYVIEWFINISHED) {
            if (this.when_firstexit === undefined ||
                    this.when_firstexit === null) {
                moment = require('lib/moment');
                this.when_firstexit = moment();
                if (result === UICONSTANTS.FINISHED) {
                    this.firstexit_is_finish = 1;
                } else if (result === UICONSTANTS.ABORTED) {
                    this.firstexit_is_abort = 1;
                }
                store = true;
            }
            if (editing_time_s > 0) {
                if (this.editing_time_s === undefined) {
                    this.editing_time_s = 0;
                }
                this.editing_time_s += editing_time_s;
                store = true;
            }
            if (store) {
                this.dbstore();
                // Note that this will 'touch' when_last_modified.
                // See CLIENT_DATE_FIELD in database.py on the server, and
                // MODIFICATION_TIMESTAMP_FIELDNAME on the tablet.
            }
        }
        Titanium.App.fireEvent(EVENTS.TASK_FINISHED, {
            tablename: this._tablename,
            id: this.id,
            result: result
        });
    },

    isCompleteSuffix: function () {
        return this.isComplete() ? "" : (" " + L('incomplete'));
    },

    isFemale: function () {
        if (this._anonymous) {
            return null;
        }
        var Patient = require('table/Patient'),
            female = new Patient(
                this[DBCONSTANTS.PATIENT_FK_FIELDNAME]
            ).isFemale();
        return female;
    },

    setDefaultClinicianVariablesAtFirstUse: function (readOnly) {
        if (readOnly) {
            return;
        }
        var storedvars = require('table/storedvars');
        if (this.id === undefined || this.id === null) {
            // first edit
            this.clinician_specialty = storedvars.defaultClinicianSpecialty.getValue();
            this.clinician_name = storedvars.defaultClinicianName.getValue();
            this.clinician_professional_registration = storedvars.defaultClinicianProfessionalRegistration.getValue();
            this.clinician_post = storedvars.defaultClinicianPost.getValue();
            this.clinician_service = storedvars.defaultClinicianService.getValue();
            this.clinician_contact_details = storedvars.defaultClinicianContactDetails.getValue();
        }
    },

    getClinicianQuestionnaireBlock: function () {
        var UICONSTANTS = require('common/UICONSTANTS');
        return {
            type: "QuestionTypedVariables",
            mandatory: false,
            useColumns: true,
            variables: [
                {
                    type: UICONSTANTS.TYPEDVAR_TEXT,
                    field: "clinician_specialty",
                    prompt: L("clinician_specialty")
                },
                {
                    type: UICONSTANTS.TYPEDVAR_TEXT,
                    field: "clinician_name",
                    prompt: L("clinician_name")
                },
                {
                    type: UICONSTANTS.TYPEDVAR_TEXT,
                    field: "clinician_professional_registration",
                    prompt: L("clinician_professional_registration")
                },
                {
                    type: UICONSTANTS.TYPEDVAR_TEXT,
                    field: "clinician_post",
                    prompt: L("clinician_post")
                },
                {
                    type: UICONSTANTS.TYPEDVAR_TEXT,
                    field: "clinician_service",
                    prompt: L("clinician_service")
                },
                {
                    type: UICONSTANTS.TYPEDVAR_TEXT,
                    field: "clinician_contact_details",
                    prompt: L("clinician_contact_details")
                }
            ]
        };
    },

    getClinicianDetailsPage: function () {
        return {
            title: L("clinician_details"),
            clinician: true,
            elements: [ this.getClinicianQuestionnaireBlock() ]
        };
    },

    getRespondentQuestionnaireBlock: function () {
        var UICONSTANTS = require('common/UICONSTANTS');
        return {
            type: "QuestionTypedVariables",
            mandatory: false,
            useColumns: true,
            variables: [
                {
                    type: UICONSTANTS.TYPEDVAR_TEXT,
                    field: "respondent_name",
                    prompt: L("respondent_name")
                },
                {
                    type: UICONSTANTS.TYPEDVAR_TEXT,
                    field: "respondent_relationship",
                    prompt: L("respondent_relationship")
                }
            ]
        };
    },

    getRespondentDetailsPage: function () {
        return {
            title: L("respondent_details"),
            clinician: true,
            elements: [ this.getRespondentQuestionnaireBlock() ]
        };
    },

    getClinicianAndRespondentDetailsPage: function () {
        return {
            title: L("clinician_and_respondent_details"),
            clinician: true,
            elements: [
                this.getClinicianQuestionnaireBlock(),
                this.getRespondentQuestionnaireBlock()
            ]
        };
    },

    XSTRING: function (name, defaultvalue) {
        var extrastrings = require('table/extrastrings');
        defaultvalue = defaultvalue || ("[" + this._extrastringTaskname +
                                        ": " + name + "]");
        return extrastrings.get(
            this._extrastringTaskname,
            name,
            defaultvalue
        );
    }

});
exports.BaseTask = BaseTask;

//=============================================================================
// Complete or not?
//=============================================================================

function isComplete(object, prefix, start, end) {
    var i;
    for (i = start; i <= end; ++i) {
        if (object[prefix + i] === undefined || object[prefix + i] === null) {
            return false;
        }
    }
    return true;
}
exports.isComplete = isComplete;

function isCompleteByFieldnameArray(object, fields) {
    var i;
    for (i = 0; i < fields.length; ++i) {
        if (object[fields[i]] === undefined || object[fields[i]] === null) {
            return false;
        }
    }
    return true;
}
exports.isCompleteByFieldnameArray = isCompleteByFieldnameArray;

function atLeastOneNotNullByFieldnameArray(object, fields) {
    var i;
    for (i = 0; i < fields.length; ++i) {
        if (object[fields[i]] !== undefined && object[fields[i]] !== null) {
            return true;
        }
    }
    return false;
}
exports.atLeastOneNotNullByFieldnameArray = atLeastOneNotNullByFieldnameArray;

function numCompleteByFieldnameArray(object, fields) {
    var n = 0,
        i;
    for (i = 0; i < fields.length; ++i) {
        if (object[fields[i]] !== undefined && object[fields[i]] !== null) {
            n += 1;
        }
    }
    return n;
}
exports.numCompleteByFieldnameArray = numCompleteByFieldnameArray;

function numIncompleteByFieldnameArray(object, fields) {
    var n = 0,
        i;
    for (i = 0; i < fields.length; ++i) {
        if (object[fields[i]] === undefined || object[fields[i]] === null) {
            n += 1;
        }
    }
    return n;
}
exports.numIncompleteByFieldnameArray = numIncompleteByFieldnameArray;

function isCompleteByFieldlistArray(object, fieldspecs) {
    // As for isCompleteByFieldnameArray, but using a list of field definitions
    var i,
        fieldname;
    for (i = 0; i < fieldspecs.length; ++i) {
        fieldname = fieldspecs[i].name;
        if (object[fieldname] === undefined || object[fieldname] === null) {
            return false;
        }
    }
    return true;
}
exports.isCompleteByFieldlistArray = isCompleteByFieldlistArray;

//=============================================================================
// True or not?
//=============================================================================

function atLeastOneTrueByFieldnameArray(object, fields) {
    var i;
    for (i = 0; i < fields.length; ++i) {
        if (object[fields[i]]) {
            return true;
        }
    }
    return false;
}
exports.atLeastOneTrueByFieldnameArray = atLeastOneTrueByFieldnameArray;

function totalScore(object, prefix, start, end) {
    var total = 0,
        i;
    for (i = start; i <= end; ++i) {
        if (object[prefix + i] !== undefined && object[prefix + i] !== null) {
            total += object[prefix + i];
        }
    }
    return total;
}
exports.totalScore = totalScore;

function asBinary(object, field) {
    return object[field] ? 1 : 0;
}
exports.asBinary = asBinary;

function countBooleansByFieldnameArray(object, arr) {
    var total = 0,
        i;
    for (i = 0; i < arr.length; ++i) {
        // http://stackoverflow.com/questions/3010840/
        total += object[arr[i]] ? 1 : 0;
    }
    return total;
}
exports.countBooleansByFieldnameArray = countBooleansByFieldnameArray;

function countBooleans(object, prefix, start, end) {
    var total = 0,
        i;
    for (i = start; i <= end; ++i) {
        total += object[prefix + i] ? 1 : 0;
    }
    return total;
}
exports.countBooleans = countBooleans;

function allTrue(object, prefix, start, end) {
    var i;
    for (i = start; i <= end; ++i) {
        if (!object[prefix + i]) {
            return false;
        }
    }
    return true;
}
exports.allTrue = allTrue;

function allTrueByFieldnameArray(object, arr) {
    var i;
    for (i = 0; i < arr.length; ++i) {
        if (!object[arr[i]]) {
            return false;
        }
    }
    return true;
}
exports.allTrueByFieldnameArray = allTrueByFieldnameArray;

function noneTrue(object, prefix, start, end) {
    var i;
    for (i = start; i <= end; ++i) {
        if (object[prefix + i]) {
            return false;
        }
    }
    return true;
}
exports.noneTrue = noneTrue;

function noneTrueByFieldnameArray(object, arr) {
    var i;
    for (i = 0; i < arr.length; ++i) {
        if (object[arr[i]]) {
            return false;
        }
    }
    return true;
}
exports.noneTrueByFieldnameArray = noneTrueByFieldnameArray;

//=============================================================================
// More...
//=============================================================================

function identity(x) {
    return x;
}
exports.identity = identity;

function descriptionValuePair(object, description, fieldname, transform,
                              spacer) {
    if (transform === undefined) {
        transform = identity;
    }
    if (spacer === undefined) {
        spacer = ": ";
    }
    return description + spacer + transform(object[fieldname]) + "\n";
}
exports.descriptionValuePair = descriptionValuePair;

function lstringValuePair(object, lstringname, fieldname, transform, spacer) {
    if (transform === undefined) {
        transform = identity;
    }
    if (spacer === undefined) {
        spacer = ": ";
    }
    return L(lstringname) + spacer + transform(object[fieldname]) + "\n";
}
exports.lstringValuePair = lstringValuePair;

function valueDetail(object, stringprefix, stringsuffix, spacer, fieldprefix,
                     start, end) {
    var msg = "",
        i;
    for (i = start; i <= end; ++i) {
        msg += (L(stringprefix + i + stringsuffix) + spacer +
                object[fieldprefix + i] + "\n");
    }
    return msg;
}
exports.valueDetail = valueDetail;

function yesNoNullDetail(object, stringprefix, stringsuffix, spacer,
                         fieldprefix, start, end) {
    var msg = "",
        i;
    for (i = start; i <= end; ++i) {
        msg += (L(stringprefix + i + stringsuffix) + spacer +
                uifunc.yesNoNull(object[fieldprefix + i]) + "\n");
    }
    return msg;
}
exports.yesNoNullDetail = yesNoNullDetail;

//=============================================================================
// Standard options
//=============================================================================

exports.NO_CHAR = noChar;
exports.YES_CHAR = yesChar;

exports.OPTIONS_YES_NO_CHAR = [
    new KeyValuePair(L('Yes'), yesChar),
    new KeyValuePair(L('No'), noChar)
];
exports.OPTIONS_YES_NO_BOOLEAN = [
    new KeyValuePair(L('Yes'), true),
    new KeyValuePair(L('No'), false)
];
exports.OPTIONS_YES_NO_INTEGER = [
    new KeyValuePair(L('Yes'), 1),
    new KeyValuePair(L('No'), 0)
];
exports.OPTIONS_NO_YES_CHAR = [
    new KeyValuePair(L('No'), noChar),
    new KeyValuePair(L('Yes'), yesChar)
];
exports.OPTIONS_NO_YES_BOOLEAN = [
    new KeyValuePair(L('No'), false),
    new KeyValuePair(L('Yes'), true)
];
exports.OPTIONS_NO_YES_INTEGER = [
    new KeyValuePair(L('No'), 0),
    new KeyValuePair(L('Yes'), 1)
];

exports.OPTIONS_INCORRECT_CORRECT_BOOLEAN = [
    new KeyValuePair(L('incorrect'), false),
    new KeyValuePair(L('correct'), true)
];
exports.OPTIONS_INCORRECT_CORRECT_INTEGER = [
    new KeyValuePair(L('incorrect'), 0),
    new KeyValuePair(L('correct'), 1)
];

exports.OPTIONS_FALSE_TRUE_BOOLEAN = [
    new KeyValuePair(L("False"), false),
    new KeyValuePair(L("True"), true)
];

exports.OPTIONS_ABSENT_PRESENT_BOOLEAN = [
    new KeyValuePair(L("Absent"), false),
    new KeyValuePair(L("Present"), true)
];

//=============================================================================
// Arrays and strings
//=============================================================================

function arrayLookup(array, index) {
    return lang.arrayGetValueOrDefault(array, index, "?");
}
exports.arrayLookup = arrayLookup;

function stringArrayFromSequence(prefix, start, end, suffix) {
    if (suffix === undefined) {
        suffix = "";
    }
    var arr = [],
        i;
    for (i = start; i <= end; ++i) {
        arr.push(prefix + i + suffix);
    }
    return arr;
}
exports.stringArrayFromSequence = stringArrayFromSequence;

function localizedStringArrayFromSequence(prefix, start, end, suffix) {
    var stringnames = stringArrayFromSequence(prefix, start, end, suffix),
        arr = [],
        i;
    for (i = 0; i < stringnames.length; ++i) {
        arr.push(L(stringnames[i]));
    }
    return arr;
}
exports.localizedStringArrayFromSequence = localizedStringArrayFromSequence;

function localizedStringArrayBySuffixArray(prefix, suffixarray) {
    var arr = [],
        i;
    for (i = 0; i < suffixarray.length; ++i) {
        arr.push(L(prefix + suffixarray[i]));
    }
    return arr;
}
exports.localizedStringArrayBySuffixArray = localizedStringArrayBySuffixArray;

//=============================================================================
// Webview
//=============================================================================

function createFullscreenWebviewWindow(html, nameEventFromWebview,
                                       fnEventFromWebView) {
    var webview = Titanium.UI.createWebView({
            html: html,
            top: 0,
            left: 0,
            height: Titanium.UI.FILL,
            width: Titanium.UI.FILL,
            focusable: true, // 2015-02-04
            willHandleTouches: false, // changed 2015-02-04... true, // for iOS
            scalesPageToFit: false, // prevents zooming on iOS
            enableZoomControls: false, // for Android
            scrollsToTop: false, // iOS
            disableBounce: true, // iOS
            showScrollbars: false, // MobileWeb?
            keepScreenOn: true // Android
            // makes no difference // borderRadius: 0,
            // http://developer.appcelerator.com/question/118677/masking-or-hiding-overflow-from-a-view
        }),
        // View to make it fullscreen
        fsview = uifunc.createFullscreenView({}),
        window = Titanium.UI.createWindow({
            navBarHidden: true,
            fullscreen: true,
            orientationModes: [
                Titanium.UI.LANDSCAPE_RIGHT,
                Titanium.UI.LANDSCAPE_LEFT
            ] // disallow portrait mode
        });
    // ***
    function keypressed(e) {
        // experimental! Android only?
        Titanium.API.trace("WEBVIEW KEY EVENT: " + JSON.stringify(e));
    }

    fsview.add(webview);
    webview.addEventListener('keypressed', keypressed);
    // Window
    uifunc.addAndroidCloser(window);
    window.add(fsview);
    // Window listeners and cleanup
    Titanium.App.addEventListener(nameEventFromWebview, fnEventFromWebView);
    // ... should have a matching removeEventListener call somewhere
    window.addEventListener('close', function () {
        webview.removeEventListener('keypressed', keypressed);
        Titanium.App.removeEventListener(nameEventFromWebview,
                                         fnEventFromWebView);
        webview.evalJS("shutdown()"); // we seem to have to do this by hand
    });
    return window;
}
exports.createFullscreenWebviewWindow = createFullscreenWebviewWindow;

function processWebviewSoundRequest(e, eventToWebview) {
    // return value: was the event handled?
    var soundhandler = require('lib/soundhandler');
    switch (e.eventType) {
    case "loadsound":
        if (e.finishedEventParams && eventToWebview) {
            soundhandler.loadSound({
                filename: e.sound,
                volume: e.volume,
                fnSoundComplete: function () {
                    Titanium.API.trace(
                        "taskcommon.processWebviewSoundRequest: " +
                            "fnSoundComplete reached for " + e.sound
                    );
                    Titanium.App.fireEvent(eventToWebview,
                                           e.finishedEventParams);
                }
            });
        } else {
            soundhandler.loadSound({
                filename: e.sound,
                volume: e.volume
            });
        }
        break;
    case "setvolume":
        soundhandler.setVolume(e.sound, e.volume);
        break;
    case "playsound":
        soundhandler.playSound(e.sound);
        break;
    case "pausesound":
        soundhandler.pauseSound(e.sound);
        break;
    case "stopsound":
        soundhandler.stopSound(e.sound);
        break;
    case "unloadsound":
        soundhandler.unloadSound(e.sound);
        break;
    case "exit":
    case "abort":
        soundhandler.unloadAllSounds();
        return false;
        // for these events, we do something, but allow the caller to do
        // things too
    default:
        return false;
    }
    return true;
}
exports.processWebviewSoundRequest = processWebviewSoundRequest;

function webviewScriptLoadingHtml(relativeFilename) {
    var platform = require('lib/platform');
    return ('<script src="' +
            platform.translateFilenameForWebView(relativeFilename) +
            '"></script>');
}

function encapsulateRawScriptForHtml(script) {
    return "<script>" + script + "</script>";
}

function getDeviceHeightWidth(landscape) {
    // AS PER http://docs.appcelerator.com/titanium/3.0/#!/api/Titanium.Platform.DisplayCaps
    Titanium.API.info('Titanium.Platform.displayCaps.density: ' +
                      Titanium.Platform.displayCaps.density);
    Titanium.API.info('Titanium.Platform.displayCaps.dpi: ' +
                      Titanium.Platform.displayCaps.dpi);
    Titanium.API.info('Titanium.Platform.displayCaps.platformHeight: ' +
                      Titanium.Platform.displayCaps.platformHeight);
    Titanium.API.info('Titanium.Platform.displayCaps.platformWidth: ' +
                      Titanium.Platform.displayCaps.platformWidth);
    if (Titanium.Platform.osname === 'iphone' ||
            Titanium.Platform.osname === 'ipad' ||
            Titanium.Platform.osname === 'android') {
        Titanium.API.info('Titanium.Platform.displayCaps.logicalDensityFactor: '
                          + Titanium.Platform.displayCaps.logicalDensityFactor);
    }
    if (Titanium.Platform.osname === 'android') {
        Titanium.API.info('Titanium.Platform.displayCaps.xdpi: ' +
                          Titanium.Platform.displayCaps.xdpi);
        Titanium.API.info('Titanium.Platform.displayCaps.ydpi: ' +
                          Titanium.Platform.displayCaps.ydpi);
    }

    landscape = landscape === undefined ? true : false;
    var platform = require('lib/platform'),
        pWidth = Titanium.Platform.displayCaps.platformWidth,
        pHeight = Titanium.Platform.displayCaps.platformHeight,
        width,
        height,
        densityMultiplier = 1;
    if (platform.android) {
        // http://stackoverflow.com/questions/23078780/android-device-height-is-not-accurate-on-titanium-mobile
        densityMultiplier = Titanium.Platform.displayCaps.logicalDensityFactor;
    }
    pWidth = pWidth / densityMultiplier;
    pHeight = pHeight / densityMultiplier;
    if (landscape) {
        width = Math.max(pWidth, pHeight);
        height = Math.min(pWidth, pHeight);
    } else {
        width = pWidth;
        height = pHeight;
    }
    return {
        width: width,
        height: height
    };
}

function insert_standardhtmlhead(html, fullscreen) {
    fullscreen = fullscreen === undefined ? true : fullscreen;
    var platform = require('lib/platform'),
        deviceDimensions,
        width,
        height,
        header;
    if (fullscreen) {
        // Fullscreen going wrong on Android 4.4.2 on a 1900x1200-ish tablet
        // using device-width/device-height, so try to specify exactly:
        // https://developer.appcelerator.com/question/120423/how-to-manipulate-webview-to-fit-every-android-platform
        deviceDimensions = getDeviceHeightWidth(true);
        width = deviceDimensions.width + "px";
        height = deviceDimensions.height + "px";
    } else {
        if (platform.ios) {
            width = "100px";
            height = "100px";
            // ... device-width/device-height go wrong on iOS 7/Titanium 3.2.0,
            // by allowing scrolling. A tiny viewport seems to be fine.
            // But on Android, that doesn't work.
        } else { // Android
            width = "device-width";
            height = "device-height";
        }
    }
    header = (
        '<meta http-equiv="Content-Type"' +
        ' content="text/html; charset=utf-8">' +
        // DISABLE zooming/scaling by the viewport:
        '<meta name="viewport"' +
        ' content="width=' + width + ', height=' + height + ',' +
        ' initial-scale=1, minimum-scale=1, maximum-scale=1,' +
        ' user-scalable=0" />'
    );
    Titanium.API.trace("HTML HEADER: " + header);
    return html.replace(/INSERT_standardhead/, header);
}
exports.insert_standardhtmlhead = insert_standardhtmlhead;

function insertScript_taskhtmlcommon(html) {
    // Under iOS, we can replace with this:
    //      <script src="lib/taskhtmlcommon.jsx"></script>
    // However, under Android 4.4.2, we get:
    //      Uncaught ReferenceError: TASKNAME is not defined
    // ... so this script, and the main task script, presumably have to live in
    // the same memory space, or whatever it's called -- should we include
    // the raw HTML?
    // Well, no, that made no difference. So we have to pass the parameters
    // more sensibly.
    return html.replace(/INSERTSCRIPT_taskhtmlcommon/,
                        webviewScriptLoadingHtml("lib/taskhtmlcommon.jsx"));
}
exports.insertScript_taskhtmlcommon = insertScript_taskhtmlcommon;

function loadHtmlSetParams(htmlFilename, params, scriptFilename) {
    // Incoming filenames are presumed NOT to have been pre-translated.
    // Pass in e.g. "task_html/SOMETHING.html".
    var filefunc = require('lib/filefunc'),
        platform = require('lib/platform'),
        translatedHtmlFilename = platform.translateFilenameForWebView(
            htmlFilename
        ),
        html = filefunc.getTextFileContents(translatedHtmlFilename),
        deviceDimensions = getDeviceHeightWidth(true),
        translatedScriptFilename,
        script,
        paramsString;
    Titanium.API.trace("loadHtmlSetParams: params = " + JSON.stringify(params));
    params.screenWidth = deviceDimensions.width;
    params.screenHeight = deviceDimensions.height;
    paramsString = escape(JSON.stringify(params));

    // Header/viewports:
    html = insert_standardhtmlhead(html);

    // HTML-only specials:
    html = html.replace(/INSERTPARAM_screenWidth/, deviceDimensions.width);
    html = html.replace(/INSERTPARAM_screenHeight/, deviceDimensions.height);

    // Script insertions:
    // Must call these libraries .jsx, or they will be compiled and unusable by
    // HTML.
    // http://developer.appcelerator.com/question/125330/help-js-files-in-resources-directory-for-use-with-webview-arent-packaged-in-android-market-apk-file
    html = insertScript_taskhtmlcommon(html); // also used by QuestionCanvas_webview.js
    html = html.replace(/INSERTSCRIPT_maths/,
                        webviewScriptLoadingHtml("lib/maths.jsx"));
    html = html.replace(/INSERTSCRIPT_raphael/,
                        webviewScriptLoadingHtml("lib/raphael-min.jsx"));
    html = html.replace(/INSERTSCRIPT_moment/,
                        webviewScriptLoadingHtml("lib/moment.min.jsx"));
    Titanium.API.trace("loadHtmlSetParams: paramsString = " + paramsString);
    /*
     * ... escape() is deprecated.
     * Try:
     * var x = "http://w3schools.com/my test.asp?name=ståle&car=saab";
     * escapeURIComponent(x);
     * escapeURI(x);
     * escape(x)
     *
     * Note: the reversing is done in multiple tasks' processing as e.g.
     * JSON.parse(unescape("INSERT_paramsString"));
     */
    if (scriptFilename) {
        translatedScriptFilename = platform.translateFilenameForWebView(
            scriptFilename
        );
        script = filefunc.getTextFileContents(translatedScriptFilename);
        script = script.replace(/INSERT_paramsString/, paramsString);
        html = html.replace(/INSERTSCRIPT_taskscript/,
                            encapsulateRawScriptForHtml(script));
    } else {
        html = html.replace(/INSERT_paramsString/, paramsString);
    }
    // Titanium.API.trace(html);
    return html;
}
exports.loadHtmlSetParams = loadHtmlSetParams;

function parseDataFromWebview(data) {
    var conversion = require('lib/conversion');
    return JSON.parse(data, conversion.json_decoder_reviver);
}
exports.parseDataFromWebview = parseDataFromWebview;

//=============================================================================
// Dates
//=============================================================================

function formatDateSimple(d) {
    if (!d) {
        return "";
    }
    var UICONSTANTS = require('common/UICONSTANTS');
    return d.format(UICONSTANTS.DOB_DATE_FORMAT);
}
exports.formatDateSimple = formatDateSimple;
