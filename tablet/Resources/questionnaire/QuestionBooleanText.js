// QuestionBooleanText.js

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

var MODULE_NAME = "QuestionBooleanText",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionBooleanText(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        buttonsize,
        props_button,
        props_text,
        text,
        self = this;
    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.requireProperty(props, "text", MODULE_NAME);
    qcommon.setDefaultProperty(props, "indicatorOnLeft", false);
    qcommon.setDefaultProperty(props, "bigTick", false); // for icon
    qcommon.setDefaultProperty(props, "big", false); // for text
    qcommon.setDefaultProperty(props, "bold", true);
    qcommon.setDefaultProperty(props, "italic", false);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.setDefaultProperty(props, "allowUnsetting", false);
    qcommon.setDefaultProperty(props, "asTextButton", false);
    qcommon.setDefaultProperty(props, "valign", UICONSTANTS.ALIGN_TOP);
    // ... UICONSTANTS.ALIGN_TOP, UICONSTANTS.ALIGN_CENTRE
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    buttonsize = (
        props.bigTick ?
                UICONSTANTS.ICONSIZE :
                UICONSTANTS.QUESTIONNAIRE_CHECKMARK_IMAGE_SIZE
    );

    // Tick/cross/blank
    // Text
    props_button = {
        asTextButton: props.asTextButton,
        mandatory: props.mandatory,
        readOnly: props.readOnly,
        red: true,
        setFieldValue: function (newValue) {
            props.questionnaire.setFieldValue(props.field, newValue);
        },
        text: props.asTextButton ? props.text : "",
        size: buttonsize,
        tiprops: {},
    };
    props_text = {
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        font: UICONSTANTS.getQuestionnaireFont(props.big, props.bold,
                                               props.italic),
        color: UICONSTANTS.QUESTION_COLOUR,
        text: props.text,
        touchEnabled: true,
    };

    if (!props.asTextButton) {
        if (props.indicatorOnLeft) {
            props_button.tiprops.left = 0;
            props_text.left = buttonsize;
        } else {
            props_button.tiprops.right = 0;
            props_text.right = buttonsize;
        }
        if (props.valign === UICONSTANTS.ALIGN_TOP) {
            props_button.tiprops.top = 0;
            props_text.top = 0;
        } else {
            props_button.tiprops.center = { y: '50%' };
            props_text.center = { y: '50%' };
        }
    }

    this.button = new qcommon.BooleanWidget(props_button);
    if (props.asTextButton) {
        this.tiview = this.button.tiview;
    } else {
        this.tiview = Titanium.UI.createView({
            left: props.left,
            right: props.right,
            top: props.top,
            bottom: props.bottom,
            center: props.center,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.SIZE,
            touchEnabled: true, // see comments in QuestionBooleanImage
        });
        this.tiview.add(this.button.tiview);
        text = Titanium.UI.createLabel(props_text);
        this.tiview.add(text);
    }

    // Respond to touches
    if (!props.readOnly) {
        this.clickListener = function () { self.button.toggle(); };
        this.tiview.addEventListener('click', this.clickListener);
        if (props.allowUnsetting) {
            this.doubleClickListener = function () { self.button.unset(); };
            this.tiview.addEventListener('dblclick', this.doubleClickListener);
        }
    }
}
lang.inheritPrototype(QuestionBooleanText, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionBooleanText, {

    // Mandatory: communication from Questionnaire
    setFromField: function () {
        if (this.field === undefined) {
            return;
        }
        this.button.setValue(this.questionnaire.getFieldValue(this.field));
    },

    isInputRequired: function () {
        return this.button.isInputRequired();
    },

    setMandatory: function (mandatory) {
        this.button.setMandatory(mandatory);
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
        this.button.cleanup();
        this.button = null;
        var uifunc = require('lib/uifunc');
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
    },

});
module.exports = QuestionBooleanText;
