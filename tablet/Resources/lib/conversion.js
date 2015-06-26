// conversion.js

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

/*jslint node: true, plusplus: true, nomen: true */
"use strict";
/*global Titanium */

var moment = require('lib/moment'),
    android = (Titanium.Platform.osname === 'android'),
    BASE64_PNG_URL_PREFIX = "data:image/png;base64,",
    ENCODING_PNGURL = "pngurl",
    DETAILED_DATETIME_FORMAT = "YYYY-MM-DDTHH:mm:ss.SSSZ",
        // ISO-8601 is YYYY-MM-DDTHH:mm:ssZ; we add milliseconds
    DATE_ONLY_FORMAT = "YYYY-MM-DD";

exports.BASE64_PNG_URL_PREFIX = BASE64_PNG_URL_PREFIX;
exports.ENCODING_PNGURL = ENCODING_PNGURL;
exports.DETAILED_DATETIME_FORMAT = DETAILED_DATETIME_FORMAT;
exports.DATE_ONLY_FORMAT = DATE_ONLY_FORMAT;

//=============================================================================
// Base 64 encoding
//=============================================================================

function blobToBase64String(blob) {
    var encodedBlob,
        string;
    if (!blob) {
        return "";
    }
    encodedBlob = Titanium.Utils.base64encode(blob);
    if (!encodedBlob) {
        return "";
    }
    string = encodedBlob.toString();
    return string;
}
exports.blobToBase64String = blobToBase64String;

function base64StringToBlob(string) {
    return Titanium.Utils.base64decode(string);
}
exports.base64StringToBlob = base64StringToBlob;

function blobToMarkedBase64String(blob) {
    return "64'" + blobToBase64String(blob) + "'";
}
exports.blobToMarkedBase64String = blobToMarkedBase64String;

/*
function blobToQuotedMarkedBase64String(blob) {
    // Mimics having 64'xxx' as a literal and then SQL-quote-escaping it as
    // '64''xxx'''
    return "'64''" + blobToBase64String(blob) + "'''";
    // Removed 2014-08-02; was always a design flaw (possible for strings
    // to look like this in principle).
}
exports.blobToQuotedMarkedBase64String = blobToQuotedMarkedBase64String;
*/

function markedBase64StringToBlob(base64enc) {
    return base64StringToBlob(base64enc.substr(3, base64enc.length - 4));
}
exports.markedBase64StringToBlob = markedBase64StringToBlob;

function blobToPngUrl(blob) {
    return BASE64_PNG_URL_PREFIX + Titanium.Utils.base64encode(blob);
    // doesn't need anything else in this context
}
exports.blobToPngUrl = blobToPngUrl;

function pngUrlToBlob(url) {
    var string = url.substr(BASE64_PNG_URL_PREFIX.length);
    return base64StringToBlob(string);
}
exports.pngUrlToBlob = pngUrlToBlob;

//=============================================================================
// Hex encoding
//=============================================================================

function padHexTwo(input) {
    return (input.length === 1) ? ('0' + input) : input;
    // Nasty! Based on http://stackoverflow.com/questions/5786483/
}
exports.padHexTwo = padHexTwo;

function blobToHexEncoded(blob) {
    // blob to buffer, because buffers are easy to access bytes within
    // var blobStream = Titanium.Stream.createStream({
    //      source: blob, mode: Titanium.Stream.MODE_READ });
    // var newBuffer = Titanium.createBuffer({ length: blob.length });
    // var bytes = blobStream.read(newBuffer);
    // Could use a codec to translate it as it goes into the buffer - but
    // Titanium.Codec doesn't include a hex-encoding codec!

    // Not sure we can random-access a buffer either!
    var blobstring,
        result,
        i;
    if (!blob) {
        return null;
    }
    blobstring = blob.toString();
    result = "X'";
    for (i = 0; i < blobstring.length; ++i) {
        result += padHexTwo(blobstring.charCodeAt(i).toString(16));
    }
    return result + "'";
}
exports.blobToHexEncoded = blobToHexEncoded;

function hexEncodedToBlob(hexstring) {
    var result = "",
        pair,
        i,
        buffer;
    if (!hexstring ||
            hexstring.length < 5 || // X'00'
            hexstring.substr(0, 2) !== "X'" ||
            hexstring.substr(hexstring.length - 1, 1) !== "'") {
        return null;
    }
    for (i = 2; i < hexstring.length - 2; i += 2) {
        // Skip the leading X', and the trailing second-half of the number and
        // the trailing '
        pair = hexstring.substr(i, 2);
        result += String.fromCharCode(parseInt(pair, 16));
    }
    buffer = Titanium.createBuffer({ value: result });
    // ... *** in hexEncodedToBlob: needs checking
    return buffer.toBlob();
}
exports.hexEncodedToBlob = hexEncodedToBlob;

//=============================================================================
// Blobs
//=============================================================================

// Titanium's documentation and/or conversion functions are rubbish.
// Blobs encode their type (e.g. image, text, any old thing) inside them, and
// their conversion
// functions give different results (or crash) depending on the internal type.
// Crazy.
// So, for example, if you load an image from a file, then
// Titanium.Utils.base64encode(blob) works fine and gives a string.
// But if you read an image using webview.toImage(), then the same call crashes
// with "Uncaught Error: Invalid type for argument."

// Titanium BUG:
// http://developer.appcelerator.com/question/119320/using-toimage-on-a-view-crashes-in-android-sdk-161-and-162
function imageBlobFromView(view) {
    var image = view.toImage(); // THE DOCUMENTATION SAYS IT'S A BLOB.
    // BUT IT'S NOT. See TiUIHelper.java / createDictForImage,
    // called by TiUIHelper.java / viewToImage.
    // Ah, somebody else traced it too:
    // http://developer.appcelerator.com/question/119320/using-toimage-on-a-view-crashes-in-android-sdk-161-and-162
    if (android) {
        return image.media; // this is the blob!
    }
    return image; // this is what the documentation says is a blob
}
exports.imageBlobFromView = imageBlobFromView;

function blobToString(blob) {
    return blob.toString();
}
exports.blobToString = blobToString;

function decodeBlob(encoding, code) {
    switch (encoding) {
    case ENCODING_PNGURL:
        return pngUrlToBlob(code);
    default:
        return pngUrlToBlob(code);
    }
}
exports.decodeBlob = decodeBlob;

function encodeBlob(encoding, blob) {
    switch (encoding) {
    case ENCODING_PNGURL:
        return blobToPngUrl(blob);
    default:
        return blobToPngUrl(blob);
    }
}
exports.encodeBlob = encodeBlob;

//=============================================================================
// Boolean from string
//=============================================================================

// for use with webview's evalJS...
function boolFromString(string) {
    return (string === "true");
}
exports.boolFromString = boolFromString;

//=============================================================================
// Moments, Dates
//=============================================================================

function momentToString(m) {
    // Function must be identical in conversion.js and taskhtmlcommon.jsx
    return m.format(DETAILED_DATETIME_FORMAT);
    // We leave it in this format, which preserves local timezone information.
    // If a UTC copy is needed: var utcmoment = moment.utc(m);
}
exports.momentToString = momentToString;

function momentToDateOnlyString(m) {
    return m.format(DATE_ONLY_FORMAT);
}
exports.momentToDateOnlyString = momentToDateOnlyString;

function stringToMoment(s) {
    return moment(s);
}
exports.stringToMoment = stringToMoment;

function momentToDateStrippingTimezone(momentvalue) {
    var datevalue = momentvalue.toDate();
    return datevalue;
}
exports.momentToDateStrippingTimezone = momentToDateStrippingTimezone;

function dateToMomentAddingCurrentTimezone(datevalue) {
    var momentvalue = moment(datevalue);
    return momentvalue;
}
exports.dateToMomentAddingCurrentTimezone = dateToMomentAddingCurrentTimezone;

//=============================================================================
// JSON serialization
//=============================================================================

//-----------------------------------------------------------------------------
// moment
//-----------------------------------------------------------------------------

function json_freeze_moment(m) {
    // Function must be identical in conversion.js and taskhtmlcommon.jsx
    return {
        _class: "moment",
        value: momentToString(m)
    };
}
exports.json_freeze_moment = json_freeze_moment;

function json_thaw_moment(jsonobject) {
    return stringToMoment(jsonobject.value);
}
exports.json_thaw_moment = json_thaw_moment;

function preprocess_moments_for_json_stringify(obj) {
    // Function must be identical in conversion.js and taskhtmlcommon.jsx
    if (obj === null || typeof obj !== "object") {
        return obj;
    }
    var copy = {}, // obj.constructor() crashes
        attr;
    for (attr in obj) {
        if (obj.hasOwnProperty(attr)) {
            if (moment.isMoment(obj[attr])) {
                copy[attr] = json_freeze_moment(obj[attr]);
            } else {
                copy[attr] = obj[attr];
            }
        }
    }
    return copy;
}

//-----------------------------------------------------------------------------
// blob
//-----------------------------------------------------------------------------

function json_freeze_blob(b) {
    return {
        _class: "blob",
        value: encodeBlob(ENCODING_PNGURL, b)
    };
}
exports.json_freeze_blob = json_freeze_blob;

function json_freeze_pngurl_as_blob(x) {
    return {
        _class: "blob",
        value: x
    };
}

function json_thaw_blob(jsonobject) {
    return decodeBlob(ENCODING_PNGURL, jsonobject.value);
}
exports.json_thaw_blob = json_thaw_blob;

//-----------------------------------------------------------------------------
// general
//-----------------------------------------------------------------------------

/*jslint unparam: true */
function json_encoder_replacer(key, value) {
    // Encode to JSON (e.g. performed by webviews)

    // The cut-down version in taskhtmlcommon.jsx must operate identically (in
    // what it does).

    // MOMENT DETECTION NO LONGER WORKS, because the moment library
    // preprocesses them first via its toJSON method (discovered 2015-01-30).
    // http://momentjs.com/docs/#/displaying/as-json/
    // THEREFORE, USE preprocess_moments_for_json_stringify() first.

    // Detect a blob (typeof x will be "object")
    if (value !== null &&
            typeof value === "object" &&
            value._type === "blob") {
        // home-grown way to recognize a blob...
        // trying to use x.applyProperties({_type: "blob"}) in Titanium SDK
        // 3.0, but it's not working
        // ... get "Unable to lookup Proxy.prototype.getProperty" errors
        // ... so use json_freeze_blob() by hand instead
        return json_freeze_blob(value);
    }
    return value;
}
/*jslint unparam: false */
exports.json_encoder_replacer = json_encoder_replacer;

/*jslint unparam: true */
function json_decoder_reviver(key, value) {
    // Reverses the encoding used by the webview: see taskcommonhtml.js
    if (value !== null &&
            typeof value === "object" &&
            value._class !== undefined) {
        if (value._class === "moment") { // duck typing!
            // the value can look like an object: {...}
            // and when you print it directly its value is [object Object]
            // but (value instanceof Object) can be false... ??
            // http://javascriptweblog.wordpress.com/2011/08/08/fixing-the-javascript-typeof-operator/
            // https://developer.mozilla.org/en-US/docs/JavaScript/Reference/Operators/instanceof
            // is it because you need "new" for that to work? no...
            // different context?
            // ... let's try duck typing
            return json_thaw_moment(value);
        }
        if (value._class === "blob") {
            return json_thaw_blob(value);
        }
    }
    return value;
}
/*jslint unparam: false */
exports.json_decoder_reviver = json_decoder_reviver;

function json_encode(thing) {
    return JSON.stringify(thing, json_encoder_replacer);
}
exports.json_encode = json_encode;

function json_encode_single_blob(thing) {
    return JSON.stringify(json_freeze_blob(thing));
}
exports.json_encode_single_blob = json_encode_single_blob;

function json_encode_single_pngurl_as_blob(thing) {
    return JSON.stringify(json_freeze_pngurl_as_blob(thing));
}
exports.json_encode_single_pngurl_as_blob = json_encode_single_pngurl_as_blob;

function json_decode(thing) {
    return JSON.parse(thing, json_decoder_reviver);
}
exports.json_decode = json_decode;

//=============================================================================
// Character set encoding
//=============================================================================

var unicode_to_ascii_map = {
    "ä": "a",
    "ö": "o",
    "ü": "u",
    "Ä": "A",
    "Ö": "O",
    "Ü": "U",
    "á": "a",
    "à": "a",
    "â": "a",
    "é": "e",
    "è": "e",
    "ê": "e",
    "ú": "u",
    "ù": "u",
    "û": "u",
    "ó": "o",
    "ò": "o",
    "ô": "o",
    "Á": "A",
    "À": "A",
    "Â": "A",
    "É": "E",
    "È": "E",
    "Ê": "E",
    "Ú": "U",
    "Ù": "U",
    "Û": "U",
    "Ó": "O",
    "Ò": "O",
    "Ô": "O",
    "ß": "s",
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    "×": "*",
    "•": "(*)",
    "≤": "<=",
    "≥": ">=",
    "≠": "!=",
};

/*
var unicode_chars = "";
for (uc in unicode_to_ascii_map) {
    unicode_chars += uc;
}
var unicode_to_ascii_regexp = RegExp(unicode_chars, "g");
Titanium.API.trace("transliterateUtf8toAscii: unicode_chars = " +
                   unicode_chars);
Titanium.API.trace("transliterateUtf8toAscii: unicode_to_ascii_regexp = " +
                   unicode_to_ascii_regexp);
*/

function letterTranslator(match) {
    var replacement = unicode_to_ascii_map[match] || match;
    return replacement;
}

function transliterateUtf8toAscii(ustring) {
    // FAILS IN TITANIUM:
    // return ustring.replace(unicode_to_ascii_regexp, letterTranslator);
    var result = "",
        i;
    // http://stackoverflow.com/questions/135448/
    for (i = 0; i < ustring.length; ++i) {
        result += letterTranslator(ustring.charAt(i));
    }
    return result;
}
exports.transliterateUtf8toAscii = transliterateUtf8toAscii;

/*
teststring = "abc á     ‘ ’ “ ” – — × • ≤ ≥ ≠ xyz";
Titanium.API.trace("transliterateUtf8toAscii: from = " + teststring);
Titanium.API.trace("transliterateUtf8toAscii: to   = " +
                   transliterateUtf8toAscii(teststring));
*/

//=============================================================================
// CSV, comma-separated SQL values, and other decoding/encoding
//=============================================================================
var REGEX_WHITESPACE = /\s/g;
var REGEX_BLOB_HEX = /^X'([a-fA-F0-9][a-fA-F0-9])+'$/;
var REGEX_BLOB_BASE64 = /^64'(?:[A-Za-z0-9+\/]{4})*(?:[A-Za-z0-9+\/]{2}[AEIMQUYcgkosw048]=|[A-Za-z0-9+\/][AQgw]==)?'$/;
var SQLSEP = ",";
var SQLQUOTE = "'";

function sql_dequote_string(s) {
    if (s.length < 2) {
        // Something wrong.
        return s;
    }
    s = s.substr(1, s.length - 2); // chop off surrounding quotes
    return s.replace(/''/g, "'");  // replace '' with '
}

function unescape_newlines(s) {
    // See escape_newlines() and unescape_newlines() in database.py
    var d = "",  // the destination string
        in_escape = false,
        i,
        c;
    if (!s) {
        return s;
    }
    for (i = 0; i < s.length; ++i) {
        c = s[i];
        if (in_escape) {
            if (c === "r") {
                d += "\r";
            } else if (c === "n") {
                d += "\n";
            } else {
                d += c;
            }
            in_escape = false;
        } else {
            if (c === "\\") {
                in_escape = true;
            } else {
                d += c;
            }
        }
    }
    return d;
}

function decode_single_sql_literal(v) {
    // Takes a string representing an SQL value. Returns the value.
    // See encode_single_value(), decode_single_value() in database.py

    var lang = require('lib/lang'),
        t;

    if (!v) {
        return null;
    }
    if (v.toUpperCase() === "NULL") {
        return null;
    }

    // BLOB?
    t = v.replace(REGEX_WHITESPACE, "");
    if (REGEX_BLOB_HEX.test(t)) {
        return hexEncodedToBlob(t);
    }
    if (REGEX_BLOB_BASE64.test(t)) {
        return markedBase64StringToBlob(t);
    }

    if (v.length >= 2 && v[0] === SQLQUOTE && v[v.length - 1] === SQLQUOTE) {
        // Quoted string
        return sql_dequote_string(unescape_newlines(v));
    }

    if (lang.isNumber(v)) {
        // Number
        return parseFloat(v);  // copes with integer and float
    }

    // Something odd... Allow it as a string.
    Titanium.API.warn("decode_single_sql_literal: something odd");
    return v;
}

function CSVSQLtoArray(s) {
    // Equivalent, broadly speaking, to gen_items_from_sql_csv() in database.py
    // Titanium.API.trace("CSVSQLtoArray: s = " + s);
    if (!s) {
        return [];
    }
    var n = s.length,
        results = [],
        startpos = 0,
        pos = 0,
        in_quotes = false,
        chunk;
    while (pos < n) {
        if (!in_quotes) {
            if (s[pos] === SQLSEP) {
                // end of chunk
                chunk = s.substr(startpos, pos - startpos).trim();
                // ... substr will not include s[pos]
                startpos = pos + 1;

                // ------------------------------------------------------------
                // SQL literal processing here: more memory-efficient to
                // process result immediately rather than store an array of
                // intermediate chunks
                // ------------------------------------------------------------

                results.push(decode_single_sql_literal(chunk));
            } else if (s[pos] === SQLQUOTE) {
                // start of quote
                in_quotes = true;
            }
        } else {
            if (pos < n - 1 && s[pos] === SQLQUOTE &&
                    s[pos + 1] === SQLQUOTE) {
                // double quote, '', is an escaped quote, not end of quote
                pos += 1;  // skip one more than we otherwise would
            } else if (s[pos] === SQLQUOTE) {
                // end of quote
                in_quotes = false;
            }
        }
        pos += 1;
    }
    // Last chunk
    chunk = s.substr(startpos, s.length - startpos).trim();
    // ------------------------------------------------------------------------
    // More SQL literal processing here
    // ------------------------------------------------------------------------
    results.push(decode_single_sql_literal(chunk));
    // Titanium.API.trace("CSVSQLtoArray: results = " + JSON.stringify(results));
    return results;
}
exports.CSVSQLtoArray = CSVSQLtoArray;


/*

teststring = (
    "one, two, 3, 4.5, NULL, 'hello \"hi\\nwith linebreak\" slash \\', "
    + "'NULL', 'quote''s here', "
    + "X'012345', 64'aGVsbG8=', "
    + "'X''012345'', '64''aGVsbG8=''"
);
CSVSQLtoArray(teststring);

*/
