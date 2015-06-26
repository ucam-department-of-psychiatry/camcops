// debugger.js

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
/*global Titanium */

var nl = "\n",
    spaces = "  ";

function dumpLayoutTreePositions(view, depth) {
    var i,
        d = view.getSize();
    if (depth === undefined) {
        depth = 0;
    }
    Titanium.API.trace("Object at depth " + depth + ": " + nl);
    Titanium.API.trace(spaces + "x: " + d.x + ", y: " + d.y +
                       ", height: " + d.height + ", width: " + d.width + nl);
    for (i = 0; i < view.children.length; ++i) {
        dumpLayoutTreePositions(view.children[i], depth + 1);
    }
}
exports.dumpLayoutTreePositions = dumpLayoutTreePositions;

function traceTiming(text) {
    var moment = require('lib/moment'),
        conversion = require('lib/conversion');
    Titanium.API.trace(text + ": " + conversion.momentToString(moment()));
}
exports.traceTiming = traceTiming;

function dumpRecurse(object, name, depth, params) {
    var dump = "",
        type = typeof object,
        i,
        prop;

    if (params.maxDepth > 0 && depth > params.maxDepth) {
        return null;
    }
    if (params.lineLimit > 0 && params.linesSoFar > params.lineLimit) {
        Titanium.API.trace("dumpRecurse(): line limit of " + params.lineLimit +
                           " reached, stopping");
        return null;
    }
    params.linesSoFar += 1;
    if (params.showLevelNotDots) {
        dump += "[level " + depth + "]";
    } else {
        for (i = 0; i < depth; ++i) {
            dump += "... ";
        }
    }

    switch (type) {
    case "string":
    case "number":
    case "boolean":
    case "function":
        dump += name + " [" + type + "]: " + object + "\n";
        break;
    case "undefined":
    case "null":
        dump += name + " [" + type + "]\n";
        break;
    case "object":
        dump += name + " [" + type + "]: " + object + "\n";
        // ... usually prints the object's type
        if (params.traceNotReturnString) {
            Titanium.API.trace(dump);
        }
        for (prop in object) {
            if (object.hasOwnProperty(prop)) {
                if (params.traceNotReturnString) {
                    dumpRecurse(object[prop], prop, depth + 1, params);
                } else {
                    dump += dumpRecurse(object[prop], prop, depth + 1, params);
                }
            }
        }
        if (params.traceNotReturnString) {
            return null;
        }
        break;
    default:
        dump += name + " [" + type + "]\n";
        break;
    }
    if (params.traceNotReturnString) {
        Titanium.API.trace(dump);
        return null;
    }
    return dump;
}

function dumpObject(object, params) {
    if (params === undefined) {
        params = {};
    }
    if (params.traceNotReturnString === undefined) {
        params.traceNotReturnString = true;
    }
    if (params.lineLimit === undefined) {
        params.lineLimit = 200;
    }
    if (params.maxDepth === undefined) {
        params.maxDepth = 0;
    }
    if (params.showLevelNotDots === undefined) {
        params.showLevelNotDots = false;
    }
    params.linesSoFar = 0;
    if (params.traceNotReturnString) {
        dumpRecurse(object, "(objectroot)", 0, params);
        return null;
    }
    return dumpRecurse(object, "(objectroot)", 0, params);
}
exports.dumpObject = dumpObject;
