// scaletest.jsx

/*
    Copyright (C) 2015-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.

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
/*global unescape */
/*global document, event */ // DOM
/*global trace, sendEvent, createText, createButton, setTouchStartEvent,
    registerWebviewTask
*/
/*global Raphael */

    //-------------------------------------------------------------------------
    // Incoming task parameters
    //-------------------------------------------------------------------------
var tp = JSON.parse(unescape("INSERT_paramsString")),
    //-------------------------------------------------------------------------
    // Events
    //-------------------------------------------------------------------------
    TASKNAME = "SCALETEST",
    EVENTNAME_OUT = "SCALETEST_EVENT_FROM_WEBVIEW",
    EVENTNAME_IN = "SCALETEST_EVENT_TO_WEBVIEW",
    //-------------------------------------------------------------------------
    // Other
    //-------------------------------------------------------------------------
    paper = new Raphael(0, 0, tp.screenWidth, tp.screenHeight);

function incomingEvent(e) {
    trace("incomingEvent: " + JSON.stringify(e));
}

function onKeyPress(e) {
    // http://javascript.info/tutorial/keyboard-events
    // http://stackoverflow.com/questions/905222
    e = e || event;
    trace("keypress: " + e.keyCode);
    switch (e.keyCode) {
    case 27:  // Escape
        break;
    default:
        break;
    }
    return false;  // prevent it bubbling up
}

function onTouchMove(e) {
    // This prevents native scrolling from happening.
    trace("touchmove");
    e.preventDefault();
}

function startTask() {
    var gridattr = {stroke: "#fff", opacity: 0.5, "stroke-width" : 1},
        PROMPT_X = 400,
        PROMPT_Y = 200,
        FONT = "20px Arial",
        PROMPT_ATTR = {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "text-anchor": "start" // start, middle, end
        },
        EXIT = {
            label: "Exit",
            shapeattr: {
                fill: Raphael.rgb(0, 0, 200),
                stroke: Raphael.rgb(255, 255, 255),
                "stroke-width": 3
            },
            textattr: {
                fill: Raphael.rgb(255, 255, 255),
                font: FONT,
                "text-anchor": "middle" // start, middle, end
            },
            left: 100,
            right: 300,
            top: 500,
            bottom: 600,
            radius: 20,
        },
        i,
        B;

    trace("starttask: params = " + JSON.stringify(tp));

    // Outgoing event
    sendEvent({eventType: "test"});

    // Local listeners
    document.body.addEventListener('touchmove', onTouchMove, false);
    document.body.addEventListener('keydown', onKeyPress, false);

    // grid
    for (i = 0; i < tp.screenWidth || i < tp.screenHeight; i += 100) {
        paper.path(["M", 0, i, "L", tp.screenWidth, i]).attr(gridattr);
        paper.path(["M", i, 0, "L", i, tp.screenHeight]).attr(gridattr);
    }
    // text
    paper.text(PROMPT_X, PROMPT_Y, "Raphael text").attr(PROMPT_ATTR);

    // button
    B = createButton(paper, EXIT);
    setTouchStartEvent(B, function () {
        sendEvent({eventType: "exit"});
    });
}

registerWebviewTask(TASKNAME, EVENTNAME_IN, EVENTNAME_OUT,
                    startTask, incomingEvent);
