// dbcore.js

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

/*jslint node: true, plusplus: true */
"use strict";


// http://blog.stevenlevithan.com/archives/javascript-roman-numeral-converter

function romanize(num) {
    var lookup = {M: 1000, CM: 900, D: 500, CD: 400, C: 100, XC: 90, L: 50,
                  XL: 40, X: 10, IX: 9, V: 5, IV: 4, I: 1},
        roman = '',
        i;
    for (i in lookup) {
        if (lookup.hasOwnProperty(i)) {
            while (num >= lookup[i]) {
                roman += i;
                num -= lookup[i];
            }
        }
    }
    return roman;
}
exports.romanize = romanize;

function deromanize(roman) {
    var lookup = {I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000},
        arabic = 0,
        i = roman.length;
    roman = roman.toUpperCase();
    while (i--) {
        if (lookup[roman[i]] < lookup[roman[i + 1]]) {
            arabic -= lookup[roman[i]];
        } else {
            arabic += lookup[roman[i]];
        }
    }
    return arabic;
}
exports.deromanize = deromanize;
