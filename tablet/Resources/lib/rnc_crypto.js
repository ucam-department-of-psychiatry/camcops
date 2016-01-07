// rnc_crypto.js

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

/*jslint node: true, plusplus: true, stupid: true */
"use strict";
/*global Int8Array, Uint8Array, Int16Array, Uint16Array, Int32Array, Uint32Array, Float32Array */
// ... http://stackoverflow.com/questions/12392132/does-node-js-provide-a-real-array-implementation
/*global Uint8ClampedArray, Float64Array */

var storedvars = require('table/storedvars'),
    BCRYPT_LOG_ROUNDS = 6,
        // because tablets are pretty slow; see
        // http://security.stackexchange.com/questions/3959/
    obscuringKey = storedvars.obscuringKey.getValue();

if (!obscuringKey) { // not yet set
    obscuringKey = Math.random().toString(36).substring(7);
    // ... some random value: http://stackoverflow.com/questions/1349404/
    storedvars.obscuringKey.setValue(obscuringKey);
}

function hashPassword(plaintextpw) {
    var bcrypt = require('lib/bcrypt'),
        salt = bcrypt.genSaltSync(BCRYPT_LOG_ROUNDS),
        hashedpw = bcrypt.hashSync(plaintextpw, salt);
    return hashedpw;
}
exports.hashPassword = hashPassword;

function isPasswordValid(plaintextpw, storedhash) {
    var bcrypt = require('lib/bcrypt');
    return bcrypt.compareSync(plaintextpw, storedhash);
}
exports.isPasswordValid = isPasswordValid;

function obscurePassword(plaintextpw) {
    var sjcl = require('lib/sjcl');
    if (!plaintextpw) {
        return "";
    }
    return sjcl.encrypt(obscuringKey, plaintextpw);
}
exports.obscurePassword = obscurePassword;

function retrieveObscuredPassword(obscuredpw) {
    var sjcl = require('lib/sjcl');
    if (!obscuredpw) {
        return "";
    }
    return sjcl.decrypt(obscuringKey, obscuredpw);
}
exports.retrieveObscuredPassword = retrieveObscuredPassword;

// For bcrypt.js:
function randomBytes(size) {
    // mimicking the NodeJS crypto function (synchronous version)
    var mersennetwister = require('lib/mersennetwister'),
        r = [],
        i;
    for (i = 0; i < size; ++i) {
        r.push(mersennetwister.instance.byte());
    }
    return r;
}
exports.randomBytes = randomBytes;
exports.pseudoRandomBytes = randomBytes;

// for sjcl.js:
function getRandomValues(arr) {
    // The array will be modified in place.
    // https://developer.mozilla.org/en-US/docs/Web/API/window.crypto.getRandomValues
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Typed_arrays?redirectlocale=en-US&redirectslug=JavaScript%2FTyped_arrays
    var mersennetwister = require('lib/mersennetwister'),
        generator = null,
        i;
    switch (arr.constructor) {
    // Some of these may be iffy! *** (in rnc_crypto.getRandomValues)
    case Int8Array:
    case Uint8Array:
    case Uint8ClampedArray:
        generator = mersennetwister.instance.byte;
        break;
    case Int16Array:
    case Uint16Array:
        generator = mersennetwister.instance.int16;
        break;
    case Int32Array:
    case Uint32Array:
        generator = mersennetwister.instance.int32;
        break;
    case Float32Array:
        generator = mersennetwister.instance.float;
        break;
    case Float64Array:
        generator = mersennetwister.instance.double;
        break;
    }
    if (typeof generator !== "function") {
        throw new Error("Invalid array type passed to getRandomValues");
    }
    for (i = 0; i < arr.length; ++i) {
        arr[i] = generator();
    }
}
exports.getRandomValues = getRandomValues;
