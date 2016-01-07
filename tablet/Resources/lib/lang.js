// lang.js

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

/*jslint node: true, plusplus: true */
"use strict";

//=====================================================================
// undefined, null, default values
//=====================================================================
// Note that these fail in e.g. Chrome, doing isDefined(Titanium) --
// throws ReferenceError / undefined

/*
function valueOrDefault(value, defaultValue) {
    return (typeof value === "undefined") ? defaultValue : value;
}
exports.valueOrDefault = valueOrDefault;

function isUndefined(value) {
    return (typeof value === "undefined");
}
exports.isUndefined = isUndefined;

function isDefined(value) {
    return (typeof value !== "undefined");
}
exports.isDefined = isDefined;
*/

// http://stackoverflow.com/questions/27509/
// http://weblogs.asp.net/bleroy/archive/2005/02/15/Three-common-mistakes-in-JavaScript-_2F00_-EcmaScript.aspx

//=============================================================================
// Properties
//=============================================================================

function copyProperties(from, to) {
    var prop;
    for (prop in from) {
        if (from.hasOwnProperty(prop)) {
            to[prop] = from[prop];
        }
    }
    // If the prototype could have been fiddled with, an extra check may be
    // needed:
    // http://stackoverflow.com/questions/587881/
    // http://stackoverflow.com/questions/85992/
}
exports.copyProperties = copyProperties;

function copyProperty(from, to, srcpropname, destpropname) {
    if (destpropname === undefined) {
        destpropname = srcpropname;
    }
    // http://stackoverflow.com/questions/135448/
    if (from.hasOwnProperty(srcpropname)) {
        to[destpropname] = from[srcpropname];
    }
}
exports.copyProperty = copyProperty;

//=============================================================================
// Inheritance
//=============================================================================

function inheritPrototype(childObject, parentObject) {
    // http://javascriptissexy.com/oop-in-javascript-what-you-need-to-know/
    // As discussed above, we use the Crockford’s method to copy the properties
    // and methods from the parentObject onto the childObject
    // So the copyOfParent object now has everything the parentObject has
    var copyOfParent = Object.create(parentObject.prototype);

    // Then we set the constructor of this new object to point to the
    // childObject. This step is necessary because the preceding step overwrote
    // the childObject constructor when it overwrote the childObject prototype
    // (during the Object.create() process)
    copyOfParent.constructor = childObject;

    // Then we set the childObject prototype to copyOfParent, so that the
    // childObject can in turn inherit everything from copyOfParent (from
    // parentObject)
    childObject.prototype = copyOfParent;
}
exports.inheritPrototype = inheritPrototype;

function extendPrototype(destObject, srcObject) {
    var prop;
    for (prop in srcObject) {
        if (srcObject.hasOwnProperty(prop)) {
            // http://stackoverflow.com/questions/921789/
            destObject.prototype[prop] = srcObject[prop];
        }
    }
}
exports.extendPrototype = extendPrototype;

//=============================================================================
// Array manipulation
//=============================================================================

/*
function deleteArrayElement(array, index) {
    if (index < 0 || index >= array.length) return;
    array.splice(index, 1);
}
exports.deleteArrayElement = deleteArrayElement;
*/

function appendArray(a, b) {
    // http://stackoverflow.com/questions/1374126/
    a.push.apply(a, b);
}
exports.appendArray = appendArray;

function removeFromArrayByValue(array, value) {
    var index,
        done = false;
    while (!done) {
        index = array.indexOf(value);
        if (index === -1) {
            done = true;
        } else {
            array.splice(index, 1);
        }
    }
}
exports.removeFromArrayByValue = removeFromArrayByValue;

function arrayGetIndexByValue(array, value) {
    var i;
    for (i = 0; i < array.length; ++i) {
        if (array[i] === value) {
            return i;
        }
    }
    return null;
}
exports.arrayGetIndexByValue = arrayGetIndexByValue;

function arrayGetValueOrDefault(array, index, defaultValue) {
    if (defaultValue === undefined) {
        defaultValue = null;
    }
    if (index === undefined || index === null ||
            index < 0 || index >= array.length) {
        return defaultValue;
    }
    return array[index];
}
exports.arrayGetValueOrDefault = arrayGetValueOrDefault;

function removeSecondArrayContentsFromFirstArray(array1, array2) {
    var i;
    for (i = 0; i < array2.length; ++i) {
        removeFromArrayByValue(array1, array2[i]);
    }
}
exports.removeSecondArrayContentsFromFirstArray = removeSecondArrayContentsFromFirstArray;

// Intersection: http://stackoverflow.com/questions/1885557/

/* destructively finds the intersection of
 * two arrays in a simple fashion.
 *
 * PARAMS
 *  a - first array, must already be sorted
 *  b - second array, must already be sorted
 *
 * NOTES
 *  State of input arrays is undefined when
 *  the function returns.  They should be
 *  (prolly) be dumped.
 *
 *  Should have O(n) operations, where n is
 *    n = MIN(a.length, b.length)
 */
function intersect_destructive(a, b) {
    var result = [];
    while (a.length > 0 && b.length > 0) {
        if (a[0] < b[0]) {
            a.shift();
        } else if (a[0] > b[0]) {
            b.shift();
        } else {
            /* they're equal */
            result.push(a.shift());
            b.shift();
        }
    }
    return result;
}
exports.intersect_destructive = intersect_destructive;

/* finds the intersection of
 * two arrays in a simple fashion.
 *
 * PARAMS
 *  a - first array, must already be sorted
 *  b - second array, must already be sorted
 *
 * NOTES
 *
 *  Should have O(n) operations, where n is
 *    n = MIN(a.length(), b.length())
 */
function intersect_safe(a, b) {
    var ai = 0,
        bi = 0,
        result = [];
    while (ai < a.length && bi < b.length) {
        if (a[ai] < b[bi]) {
            ai++;
        } else if (a[ai] > b[bi]) {
            bi++;
        } else {
            /* they're equal */
            result.push(a[ai]);
            ai++;
            bi++;
        }
    }
    return result;
}
exports.intersect_safe = intersect_safe;

//=============================================================================
// Key-value pairs (using KeyValuePair objects)
//=============================================================================

function kvpGetValue(kvparray, key) {
    var i;
    for (i = 0; i < kvparray.length; ++i) {
        if (kvparray[i].key === key) {
            return kvparray[i].value;
        }
    }
    return null;
}
exports.kvpGetValue = kvpGetValue;

function kvpGetIndexByValue(kvparray, value) {
    var i;
    for (i = 0; i < kvparray.length; ++i) {
        if (kvparray[i].value === value) {
            return i;
        }
    }
    return null;
}
exports.kvpGetIndexByValue = kvpGetIndexByValue;

function kvpGetKeyByValue(kvparray, value) {
    var i;
    for (i = 0; i < kvparray.length; ++i) {
        if (kvparray[i].value === value) {
            // will be happy with "0 == false" (true) and "1 == true" (true),
            // so yes/no booleans can be specified validly with 0/1
            return kvparray[i].key;
        }
    }
    return null;
}
exports.kvpGetKeyByValue = kvpGetKeyByValue;

function kvpRemoveByKey(kvparray, key) {
    var i;
    for (i = kvparray.length - 1; i >= 0; --i) { // count down for deletion
        if (kvparray[i].key === key) {
            kvparray.splice(i, 1);
        }
    }
}
exports.kvpRemoveByKey = kvpRemoveByKey;

//=============================================================================
// Randomization
//=============================================================================

function randomFloatBetween(x, y) {
    return Math.random() * (y - x) + x; // Math.random() is 0-1
}
exports.randomFloatBetween = randomFloatBetween;

// http://stackoverflow.com/questions/2450954/how-to-randomize-a-javascript-array
// http://javascript.about.com/library/blshuffle.htm
// http://stackoverflow.com/questions/9391718/javascript-integer-division-or-is-math-floorx-equivalent-to-x-0-for-x-0
// http://www.codinghorror.com/blog/2007/12/the-danger-of-naivete.html
// http://en.wikipedia.org/wiki/Knuth_shuffle
function shuffle(array) { // in-place shuffle
    // Array of size n indexed from 0 to n-1.
    /*jslint bitwise: true */
    var i,
        j,
        temp;
    for (i = array.length - 1; i > 0; i--) { // For n-1 to 1 inclusive.
        // j is a random integer where 0 <= j <= i
        j = Math.random() * (i + 1) | 0;
        // Math.random() returns a random number between 0 and 1.
        // The "| 0" performs a floor operation.
        // Swap array[i] and array[j]:
        temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
}
exports.shuffle = shuffle;

//=============================================================================
// Maps
//=============================================================================

function reverseArbitraryMap(map) {
    // Avoid this: for an ordered array, use reverseDenseMap().
    // Otherwise key 0 becomes "0", etc.
    var revmap = [],
        key;
    for (key in map) {
        if (map.hasOwnProperty(key)) {  // for JSLint
            revmap[map[key]] = key;
        }
    }
    return revmap;
}
exports.reverseArbitraryMap = reverseArbitraryMap;

function reverseDenseMap(map) {
    // Creating an array of a predefined size: fiddly in Javascript.
    // Can use "new Array(length)", but it appears to be somewhat deprecated.
    // See also http://blog.caplin.com/2012/01/13/javascript-is-hard-part-1-you-cant-trust-arrays/
    // USE map_two = map_one.slice(0) TO COPY, NOT THIS; --- map_two = map_one;
    // But we don't need to do anything. We can use indexes that are
    // "out of bounds" and it'll be happy.
    var revmap = [],
        i;
    for (i = 0; i < map.length; ++i) {
        revmap[map[i]] = i;
    }
    return revmap;
}
exports.reverseDenseMap = reverseDenseMap;

function createBidirectionalSequenceMaps(length, randomize) {
    // Creates a mapping, optionally randomized, and its inverse mapping.
    // Suppose the first is      4 1 3 0 2 e.g. map_one[0] = 4
    // Then the second should be 3 1 4 2 0 e.g. map_two[4] = 0
    var map_one = [],
        map_two,
        i;
    for (i = 0; i < length; ++i) {
        map_one.push(i);
    }
    if (randomize) {
        shuffle(map_one);
    }
    map_two = reverseDenseMap(map_one);
    return {
        map_original_to_view: map_one,
        map_view_to_original: map_two
    };
}
exports.createBidirectionalSequenceMaps = createBidirectionalSequenceMaps;

//=============================================================================
// Validation
//=============================================================================

// Number validation: http://stackoverflow.com/questions/18082/
// Unit extraction:
// http://upshots.org/javascript/javascript-get-current-style-as-any-unit
function isNumber(n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
}
exports.isNumber = isNumber;

//=============================================================================
// Titanium units manipulation
//=============================================================================

function getUnitsOrNull(x) {
    /*jslint regexp: true */
    return isNumber(x) ? null : x.match(/[^0-9.]+$/)[0].trim();
    // A clump of things at the end of the line that don't match 0-9 or .
    // -- see http://www.javascriptkit.com/javatutors/redev2.shtml
    // Match returns an array (or null), not a string.
}

function addUnits(a, b) {
    var answer,
        units_a = getUnitsOrNull(a),
        units_b = getUnitsOrNull(b);
    if (units_a === null && units_b === null) {
        answer = a + b;
    } else {
        if (units_a !== units_b) {
            throw new Error("addUnits: mismatched units, a=" + a + ", b=" + b);
        }
        answer = (parseFloat(a) + parseFloat(b)) + units_a;
    }
    return answer;
}
exports.addUnits = addUnits;

function subtractUnits(a, b) {
    var answer,
        units_a = getUnitsOrNull(a),
        units_b = getUnitsOrNull(b);
    if (units_a === null && units_b === null) {
        answer = a - b;
    } else {
        if (units_a !== units_b) {
            throw new Error("subtractUnits: mismatched units, a=" + a +
                            ", b=" + b);
        }
        answer = (parseFloat(a) - parseFloat(b)) + units_a;
    }
    return answer;
}
exports.subtractUnits = subtractUnits;

function multiplyUnits(a, b) {
    var answer,
        units_a = getUnitsOrNull(a),
        units_b = getUnitsOrNull(b),
        final_units;
    if (units_a === null && units_b === null) {
        answer = a * b;
    } else {
        if (units_a !== null && units_b !== null) {
            throw new Error("multiplyUnits: mismatched units, a=" + a +
                            ", b=" + b);
        }
        final_units = (units_a !== null) ? units_a : units_b;
        answer = (parseFloat(a) * parseFloat(b)) + final_units;
    }
    return answer;
}
exports.multiplyUnits = multiplyUnits;

function divideUnits(a, b) {
    var answer,
        units_a = getUnitsOrNull(a),
        units_b = getUnitsOrNull(b),
        final_units;
    if (units_a === null && units_b === null) {
        answer = a / b;
    } else {
        if (units_a !== null && units_b !== null) {
            throw new Error("divideUnits: mismatched units, a=" + a +
                            ", b=" + b);
        }
        final_units = (units_a !== null) ? units_a : units_b;
        answer = (parseFloat(a) / parseFloat(b)) + final_units;
    }
    return answer;
}
exports.divideUnits = divideUnits;

function zeroInUnits(x) {
    var units = getUnitsOrNull(x);
    if (units === null) {
        return 0;
    }
    return '0' + units;
}
exports.zeroInUnits = zeroInUnits;

//=============================================================================
// String manipulation
//=============================================================================

function upperCase(string) {
    if (!string) {
        return "";
    }
    return string.toUpperCase();
}
exports.upperCase = upperCase;

//=============================================================================
// Regular expressions
//=============================================================================

function getFirstRegexMatch(string, regex) {
    var result = regex.exec(string);
    if (result === null) {
        return null;
    }
    // result[0] is the whole match
    // result[1], result[2], ... are the bits matching parenthesized bits
    return result[1];
}
exports.getFirstRegexMatch = getFirstRegexMatch;

function getFirstRegexMatchAsInt(string, regex) {
    var result = getFirstRegexMatch(string, regex);
    if (result === null || !isNumber(result)) {
        return null;
    }
    return parseInt(result, 10); // base 10
}
exports.getFirstRegexMatchAsInt = getFirstRegexMatchAsInt;

function getFirstRegexStringMatch(string, regexstring, modifier) {
    var regex = new RegExp(regexstring, modifier);
    return getFirstRegexMatch(string, regex);
}
exports.getFirstRegexStringMatch = getFirstRegexStringMatch;

//=============================================================================
// Maths
//=============================================================================

function mean() {
    // call either as:
    //       mean( A, B, C );
    // or with a single argument:
    //       mean( [ A, B, C] );
    var total = 0.0,
        n = 0,
        i,
        list,
        firstindex = 0;
    if (arguments.length === 1) {
        // single argument: treat it as a list and take the mean of the list
        // members
        list = arguments[firstindex]; // for JSLint
        for (i = 0; i < list.length; ++i) {
            if (list[i] !== null && !isNaN(list[i])) {
                // isNaN(undefined) is true; isNaN(null) is false.
                total += list[i];
                n += 1;
            }
        }
    } else {
        // multiple arguments: take the mean of them
        for (i = 0; i < arguments.length; ++i) {
            if (arguments[i] !== null && !isNaN(arguments[i])) {
                // isNaN(undefined) is true; isNaN(null) is false.
                total += arguments[i];
                n += 1;
            }
        }
    }
    if (n === 0) {
        return null;
    }
    return total / n;
}
exports.mean = mean;

function toFixedOrNull(number, dp) {
    if (number === undefined || number === null || isNaN(number)) {
        return null;
    }
    return number.toFixed(dp);
}
exports.toFixedOrNull = toFixedOrNull;

function div(a, b) {
    // http://stackoverflow.com/questions/4228356/integer-division-in-javascript
    // return ~~(a / b);
    return Math.floor(a / b);
}
exports.div = div;

//=============================================================================
// Logic
//=============================================================================

function falseNotNull(x) {
    if (x === undefined || x === null) {
        return false;
    }
    return x ? false : true;
}
exports.falseNotNull = falseNotNull;
