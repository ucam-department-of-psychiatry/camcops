// QuestionPhoto.js
// Simple image display.

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

/*jslint node: true, newcap: true */
"use strict";
/*global Titanium, L */

var MODULE_NAME = "QuestionPhoto",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionPhoto(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        uifunc = require('lib/uifunc'),
        tiprops = {},
        self = this;
    // var debugfunc = require('lib/debugfunc');
    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.requireProperty(props, "rotationField", MODULE_NAME);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "offerDeleteButton", true);
    // some named properties passed to Titanium.UI.createView, see
    // copyStandardTiProps below
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.anchor = {x: 0.5, y: 0.5};
    // http://developer.appcelerator.com/question/84171/rotate-an-image-around-its-center
    this.blank = true;
    this.rotationField = props.rotationField;

    qcommon.copyStandardTiProps(props, tiprops);
    tiprops.width = Titanium.UI.SIZE;
    tiprops.height = Titanium.UI.SIZE;
    this.tiview = Titanium.UI.createView(tiprops);

    this.imageView = Titanium.UI.createImageView({
        top: 0,
        left: UICONSTANTS.ICONSIZE,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE,
        anchorPoint: this.anchor, // iOS only
        touchEnabled: false,
        image: null,
    });
    this.tiview.add(this.imageView);

    // WAIT
    this.wait = uifunc.createWait({ window: this.tiview });

    if (!props.readOnly) {
        // Camera button
        this.takeButton = uifunc.createCameraButton({ top: 0, left: 0 });
        this.takeListener = function () {
            self.take();
        };
        this.takeButton.addEventListener('click', this.takeListener);
        this.tiview.add(this.takeButton);

        // Rotate anticlockwise button
        this.rotateAnticlockwiseButton = uifunc.createRotateAnticlockwiseButton({
            top: UICONSTANTS.ICONSIZE * 2,
            left: 0
        });
        this.rotateAnticlockwiseListener = function () {
            self.rotateAnticlockwise();
        };
        this.rotateAnticlockwiseButton.addEventListener(
            'click',
            this.rotateAnticlockwiseListener
        );
        this.tiview.add(this.rotateAnticlockwiseButton);

        // Rotate clockwise button
        this.rotateClockwiseButton = uifunc.createRotateClockwiseButton({
            top: UICONSTANTS.ICONSIZE * 3,
            left: 0
        });
        this.rotateClockwiseListener = function () {
            self.rotateClockwise();
        };
        this.rotateClockwiseButton.addEventListener(
            'click',
            this.rotateClockwiseListener
        );
        this.tiview.add(this.rotateClockwiseButton);

        // Delete button
        if (props.offerDeleteButton) {
            this.deleteButton = uifunc.createDeleteButton({
                top: UICONSTANTS.ICONSIZE * 5,
                left: 0
            });
            this.deleteListener = function () {
                self.confirmDelete();
            };
            this.deleteButton.addEventListener('click', this.deleteListener);
            this.tiview.add(this.deleteButton);
        }
    }

    // PROBLEM: rotation works fine after the view is open,
    // but it's hard to get it to appear correctly rotated the first time round
    // -- I think because we're using width/height = SIZE, and before
    // the image has loaded, it's confused about what to rotate around.
    // This is the solution:

    this.loadListener = function () { self.applyRotation(); };
    this.imageView.addEventListener('load', this.loadListener);
    // ... fires when image load complete
}
lang.inheritPrototype(QuestionPhoto, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionPhoto, {

    isInputRequired: function () {
        return this.mandatory && this.blank;
    },

    // Image arriving from camera
    acceptPhoto: function (event) {
        // event has members: media (the image), width, height
        // we keep the "event" object intact in an attempt to save memory
        // using pass-by-reference
        this.wait.show();
        // var conversion = require('lib/conversion');

        // Our photo is a blob in event.media
        // One problem: it's giant (presumably 8MP, or 3264x2448). So we may
        // need to resize it.
        /*
        // Titanium.API.trace("Titanium.Platform.availableMemory = " +
        //                    Titanium.Platform.availableMemory);
        // ... in bytes on Android
        if (platform.android) {
            // Another problem: no height/width information in the blob on
            // Android ... so use the fact that event.width and event.height
            // encode this... and this technique:
            // http://developer.appcelerator.com/question/141630/tiimagefactory-for-android-works-in-the-emulator-but-crashes-on-my-phone
            // compute minimum scale to fill the screen

            //var scale = 1;
            //if (width < height) {
            //    scale = Titanium.Platform.displayCaps.platformWidth / width;
            //}
            //else {
            //    scale = Titanium.Platform.displayCaps.platformHeight / height;
            //}

            var offscreenView = Titanium.UI.createImageView({
                image: image,
                // width: width * scale,
                // height: height * scale,
                // width: width,
                // height: height,
                width: UICONSTANTS.PHOTO_WIDTH,
                height: UICONSTANTS.PHOTO_HEIGHT,
            });
            image = offscreenView.toBlob();
        }
        else {
            var ImageFactory = require('ti.imagefactory');
            image = ImageFactory.imageAsResized(image, {
                width: UICONSTANTS.PHOTO_WIDTH,
                height: UICONSTANTS.PHOTO_HEIGHT
            });
        }
        // CONSIDER ALSO: conversion to black and white (e.g. with HTML5
        // canvas...)
        */
        // Save it to our field
        // Titanium.API.trace("Titanium.Platform.availableMemory = " +
        //                    Titanium.Platform.availableMemory);
        // However, for iOS, we have to transfer it encoded...

        // 1...
        // var code = conversion.encodeBlob(conversion.ENCODING_PNGURL, image);
        // 2...
        // Titanium.API.trace("APPLYING PROPERTIES TO BLOB");
        // image.applyProperties({_type: "blob"}); // NOT WORKING
        // Titanium.API.trace("SENDING PHOTO: " + debugfunc.dumpObject(image));
        // 3...
        this.questionnaire.setFieldValue(this.field, event.media);
        this.questionnaire.setFieldValue(this.rotationField, 0);
        // ... default starting rotation

        // code = null; // dispose of memory?
        // Make it visible
        // Titanium.API.trace("Titanium.Platform.availableMemory = " +
        //                    Titanium.Platform.availableMemory);
        this.imageView.setImage(event.media);
        // Titanium.API.trace("Titanium.Platform.availableMemory = " +
        //                    Titanium.Platform.availableMemory);
        this.applyRotation();
        this.blank = false;
        this.wait.hide();
        // Have had out-of-memory crashes in this section. Trying:
        // ti.android.largeHeap
    },

    take: function () {
        this.wait.show();
        var self = this,
            a,
            uifunc;
        Titanium.API.trace("Titanium.Platform.availableMemory = " +
                           Titanium.Platform.availableMemory);
        // ... in bytes on Android
        Titanium.Media.showCamera({
            success: function (event) {
                // called when media returned from the camera
                Titanium.API.trace("Titanium.Platform.availableMemory = " +
                                   Titanium.Platform.availableMemory);
                if (event.mediaType === Titanium.Media.MEDIA_TYPE_PHOTO) {
                    self.acceptPhoto(event);
                } else {
                    uifunc = require('lib/uifunc');
                    uifunc.alert("got the wrong type back =" + event.mediaType);
                }
            },
            cancel: function () {
                // called when user cancels taking a picture
                return;
            },
            error: function (error) {
                // called when there's an error
                a = Titanium.UI.createAlertDialog({title: 'Camera'});
                if (error.code === Titanium.Media.NO_CAMERA) {
                    a.setMessage('Please run this test on device');
                } else {
                    a.setMessage('Unexpected error: ' + error.code);
                }
                a.show();
            },
            autohide: true,
            saveToPhotoGallery: false,
            allowEditing: false,
            mediaTypes: [Titanium.Media.MEDIA_TYPE_PHOTO]
        });
        this.wait.hide();
    },

    rotateClockwise: function () {
        var rotation = this.getRotation();
        rotation = (rotation + 90) % 360;
        this.questionnaire.setFieldValue(this.rotationField, rotation);
        this.applyRotation();
    },

    rotateAnticlockwise: function () {
        var rotation = this.getRotation();
        rotation = (rotation + 270) % 360;
        this.questionnaire.setFieldValue(this.rotationField, rotation);
        this.applyRotation();
    },

    getRotation: function () {
        var rotation = this.questionnaire.getFieldValue(this.rotationField);
        if (rotation === null) {
            rotation = 0;
        }
        return rotation;
    },

    sendImageToView: function (blob) {
        Titanium.API.trace("QuestionPhoto.sendImageToView");
        this.imageView.setImage(blob);
        this.applyRotation(); // will be called by the loadListener too? Not
        // sure of that!
    },

    // From field to image
    setFromField: function () {
        Titanium.API.trace("QuestionPhoto.setFromField");
        if (this.field === undefined) {
            return;
        }
        var blob = this.questionnaire.getFieldValue(this.field);
        if (blob !== null) {
            this.blank = false;
        }
        this.sendImageToView(blob);
    },

    getTransformationMatrix: function () {
        var rotation = this.getRotation();
        return Titanium.UI.create2DMatrix({
            anchorPoint: this.anchor,
            // http://docs.appcelerator.com/titanium/3.0/#!/api/MatrixCreationDict
            rotate: rotation
        });
    },

    /*
        Note also the ImageView autorotate field:
            https://jira.appcelerator.org/browse/TIMOB-3887
            http://docs.appcelerator.com/titanium/3.0/#!/api/Titanium.UI.ImageView-property-autorotate
        ... though it looks like that's not without problems!
    */

    applyRotation: function () {
        var matrix = this.getTransformationMatrix(),
            platform = require('lib/platform'),
            animation;
        Titanium.API.trace("QuestionPhoto.applyRotation: transformation " +
                           "matrix = " + JSON.stringify(matrix));
        if (platform.ios) {
            // works on iOS:
            this.imageView.setAnchorPoint(this.anchor);
            // ... iOS only; docs say to use Titanium.UI.Animation.anchorPoint
            // for Android
            this.imageView.setTransform(matrix);
        } else {
            // Android
            animation = Titanium.UI.createAnimation({
                transform: matrix,
                anchorPoint: this.anchor,
                duration: 1,
                autoreverse: false,
            });
            this.imageView.animate(animation);

            /*
            This worked prior to Jan 2014, and the documented way didn't, but
            now the documented way (above) works.
                this.imageView.setTransform(matrix);
                // ... anchor information is within this
            */
        }
    },

    confirmDelete: function () {
        var dlg = Titanium.UI.createAlertDialog({
                title: L('delete_photo_q'),
                message: L('delete_photo_sure'),
                buttonNames: [L('cancel'), L('delete')],
            }),
            self = this;
        dlg.addEventListener('click', function (ev) {
            if (ev.index === 1) { // Delete
                self.imageView.setImage(null);
                self.blank = true;
                self.questionnaire.setFieldValue(self.field, null);
            }
            dlg = null;
        });
        dlg.show();
    },

    cleanup: function () {
        if (this.takeListener) {
            this.takeButton.removeEventListener('click', this.takeListener);
            this.takeButton = null;
            this.takeListener = null;
        }
        if (this.rotateAnticlockwiseListener) {
            this.rotateAnticlockwiseButton.removeEventListener(
                'click',
                this.rotateAnticlockwiseListener
            );
            this.rotateAnticlockwiseButton = null;
            this.rotateAnticlockwiseListener = null;
        }
        if (this.rotateClockwiseListener) {
            this.rotateClockwiseButton.removeEventListener(
                'click',
                this.rotateClockwiseListener
            );
            this.rotateClockwiseButton = null;
            this.rotateClockwiseListener = null;
        }
        if (this.deleteListener) {
            this.deleteButton.removeEventListener('click',
                                                  this.deleteListener);
            this.deleteButton = null;
            this.deleteListener = null;
        }
        this.imageView.removeEventListener('load', this.loadListener);
        this.loadListener = null;
        this.imageView = null;

        this.wait = null;
    },

});
module.exports = QuestionPhoto;
