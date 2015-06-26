// taskhtmlcommon.jsx
// Note: this is for inclusion into HTML, and is NOT a CommonJS module.

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

// Loading Javascript programmatically: http://stackoverflow.com/questions/11509686/javascript-src-loading-order
// However, typically useless since we would like to use Raphael elements before the onload() function is called.

/*jslint node: true, plusplus: true, nomen: true */
"use strict";
/*global Titanium */
/*global moment */
/*global TASKNAME, EVENTNAME_IN, EVENTNAME_OUT, startTask, incomingEvent */

var inTitanium = (this.Titanium !== undefined),
    NOT_IN_TITANIUM_MSG = "call not permitted; not in Titanium environment",
    windowInitialized = false,
    RADPERDEG = Math.PI / 180, // radians per degree
    TASKNAME = "",
    EVENTNAME_IN,
    EVENTNAME_OUT,
    startTask,
    incomingEvent;

//=============================================================================
// registerWebviewTask
//=============================================================================

function registerWebviewTask(taskname, eventname_in, eventname_out,
                             startTaskFn, incomingEventFn) {
    TASKNAME = taskname;
    EVENTNAME_IN = eventname_in;
    EVENTNAME_OUT = eventname_out;
    startTask = startTaskFn;
    incomingEvent = incomingEventFn;
}

//=============================================================================
// trace
//=============================================================================

function trace(msg) {
    var prefix = TASKNAME || "WEBVIEW";
    if (inTitanium) {
        Titanium.API.debug(prefix + ": " + msg);
    } else {
        console.log(msg); // for web browser debugging
    }
}

//=============================================================================
// Language
//=============================================================================

function assert(test, message) {
    // Don't use "throw" in plain webview code; its results are invisible.
    // Use assert(false, msg) instead; it will then trace() before stopping.
    if (!test) {
        trace(message);
        trace("+++ STOPPING +++");
        throw new Error(message);
    }
}

function copyProperties(from, to) {
    var prop;
    for (prop in from) {
        if (from.hasOwnProperty(prop)) {
            to[prop] = from[prop];
        }
    }
}

function copyProperty(from, to, prop) {
    to[prop] = from[prop];
}

function deleteNullPropertiesRecursively(obj) {
    var prop;
    for (prop in obj) {
        if (obj.hasOwnProperty(prop)) {
            if (obj[prop] === null) {
                delete obj[prop];
            } else if (obj[prop] instanceof Object) {
                deleteNullPropertiesRecursively(obj[prop]);
            }
        }
    }
}

//=============================================================================
// Arrays
//=============================================================================

function appendArray(a, b) {
    a.push.apply(a, b);
}

/*jslint bitwise: true */
function shuffle(array) {
    var i,
        j,
        temp;
    for (i = array.length - 1; i > 0; i--) {
        j = Math.random() * (i + 1) | 0;
        temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
}
/*jslint bitwise: false */

function rotateArray(array, n) {
    n %= array.length;
    return array.slice(n, array.length).concat(array.slice(0, n));
}

//=====================================================================
// Random numbers
//=====================================================================

function randomFloatBetween(min, max) { // ... [min, max)
    // Math.random() is 0 (inclusive) to 1 (exclusive), i.e. [0 ... 1)
    // http://stackoverflow.com/questions/1527803/
    return Math.random() * (max - min) + min;
}

function randomIntegerBetween(min, max) { // both inclusive
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomBool(p) {
    if (p === undefined || p === null) {
        p = 0.5;
    }
    return (Math.random() < p);
}

function randomNormal(mean, variance) {
    // adapted from
    // http://blog.yjl.im/2010/09/simulating-normal-random-variable-using.html
    if (mean === undefined) {
        mean = 0.0;
    }
    if (variance === undefined) {
        variance = 1.0;
    }
    var V1,
        V2,
        S,
        U1,
        U2,
        X;
    do {
        U1 = Math.random();
        U2 = Math.random();
        V1 = 2 * U1 - 1;
        V2 = 2 * U2 - 1;
        S = V1 * V1 + V2 * V2;
    } while (S > 1);
    X = Math.sqrt(-2 * Math.log(S) / S) * V1;
    X = mean + Math.sqrt(variance) * X;
    return X;
}

//=============================================================================
// Other maths
//=============================================================================

function div(a, b) {
    // http://stackoverflow.com/questions/4228356/
    return Math.floor(a / b);
}

function clip(x, minimum, maximum) {
    return Math.max(Math.min(x, maximum), minimum);
}

//=============================================================================
// Raphael
//=============================================================================

function alignTop(t) {
    var b = t.getBBox();
    t.attr("y", b.y + b.height);
    // "y", when written, is the vertical midpoint, for text objects
    // "y", when read from the bounding box, is the actual top
    // ... so if you want the top to be at y', then y = y' + height/2
}

function textbox_slow(paper, x, y, maxwidth, text, params) {
    trace("WARNING: taskhtmlcommon.textbox() is too slow");
    // RIDICULOUSLY SLOW - avoid. Later versions of SVG will support text
    // wrapping... Word wrap: http://stackoverflow.com/questions/3142007/
    var t = paper.text(x, y).attr(params),
        words = text.split(" "),
        tempText = "",
        i;
    t.attr("text-anchor", "start");
    for (i = 0; i < words.length; ++i) {
        t.attr("text", tempText + " " + words[i]);
        if (t.getBBox().width > maxwidth) {
            tempText += "\n" + words[i];
        } else {
            tempText += " " + words[i];
        }
    }
    t.attr("text", tempText.substring(1));
    alignTop(t);
    return t;
}

function textbox(paper, x, y, maxwidth, content, params) {
    // Word wrap: http://stackoverflow.com/questions/3142007/
    var t = paper.text(x, y).attr(params),
        abc = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        letterWidth,
        i,
        l,
        words = content.split(" "),
        working_x = 0,
        s = [];
    t.attr({
        'text-anchor' : 'start',
        "text" : abc
    });
    letterWidth = t.getBBox().width / abc.length;
    /* RNC: this statement seems redundant
    t.attr({
        "text" : content
    });
    */
    for (i = 0; i < words.length; i++) {
        l = words[i].length;
        if (working_x + (l * letterWidth) > maxwidth) {
            s.push("\n");
            working_x = 0;
        }
        working_x += l * letterWidth;
        s.push(words[i] + " ");
    }
    t.attr({
        "text" : s.join("")
    });
    alignTop(t);
    return t;
}

function setTouchStartEvent(element, func) {
    // Don't set both! In Titanium, that appears to cause, in response to a
    // touch:
    // (1) first event
    // (2) second event comes along and overwrites it somehow, aborting the
    //     first function call MIDWAY (!?)
    if (inTitanium) {
        element.touchstart(func);
    } else {
        element.mousedown(func); // for web browser debugging
    }
}

function clearTouchEvents(element) {
    if (inTitanium) {
        element.untouchstart();
    } else {
        element.unmousedown(); // for web browser debugging
    }
}

function createButton(paper, BUTTONINFO) {
    var set = paper.set(),
        button = paper.rect(BUTTONINFO.left,
                            BUTTONINFO.top,
                            BUTTONINFO.right - BUTTONINFO.left,
                            BUTTONINFO.bottom - BUTTONINFO.top,
                            BUTTONINFO.radius).attr(BUTTONINFO.shapeattr),
        caption = paper.text((BUTTONINFO.left + BUTTONINFO.right) / 2,
                             (BUTTONINFO.top + BUTTONINFO.bottom) / 2,
                             BUTTONINFO.label).attr(BUTTONINFO.textattr);
    set.push(button);
    set.push(caption);
    return set;
}

function createText(paper, text, x, y, attr) {
    return paper.text(x, y, text).attr(attr);
}

//=============================================================================
// Time
//=============================================================================

function now() {
    return moment(); // "new" not necessary: http://momentjs.com/docs/
}

function momentToString(m) {
    // Function must be identical in conversion.js and taskhtmlcommon.jsx
    var DETAILED_DATETIME_FORMAT = "YYYY-MM-DDTHH:mm:ss.SSSZ";
        // ISO-8601 is YYYY-MM-DDTHH:mm:ssZ; we add milliseconds
    return m.format(DETAILED_DATETIME_FORMAT); // convert moment to string
}

function momentToDateOnlyString(m) {
    return m.format("YYYY-MM-DD");
}

//=============================================================================
// Communication to/from webview
//=============================================================================

function json_freeze_moment(m) {
    // Function must be identical in conversion.js and taskhtmlcommon.jsx
    return {
        _class: "moment",
        value: momentToString(m),
    };
}

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

// AS OF V1.30, json_encoder_replacer() removed, as it was doing nothing
// except altering moments, and moments alter themselves beforehand via
// JSON.stringify -- so use preprocess_moments_for_json_stringify() instead.

//=============================================================================
// Maths
//=============================================================================

/*
    Default SVG coordinate space: x positive-right, y positive-down
    atan2() gives anticlockwise angle in radians, for x positive-right,
        y positive-UP
    SVG rotation uses positive-clockwise:
    http://www.learnsvg.com/books/learnsvg/html/bitmap/chapter06/page06-03.php
    So we will work with:
    - x positive right
    - y positive down
    - angles: positive clockwise, zero to the right (following the convention:
      positive rotation is from x+ axis towards y+ axis)
*/

function pointOnCircle(centre, r, angleDegrees) {
    return {
        x: centre.x + r * Math.cos(angleDegrees * RADPERDEG),
        y: centre.y + r * Math.sin(angleDegrees * RADPERDEG)
    };
}

function pointAddXY(point, dx, dy) {
    return {
        x: point.x + dx,
        y: point.y + dy
    };
}

function vectorFromTo(from, to) {
    return {
        x: to.x - from.x,
        y: to.y - from.y
    };
}

function vectorAngleDegrees(vector) {
    // atan2() gives +pi/2 where x=0, y>0
    return Math.atan2(vector.y, vector.x) / RADPERDEG;
}

//=============================================================================
// Communication with the "outside world":
//=============================================================================

/*
    Note that the Titanium object may be undefined when the webview is created.
    So we have to check at runtime.
    Chrome: Titanium undefined, alert works, use console.log
    Android: Titanium defined, use Titanium.API.trace
    iOS: Titanium defined, alert works, Titanium.API.trace crashes silently
    (nonexistent!), use Titanium.API.debug
        for (var prop in Titanium.API) {
            alert("Titanium.API: " + prop);
        }
*/

function init() {
    trace("taskhtmlcommon.init()");
    if (windowInitialized) {
        return; // don't do it twice
    }
    windowInitialized = true;
    if (inTitanium) {
        // Titanium app listeners -- require matching remove call
        Titanium.App.addEventListener(EVENTNAME_IN, incomingEvent);
        // ... must have matching removeEventListener call
    }
    startTask();
}

function shutdown() {
    trace("taskhtmlcommon.shutdown()");
    if (!windowInitialized) {
        return;
    }
    if (inTitanium) {
        Titanium.App.removeEventListener(EVENTNAME_IN, incomingEvent);
    }
    windowInitialized = false;
}

function sendEvent(e) {
    if (inTitanium) {
        trace("taskhtmlcommon.sendEvent()");
        Titanium.App.fireEvent(EVENTNAME_OUT, e);
    } else {
        trace("taskhtmlcommon.sendEvent() -- does nothing outside Titanium");
    }
}

//=============================================================================
// Sounds (see taskcommon.js for standard handler)
//=============================================================================

function loadSound(filename, volume, finishedEventParams) {
    if (!inTitanium) {
        trace(NOT_IN_TITANIUM_MSG);
        return;
    }
    Titanium.App.fireEvent(EVENTNAME_OUT, {
        eventType: "loadsound",
        sound: filename,
        volume: volume,
        finishedEventParams: finishedEventParams
    });
}

function setVolume(filename, volume) {
    if (!inTitanium) {
        trace(NOT_IN_TITANIUM_MSG);
        return;
    }
    Titanium.App.fireEvent(EVENTNAME_OUT, {
        eventType: "setvolume",
        sound: filename,
        volume: volume
    });
}

function playSound(filename) {
    if (!inTitanium) {
        trace(NOT_IN_TITANIUM_MSG);
        return;
    }
    Titanium.App.fireEvent(EVENTNAME_OUT, {
        eventType: "playsound",
        sound: filename
    });
}

function pauseSound(filename) {
    if (!inTitanium) {
        trace(NOT_IN_TITANIUM_MSG);
        return;
    }
    Titanium.App.fireEvent(EVENTNAME_OUT, {
        eventType: "pausesound",
        sound: filename
    });
}

function stopSound(filename) {
    if (!inTitanium) {
        trace(NOT_IN_TITANIUM_MSG);
        return;
    }
    Titanium.App.fireEvent(EVENTNAME_OUT, {
        eventType: "stopsound",
        sound: filename
    });
}

function unloadSound(filename) {
    if (!inTitanium) {
        trace(NOT_IN_TITANIUM_MSG);
        return;
    }
    Titanium.App.fireEvent(EVENTNAME_OUT, {
        eventType: "unloadsound",
        sound: filename
    });
}

trace("taskhtmlcommon.jsx: In Titanium? " + inTitanium);
