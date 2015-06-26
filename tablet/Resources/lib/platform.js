// platform.js

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

/*jslint node: true */
"use strict";
/*global Titanium */

Titanium.API.info("Titanium.Platform.osname = " + Titanium.Platform.osname);

var android = (Titanium.Platform.osname === 'android');
exports.android = android;

var ipad = (Titanium.Platform.osname === 'ipad');
exports.ipad = ipad;

var iphone = (Titanium.Platform.osname === 'iphone');
exports.iphone = iphone;

var ios = iphone || ipad;
exports.ios = ios;

var mobileweb = (Titanium.Platform.osname === 'mobileweb');
exports.mobileweb = mobileweb;

var isDatabaseSupported = (android || ios);
exports.isDatabaseSupported = isDatabaseSupported;

var isFileExportSupported = android;
exports.isFileExportSupported = isFileExportSupported;

var useMockTables = false;
exports.useMockTables = useMockTables;

var isBlockingHttpSupported = (ios || mobileweb);
exports.isBlockingHttpSupported = isBlockingHttpSupported;

function translateFilename(relativeFilename) {
    // relativeFilename should descend from the Resources directory, e.g.
    // "images/camcops/add.png"
    if (mobileweb) { return relativeFilename; }
    return "/" + relativeFilename;
}
exports.translateFilename = translateFilename;

function translateFilenameForWebView(relativeFilename) {
    // relativeFilename should descend from the Resources directory, e.g.
    // "images/camcops/add.png"
    if (mobileweb) { return "../" + relativeFilename; }
    return relativeFilename;
}
exports.translateFilenameForWebView = translateFilenameForWebView;

function getNativePathOfResourceFile(filename) {
    // we may have a filename with '/' but we don't want that, or we'll get a
    // '//' in the string from the nativePath call.
    // So strip leading "/":
    while (filename.charAt(0) === "/") {
        filename = filename.substring(1);
    }
    return Titanium.Filesystem.getFile(Titanium.Filesystem.resourcesDirectory,
                                       filename).nativePath;
}
exports.getNativePathOfResourceFile = getNativePathOfResourceFile;

function isIOS7Plus() {
    // http://docs.appcelerator.com/titanium/latest/#!/guide/iOS_7_Migration_Guide
    // iOS-specific test
    if (Titanium.Platform.name === 'iPhone OS') {
        var version = Titanium.Platform.version.split("."),
            major = parseInt(version[0], 10);

        // Can only test this support on a 3.2+ device
        if (major >= 7) {
            return true;
        }
    }
    return false;
}

exports.ios7plus = isIOS7Plus();
