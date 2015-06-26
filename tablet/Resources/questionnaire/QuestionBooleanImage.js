// QuestionBooleanImage.js

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
/*global Titanium */

var MODULE_NAME = "QuestionBooleanImage",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionBooleanImage(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        ticksize,
        props_tick,
        props_image,
        image,
        self = this;
    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.requireProperty(props, "image", MODULE_NAME);
    qcommon.setDefaultProperty(props, "indicatorOnLeft", false);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.setDefaultProperty(props, "allowUnsetting", false);
    qcommon.setDefaultProperty(props, "bigTick", false); // for icon
    qcommon.setDefaultProperty(props, "valign", UICONSTANTS.ALIGN_TOP);
    // ... UICONSTANTS.ALIGN_TOP, UICONSTANTS.ALIGN_CENTRE
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    ticksize = (
        props.bigTick ?
                UICONSTANTS.ICONSIZE :
                UICONSTANTS.QUESTIONNAIRE_CHECKMARK_IMAGE_SIZE
    );

    // Tick/cross/blank
    // Image
    props_tick = {
        mandatory: props.mandatory,
        readOnly: props.readOnly,
        red: true,
        setFieldValue: function (newValue) {
            props.questionnaire.setFieldValue(props.field, newValue);
        },
        tiprops: {},
        size: ticksize,
    };
    props_image = {
        image: props.image,
        touchEnabled: true,
    };

    if (props.indicatorOnLeft) {
        props_tick.tiprops.left = 0;
        props_image.left = ticksize;
    } else {
        props_tick.tiprops.right = 0;
        props_image.right = ticksize;
    }
    if (props.valign === UICONSTANTS.ALIGN_TOP) {
        props_tick.tiprops.top = 0;
        props_image.top = 0;
    } else {
        props_tick.tiprops.center = { y: '50%' };
        props_image.center = { y: '50%' };
    }

    this.tick = new qcommon.BooleanWidget(props_tick);
    image = Titanium.UI.createImageView(props_image);

    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.SIZE,
        touchEnabled: true,
        // (1) on iOS, must be true for its constituent parts (image, tick) to
        //     receive events.
        // (2) However, if a click event is set on the view (on iOS), then the
        //     view captures and the button/image don't.
        // So need (a) all to be touch-enabled; (b) events on the components
        // (button/image).
    });
    this.tiview.add(this.tick.tiview);
    this.tiview.add(image);

    // Respond to touches
    if (!props.readOnly) {
        this.clickListener = function () { self.tick.toggle(); };
        this.tiview.addEventListener('click', this.clickListener);
        if (props.allowUnsetting) {
            this.doubleClickListener = function () { self.tick.unset(); };
            this.tiview.addEventListener('dblclick', this.doubleClickListener);
        }
    }
}
lang.inheritPrototype(QuestionBooleanImage, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionBooleanImage, {

    // Mandatory: communication from Questionnaire
    setFromField: function () {
        if (this.field === undefined) {
            return;
        }
        this.tick.setValue(this.questionnaire.getFieldValue(this.field));
    },

    isInputRequired: function () {
        return this.tick.isInputRequired();
    },

    setMandatory: function (mandatory) {
        this.tick.setMandatory(mandatory);
    },

    cleanup: function () {
        if (this.clickListener) {
            this.tiview.removeEventListener("click", this.clickListener);
            this.clickListener = null;
        }
        if (this.doubleClickListener) {
            this.tiview.removeEventListener("click", this.doubleClickListener);
            this.doubleClickListener = null;
        }
        this.tick.cleanup();
        this.tick = null;
    },

});
module.exports = QuestionBooleanImage;
