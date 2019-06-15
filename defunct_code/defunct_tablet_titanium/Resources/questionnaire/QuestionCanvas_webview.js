// QuestionCanvas_webview.js
// Editable image display - webview version. Too slow on Android.

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

/*jslint node: true */
"use strict";
/*global Titanium */

var MODULE_NAME = "QuestionCanvas_webview",
    EVENT_TO_WEBVIEW = "SKETCHCANVAS_EVENT_TO_WEBVIEW", // must match task HTML/JS
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionCanvas(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        conversion = require('lib/conversion'),
        uifunc = require('lib/uifunc'),
        COLOURS = require('common/COLOURS'),
        propsImageSize = {
            width: props.imageWidth,
            height: props.imageHeight
        },
        fileImageSize = {},
        fallbackImageSize = {
            width: UICONSTANTS.CANVAS_DEFAULT_IMAGEWIDTH,
            height: UICONSTANTS.CANVAS_DEFAULT_IMAGEHEIGHT
        },
        file,
        startingImageBlob,
        finalImageSize,
        taskcommon = require('lib/taskcommon'),
        params,
        html,
        self = this;

    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.setDefaultProperty(props, "readOnly", false);
    // other properties:
    //      image
    //      imageWidth
    //      imageHeight
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.webviewReady = false;
    this.dirtyInFramework = false;
    this.startingImageUrl = null;

    if (props.image) {
        // URL is data
        file = Titanium.Filesystem.getFile(
            Titanium.Filesystem.resourcesDirectory,
            props.image
        );
        startingImageBlob = file.read();
        this.startingImageUrl = conversion.blobToPngUrl(startingImageBlob);
        // size (Titanium bug workaround as blob.height and blob.width aren't
        // set properly)
        fileImageSize = uifunc.getImageSize(startingImageBlob);
        Titanium.API.trace(MODULE_NAME + ": image size read from file as " +
                           fileImageSize.width + " x " + fileImageSize.height);
    }
    finalImageSize = qcommon.determineImageSizeHierarchically(
        propsImageSize,
        fileImageSize,
        fallbackImageSize
    );
    Titanium.API.trace(MODULE_NAME + ": final image size sent to HTML: " +
                       finalImageSize.width + " x " + finalImageSize.height);

    // We can't call Javascript within the HTML until it's initialized.
    // So we can have the HTML request initialization data from us in the
    // following way:
    // (a) HTML loads
    // (b) <body onload="init()"> -> function init() ->
    //      Titanium.App.fireEvent("EVENT_TO_ELEMENT",
    //                             {broadcastToAllElements: true,
    //                             webviewWantsId: true} );
    // (c) ... routed via Questionnaire to QuestionCanvas...
    // (d) ... which then flags the webview as ready-to-receive and sends it
    //         its page/element ID
    // (e) ... which then triggers the webview to request data
    // HOWEVER, mainly what we want to pass in, apart from the page/element ID,
    // is the image size; we know that from the start, and it assists the HTML
    // in setting its size to know that in advance.
    // So we'll use text replacement in the HTML instead.

    params = {
        lineColour: UICONSTANTS.CANVAS_DEFAULT_STROKECOLOUR,
        pageId: props.pageId,
        elementId: props.elementId,
        imageWidth: finalImageSize.width,
        imageHeight: finalImageSize.height,
        readOnly: props.readOnly,
        lineWidth: UICONSTANTS.CANVAS_DEFAULT_STROKEWIDTH,
        backgroundColour: COLOURS.WHITE
    };
    html = taskcommon.loadHtmlSetParams(
        "task_html/sketchcanvas.html",
        params,
        "task_html/sketchcanvas.jsx"
    );
    // And extra substitutions:
    html = html.replace(/INSERT_imageWidth/g, finalImageSize.width);
    html = html.replace(/INSERT_imageHeight/g, finalImageSize.height);
    html = html.replace(/INSERT_backgroundColour/g, COLOURS.WHITE);
    Titanium.API.trace(html);

    // Additionally, we prefer events to evalJS() -- the latter tends to throw
    // up "called from wrong thread" warnings in the log.
    // On the other hand, we seem to be able to add event listeners, but it's
    // hard to get them removed again!

    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.FILL,
        height: Titanium.UI.FILL  // Don't use SIZE. It gets CONFUSED as the
        // canvas height changes, and sometimes (unreliably) goes to zero.
        // layout: 'vertical', // No! Makes the height zero sometimes.
    });

    if (!props.readOnly) {
        this.resetButton = uifunc.createReloadButton({
            left: 0,
            top: 0
        });
        this.resetListener = function () { self.reset(); };
        this.resetButton.addEventListener('click', this.resetListener);
        this.tiview.add(this.resetButton);
    }

    this.webview = Titanium.UI.createWebView({
        html: html,
        top: 0,
        left: UICONSTANTS.ICONSIZE,
        height: Titanium.UI.FILL,
        width: Titanium.UI.FILL,
        willHandleTouches: true, // for iOS
        scalesPageToFit: false, // prevents zooming on iOS
        enableZoomControls: false, // for Android
        scrollsToTop: false, // iOS
        showScrollbars: false, // MobileWeb?
        disableBounce: true // iOS
        // DISABLE any zooming/scaling by the webview
    });
    this.tiview.add(this.webview);

    // WAIT
    this.wait = uifunc.createWait({ window: this.tiview });
}
lang.inheritPrototype(QuestionCanvas, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionCanvas, {

    cleanup: function () {
        if (this.resetListener) {
            this.resetButton.removeEventListener("click", this.resetListener);
            this.resetListener = null;
        }
        this.resetButton = null;
        this.webview = null;
        this.wait = null;
    },

    eventToElement: function (e) {
        // Events from the webview come here.
        Titanium.API.trace(MODULE_NAME + ".eventToElement: e=" +
                           JSON.stringify(e));
        if (e.webviewWantsData) {
            this.webviewReady = true;
            Titanium.API.trace("webview wants data");
            this.setFromField();
        }
    },

    getBlobPNGFromCanvas: function () {
        var conversion = require('lib/conversion');
        return conversion.pngUrlToBlob(this.getPNGURLFromCanvas());
    },

    getDataUrl: function () {
        //Titanium.API.trace(MODULE_NAME + " getDataUrl");
        var blob = this.questionnaire.getFieldValue(this.field),
            conversion = require('lib/conversion');
        //Titanium.API.trace(MODULE_NAME + " getDataUrl: field = " +
        //                   this.field + ", blob = " + blob);
        if (!blob) {
            return null;
        }
        return conversion.blobToPngUrl(blob);
    },

    getPNGURLFromCanvas: function () {
        // We could use the toImage function of the view:
        // var blob = conversion.imageBlobFromView(webview);
        // ... but it'll include borders, etc. So:
        return this.webview.evalJS("getImage();");
    },

    isDirty: function () {
        if (this.dirtyInFramework) {
            return true;
        }
        if (!this.webviewReady) {
            // Titanium.API.trace(MODULE_NAME + ".isDirty: called before " +
            //                    "webview ready; refusing");
            return false;
        }
        var conversion = require('lib/conversion'),
            dirtyInCanvas = conversion.boolFromString(
                this.webview.evalJS("isDirty();")
            );
        return dirtyInCanvas;
    },

    onClose: function () {
        Titanium.API.trace(MODULE_NAME + ": onClose");
        this.save();
        this.webview.evalJS("shutdown()");
        // ... we seem to have to do this by hand
    },

    reset: function () {
        // Titanium.API.trace(MODULE_NAME + ".reset");
        this.writeDataUrlToCanvas(this.startingImageUrl);
        this.dirtyInFramework = true;
    },

    save: function () {
        // Not sure how -- or, more pertinently, whether -- to save the image
        // every time the user touches the canvas. Probably best to save it
        // just when we close this view.
        // But not if it's unmodified; that just slows us down.
        if (this.readOnly || !this.isDirty()) {
            return;
        }
        Titanium.API.trace(MODULE_NAME + ".save -- saving");
        this.wait.show();
        var blob = this.getBlobPNGFromCanvas();
        Titanium.API.trace("Eventual blob length should be: " + blob.length);
        this.questionnaire.setFieldValue(this.field, blob);
        this.dirtyInFramework = false;
        this.wait.hide();
    },

    setFromField: function () {
        Titanium.API.trace(MODULE_NAME + ".setFromField");
        this.wait.show();
        var url = this.getDataUrl();
        if (!url) {
            this.reset();
        } else {
            this.writeDataUrlToCanvas(url);
        }
        this.dirtyInFramework = false;
        this.wait.hide();
    },

    writeDataUrlToCanvas: function (url) {
        if (!this.webviewReady) {
            Titanium.API.trace(MODULE_NAME + ".writeDataUrlToCanvas: called " +
                               "before webview ready; refusing");
            return;
        }
        // Titanium.API.trace(MODULE_NAME + ": webview size = " +
        //                    webview.size.width +
        //                    " x " + webview.size.height);
        // Titanium.API.trace(MODULE_NAME + ".writeDataUrlToCanvas: blob = " +
        //                    JSON.stringify(blob));
        if (!url) {
            Titanium.API.trace(MODULE_NAME + ".writeDataUrlToCanvas: null " +
                               "url, calling clearImage()");
            Titanium.App.fireEvent(EVENT_TO_WEBVIEW, {
                pageId: this.pageId,
                elementId: this.elementId,
                clearImage: true
            });
        } else {
            Titanium.API.trace(MODULE_NAME + ".writeDataUrlToCanvas: " +
                               "calling setImage()");
            Titanium.App.fireEvent(EVENT_TO_WEBVIEW, {
                pageId: this.pageId,
                elementId: this.elementId,
                setImage: true,
                data: url
            });
        }
    }

});
module.exports = QuestionCanvas;

// CANVAS: http://developer.appcelerator.com/question/55121/html5-canvas-drawing-in-webview
// CANVAS: https://wiki.appcelerator.org/display/guides/The+WebView+Component
// http://developer.appcelerator.com/question/132151/webview-canvastodataurl-conversion-to-a-valid-png-and-then-save-to-local-gallery

// A very posh sketchpad: http://mudcu.be/sketchpad/
// Canvas tutorial: https://developer.mozilla.org/en-US/docs/Canvas_tutorial
// Canvas reference: http://dev.w3.org/html5/spec/the-canvas-element.html
// Canvas context http://dev.w3.org/html5/2dcontext/
// Setting canvas width/height to enclosing window: http://stackoverflow.com/questions/1664785/html5-canvas-resize-to-fit-window
// Disable zooming by double-tapping: http://developer.appcelerator.com/question/37771/prevent-double-tap-zoom-in-web-view
// Get base-64-encoded image from canvas: https://developer.mozilla.org/en-US/docs/DOM/HTMLCanvasElement

// DATA PASSING: http://developer.appcelerator.com/question/27781/pass-data-to-webview
// This doesn't work: passing parameters prior to/at initialization: http://sushmapandey.wordpress.com/2011/04/09/passing-parameters-to-html-page-loaded-in-a-webview/

// CANVAS SIZE:
// http://stackoverflow.com/questions/4288253/html5-canvas-100-width-height-of-viewport
// http://stackoverflow.com/questions/11006812/html5-boilerplate-meta-viewport-and-width-device-width
// http://stackoverflow.com/questions/8454255/how-can-i-have-a-full-screen-canvas-at-full-resolution-in-an-iphone-4
// http://bravenewmethod.wordpress.com/2011/08/28/html5-canvas-layout-and-mobile-devices/
// view-source:http://hernan.amiune.com/games/catsdogs/
// http://hernan.amiune.com/teaching/HTML5-Game-Development-Tips.html
// http://stackoverflow.com/questions/4938346/canvas-width-and-height-in-html5
// http://stackoverflow.com/questions/1152203/centering-a-canvas
// Centre a canvas: http://stackoverflow.com/questions/12030481/how-to-center-a-dynamically-sized-canvas-in-a-viewport
