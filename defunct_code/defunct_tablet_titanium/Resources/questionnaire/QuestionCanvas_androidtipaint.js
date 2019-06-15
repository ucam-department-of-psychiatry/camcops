// QuestionCanvas_androidtipaint.js
// Editable image display - uses a custom Android module.

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

var MODULE_NAME = "QuestionCanvas_androidtipaint",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

/*

    BASIC DOCUMENTATION

    Ti.Paint.createPaintView()
        Creates a Ti.Paint.PaintView object.

    Ti.Paint.Paintview
        Functions
            clear()
                Clears the paint view.
        Properties
            strokeWidth[double]
                Controls the width of the strokes.
            strokeColor[string]
                Controls the color of the strokes.
            strokeAlpha[int]
                Controls the opacity of the strokes.
            eraseMode[boolean]
                Controls if the strokes are in "erase mode" -- that is, any
                existing paint will be erased.
            image[string]
                Loads an image (by its URL) directly in to the paint view so
                that it can be drawn on and erased.

    MORE EXAMPLES
    http://developer.appcelerator.com/question/136372/tipaint-module-only-loads-image-from-resources-directory-android

    THE SOURCE
    https://github.com/appcelerator/titanium_modules/blob/master/paint/mobile/android/src/ti/modules/titanium/paint/UIPaintView.java
    https://github.com/appcelerator/titanium_modules/blob/master/paint/mobile/android/src/ti/modules/titanium/paint/PaintViewProxy.java
    https://github.com/appcelerator/titanium_modules/blob/master/paint/mobile/ios/Classes/TiPaintPaintView.m

    ... suggests also:

        setEraseMode()
        setStrokeWidth()
        setStrokeColor()
        setStrokeAlpha()
        setImage(String imagePath) -- NB not a BLOB parameter
        clear()
*/

function PaintModule() {
    var platform = require('lib/platform');
    if (platform.android) {
        return require('org.camcops.androidtipaint'); // module
    }
    return require('ti.paint'); // module
}

function QuestionCanvas(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        uifunc = require('lib/uifunc'),
        platform = require('lib/platform'),
        self = this;
    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "strokeWidth",
                               UICONSTANTS.CANVAS_DEFAULT_STROKEWIDTH);
    qcommon.setDefaultProperty(props, "strokeColor",
                               UICONSTANTS.CANVAS_DEFAULT_STROKECOLOUR);
    qcommon.setDefaultProperty(props, "strokeAlpha",
                               UICONSTANTS.CANVAS_DEFAULT_STROKEALPHA);
    // other properties:
    //      image
    //      imageWidth
    //      imageHeight
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    // URL is filename
    this.startingImageUrl = platform.getNativePathOfResourceFile(props.image);
    this.dirtyInFramework = false;

    // Check sizing with e.g. SLUMS three-shape picture (rectangle)

    // View fills its size (then does some magic internally)
    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.FILL,
        height: Titanium.UI.FILL
    });

    // WAIT doesn't work - the wait gets stuck on for some reason (from ~Jan
    // 2014) // this.wait = uifunc.createWait( { window: this.tiview });

    if (!props.readOnly) {
        this.resetButton = uifunc.createReloadButton({
            left: 0,
            top: 0
        });
        this.resetListener = function () { self.reset(); };
        this.resetButton.addEventListener('click', this.resetListener);
        this.tiview.add(this.resetButton);
    }

    this.paintviewprops = {
        top: 0,
        left: UICONSTANTS.ICONSIZE,
        width: Titanium.UI.FILL,
        height: Titanium.UI.FILL,

        strokeWidth: props.strokeWidth,
        strokeColor: props.strokeColor,
        strokeAlpha: props.strokeAlpha,
        eraseMode: false,
        readOnly: props.readOnly, // RNC addition
        requestedWidth: props.imageWidth, // RNC addition
        requestedHeight: props.imageHeight, // RNC addition

        image: this.startingImageUrl
    };
    this.paintview = null;

    this.setValueOnlyAfterVisible = true;
    // otherwise, my PaintViewProxy says:
    //      setImage: paintView == null; ignoring setImage request
}
lang.inheritPrototype(QuestionCanvas, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionCanvas, {

    cleanup: function () {
        if (this.resetListener) {
            this.resetButton.removeEventListener("click", this.resetListener);
            this.resetListener = null;
        }
        this.resetButton = null;
        this.paintview = null;
        // doesn't work - the wait gets stuck on for some reason (from ~Jan
        // 2014) // this.wait = null;
    },

    createPaintView: function () {
        Titanium.API.trace(MODULE_NAME + ".createPaintView");
        var Paint = new PaintModule();
        this.paintview = Paint.createPaintView(this.paintviewprops);
        this.tiview.add(this.paintview);
    },

    destroyPaintView: function () {
        Titanium.API.trace(MODULE_NAME + ".destroyPaintView");
        if (this.paintview) {
            this.tiview.remove(this.paintview);
            this.paintview = null;
        }
    },

    getBlobPNGFromCanvas: function () { // ... does indeed seem to be a PNG!
        return this.paintview.getImage().media; // RNC custom function
        /*
        var platform = require('lib/platform');
        if (platform.android) {
            // https://developer.appcelerator.com/question/152878/tipaint-error-in-android
            return this.paintview.toImage().media;
            // ... works fine

            // In full:
            // var result = this.paintview.toImage();
            // Titanium.API.trace(MODULE_NAME + ".getBlobPNGFromCanvas: " +
            //                    JSON.stringify(result) );
            // return result.media;
        }
        else {
            return this.paintview.toImage();
            // NOT WORKING RELIABLY ON iOS.
            // ALSO, OCCASIONAL SCREEN CORRUPTION (REGULAR DOT-PATTERNS AS IF
            // RAM DUMPED TO SCREEN).
            // Definitely a buggy module.
            // Abandoned for now on iOS in favour of webview.
        }
        */
    },

    getDataUrl: function () {
        //Titanium.API.trace(MODULE_NAME + ".getDataUrl");

        /*
        // Method 1: doesn't work:
        var blob = this.questionnaire.getFieldValue(this.field);
        if (blob == null) {
            return null;
        }
        var conversion = require('lib/conversion');
        return conversion.blobToPngUrl(blob);
        */

        // Method 2:
        var filename = this.questionnaire.getFieldValue(this.field, true);
        // SPECIAL: getBlobsAsFilenames = true
        return filename; // which is as a URL
    },

    isDirty: function () {
        if (this.dirtyInFramework) {
            return true;
        }
        return this.paintview.getDirty();
    },

    onClose: function () {
        Titanium.API.trace(MODULE_NAME + ".onClose");
        this.save();
    },

    reset: function () {
        Titanium.API.trace(MODULE_NAME + ".reset");
        this.writeImageToCanvas(this.startingImageUrl);
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
        Titanium.API.trace(MODULE_NAME + ".save");
        // doesn't work - the wait gets stuck on for some reason (from ~Jan
        // 2014) // this.wait.show();
        var blob = this.getBlobPNGFromCanvas();
        Titanium.API.trace("Eventual blob length should be: " + blob.length);
        this.questionnaire.setFieldValue(this.field, blob);
        this.dirtyInFramework = false;
        // doesn't work - the wait gets stuck on for some reason (from ~Jan
        // 2014) // this.wait.hide();
        // Titanium.API.trace(MODULE_NAME + ".save -- FINISHING");
    },

    setFromField: function () {
        Titanium.API.trace(MODULE_NAME + ".setFromField");
        // doesn't work - the wait gets stuck on for some reason (from ~Jan
        // 2014) // this.wait.show();
        var url = this.getDataUrl();
        if (!url) {
            this.reset();
        } else {
            this.writeImageToCanvas(url);
        }
        this.dirtyInFramework = false;
        // doesn't work - the wait gets stuck on for some reason (from ~Jan
        // 2014) // this.wait.hide();
    },

    writeImageToCanvas: function (imageUrl, recreateView) {
        // image may be null
        if (recreateView === undefined) {
            recreateView = false;
        }
        Titanium.API.trace(MODULE_NAME + ".writeImageToCanvas: imageUrl = " +
                           JSON.stringify(imageUrl));
        if (!this.paintview || recreateView) {
            this.destroyPaintView();
            this.paintviewprops.image = imageUrl;
            this.createPaintView();
        } else {
            // ANDROID: WORKS BECAUSE I FIXED IT
            // IOS: DOESN'T WORK
            this.paintview.setImage(imageUrl);
        }
    }
    /*
    Android:
        this.paintview.setImage:
            ... either a simple crash probably relating to a duff filename
                (e.g. leading '/'), or:
            Uncaught Error: Only the original thread that created a view
            hierarchy can touch its views.
            ... or a java.lang.NullPointerException at the moment of
            calling this.paintview.setImage(image); in PaintViewProxy.java
            ... ah, see the source for clear() in the proxy -- needs a
                thread check...?
        destroy/recreate
            ...
            ... for a blob filename using .nativePath:
                "Immutable bitmap passed to Canvas constructor"
                though Ti.Paint source code looks OK for the method given at
                    http://stackoverflow.com/questions/13119582/android-immutable-bitmap-crash-error
                Ti.Paint:
                    https://github.com/appcelerator/titanium_modules/blob/master/paint/mobile/android/src/ti/modules/titanium/paint/UIPaintView.java
                Android Bitmap:
                    https://code.google.com/p/android-source-browsing/source/browse/graphics/java/android/graphics/Bitmap.java?repo=platform--frameworks--base&r=7b4ba9d80d2cdde310c29d01d0e22c7815d84261
                ... ah, actually, the crashing part was PaintView.onSizeChanged (not PaintView.setImage)
                ... and that may not explicitly make sure the new Bitmap is mutable

            What else? Actual creator uses tiImage (a string) and:
                TiDrawableReference.fromUrl(proxy, tiImage)
            ... from https://github.com/appcelerator/titanium_mobile/blob/master/android/titanium/src/java/org/appcelerator/titanium/view/TiDrawableReference.java

    created new module (androidtipaint); adapted previous; make bitmap mutable in onSizeChanged
    Jan 2014: further changes. Now it's nice.
    */

});
module.exports = QuestionCanvas;
