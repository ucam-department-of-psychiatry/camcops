// sketchcanvas.jsx

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
/*global unescape, document, window, Image */
/*global inTitanium, trace, sendEvent, registerWebviewTask */

//=============================================================================
// Communication with the "outside world": see taskhtmlcommon.js
//=============================================================================
// Must receive task parameters, and provide incomingEvent(), startTask()

    //-------------------------------------------------------------------------
    // Incoming task parameters
    //-------------------------------------------------------------------------
var tp = (inTitanium ?
        //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        // Titanium: config is passed here by replacing this literal:
        //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        JSON.parse(unescape("INSERT_paramsString")) :

        //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        // Web browser debugging (much quicker): test parameters
        //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        {
            // Asus Eee Pad is 1200 x 800 (WXGA), effective size (minus system
            // UI) 1200 x 752. iPad is 1024 x 768
            screenWidth: 1024,
            screenHeight: 752,
        }
    ),
    TASKNAME = "QuestionCanvas (sketchcanvas.html)",
    EVENTNAME_OUT = "EVENT_TO_ELEMENT",
    EVENTNAME_IN = "SKETCHCANVAS_EVENT_TO_WEBVIEW",
    canvas = document.getElementById("canvas"),
    ctx = canvas.getContext("2d"),
    // iOSSafari = (navigator.userAgent.match(/(iPhone)|(iPod)|(iPad)/i) !== null),
    dirty = false,
    initialized = false,
    scale = 1.0,
    drawing = false,
    pathBegun = false;

ctx.strokeStyle = tp.lineColour;
ctx.lineWidth = tp.lineWidth;
ctx.fillStyle = tp.backgroundColour;

function getViewportSize() {
    return {
        width: window.innerWidth, // iOSSafari ? window.innerWidth : document.documentElement.clientWidth,
        height: window.innerHeight
    };
}

function reportViewportSize() {
    var viewport = getViewportSize();
    trace("webview: viewport width = " + viewport.width + ", height = " + viewport.height);
}

function resize() {
    trace("resize: imageWidth=" + tp.imageWidth + ", imageHeight=" + tp.imageHeight);
    reportViewportSize();
    var viewport = getViewportSize(),
        xscale = viewport.width / tp.imageWidth,
        yscale = viewport.height / tp.imageHeight;
    scale = Math.min(xscale, yscale);
    // trace("... webview: scale = " + scale);
    canvas.style.width = (tp.imageWidth * scale) + "px"; // CSS has no default units: they must be specified for all non-zero values.
    canvas.style.height = (tp.imageHeight * scale) + "px";
}

function clearImage() {
    // trace("clearImage");
    dirty = true;
    ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
}

function setImage(urlEncodedData) {
    trace("setImage (NB calls clearImage next)"); // : url=" + urlEncodedData);
    clearImage();
    // trace("incoming image: " + urlEncodedData);
    var image = new Image();
    image.onload = function () {
        // called when the image has been loaded
        trace("setImage / onload callback");
        ctx.drawImage(image, 0, 0);
        dirty = false;
    };
    image.src = urlEncodedData; // you can also load images by filename
}

function getImage() {
    // trace("webview getImage");
    return canvas.toDataURL(); // can specify type, but PNG is the default and what we want
}

function getPage(event) {
    //when on mobile safari, the coordinates information is inside the targetTouches object
    if (event.targetTouches) {
        event = event.targetTouches[0];
    }
    if (event.pageX !== undefined &&
            event.pageX !== null &&
            event.pageY !== undefined &&
            event.pageY !== null) {
        return {pageX: event.pageX, pageY: event.pageY};
    }
    var element = (
        (!document.compatMode || document.compatMode === 'CSS1Compat') ?
                document.documentElement :
                document.body
    );
    return {
        pageX: event.clientX + element.scrollLeft,
        pageY: event.clientY + element.scrollTop
    };
}

function onTouchStart() { // 'event' parameter ignored
    if (tp.readOnly) {
        return;
    }
    drawing = true;
    pathBegun = false; // reset the path when starting over
}

function onTouchMove(event) {
    // trace("onTouchMove");
    // slow polling?
    // http://stackoverflow.com/questions/5353210/slow-touchmove-polling-on-android-via-browser-vs-native-app
    // http://stackoverflow.com/questions/9929434/slow-javascript-touch-events-on-android
    // also: http://www.reddit.com/r/Android/comments/rc6ja/developer_who_just_bailed/
    event.preventDefault(); // necessary for touchmove in Android
    event.stopPropagation();

    if (!drawing) {
        return;
    }

    var page = getPage(event),
        X = page.pageX / scale,
        Y = page.pageY / scale;

    // "page" versus "client" coords: http://www.sitepen.com/blog/2008/07/10/touching-and-gesturing-on-the-iphone/
    // trace("onTouchMove: X=" + X + ", Y=" + Y);

    if (pathBegun === false) {
        ctx.beginPath();
        pathBegun = true;
    } else {
        ctx.lineTo(X, Y);
        ctx.stroke();
        dirty = true;
    }
}

function onTouchEnd() { // 'event' parameter ignored
    drawing = false;
}

function isDirty() {
    return dirty;
}

function incomingEvent(e) {
    if (e.pageId !== tp.pageId || e.elementId !== tp.elementId) {
        // trace("webview: incomingElement (to " + getSelfString() + ")... wrong target (event is to " + e.pageId + "/" + e.elementId + ")");
        return;
    }
    // Now, handle events:
    if (e.setImage) {
        // trace("webview: incomingElement (to " + getSelfString() + ")... setImage");
        setImage(e.data);
    } else if (e.clearImage) {
        // trace("webview: incomingElement (to " + getSelfString() + ")... clearImage");
        clearImage();
    }
}

function getSelfString() {
    return tp.pageId + "/" + tp.elementId;
}

function startTask() {
    // May be called multiple times. So set a guard on adding event listeners!
    // ADDITIONALLY, I've not managed to get UNLOAD code to be called yet.
    trace("webview: startTask() " + getSelfString() + ", imageWidth=" +
          tp.imageWidth + ", imageHeight=" + tp.imageHeight);
    reportViewportSize();
    resize();
    // ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height); // http://stackoverflow.com/questions/4938346/canvas-width-and-height-in-html5
    // ctx.translate(0.5, 0.5); // http://stackoverflow.com/questions/4938346/canvas-width-and-height-in-html5
    canvas.addEventListener('touchmove', onTouchMove, false);
    canvas.addEventListener('touchstart', onTouchStart, false);
    canvas.addEventListener('touchend', onTouchEnd, false);
    window.addEventListener('orientationchange', resize, false);
    document.addEventListener('orientationchange', resize, false);
    sendEvent({
        pageId: tp.pageId,
        elementId: tp.elementId,
        webviewWantsData: true
    });
    initialized = true;
}

trace("params: " + JSON.stringify(tp));
registerWebviewTask(TASKNAME, EVENTNAME_IN, EVENTNAME_OUT,
                    startTask, incomingEvent);
