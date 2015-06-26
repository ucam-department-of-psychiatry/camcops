// imagecache.js

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

var cache = {},
    platform = require('lib/platform');

function reportCacheSize() {
    var key,
        size = 0;
    for (key in cache) {
        if (cache.hasOwnProperty(key) && cache[key].length !== undefined) {
            size += cache[key].length;
        }
    }
    Titanium.API.info("Image cache size: " + size);
}

function getImage(filename) {
    var file;
    if (!cache.hasOwnProperty(filename) || cache[filename] === null) {
        Titanium.API.info("Caching image: " + filename);
        if (platform.mobileweb) {
            // ImageView creating using Blob/File objects not supported under
            // MobileWeb.
            cache[filename] = filename;
        } else {
            file = Titanium.Filesystem.getFile(
                Titanium.Filesystem.resourcesDirectory,
                filename
            );
            if (!file.exists()) {
                Titanium.API.warn("File doesn't exist: " + filename);
                return null;
            }
            cache[filename] = file.read();
        }
        reportCacheSize();
    }
    return cache[filename];
}
exports.getImage = getImage;

function clearCache() {
    var key;
    for (key in cache) {
        if (cache.hasOwnProperty(key)) {  // for JSLint
            cache[key] = null;  // for garbage collection
        }
    }
    cache = {};
    reportCacheSize();
}
exports.clearCache = clearCache;

