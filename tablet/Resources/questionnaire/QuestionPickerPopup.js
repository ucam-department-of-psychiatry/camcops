// QuestionPickerPopup.js

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

/*jslint node: true, plusplus: true, newcap: true */
"use strict";
/*global Titanium, L */

var MODULE_NAME = "QuestionMCQ",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionPickerPopup(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        self = this;
    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.setDefaultProperty(props, "randomize", false);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.setDefaultProperty(
        props,
        "buttonTextWhenNull",
        L("questionpicker_default_button_text_when_null")
    );
    qcommon.setDefaultProperty(
        props,
        "ios7ButtonTextFlankerLeft",
        UICONSTANTS.IOS7_BUTTON_TEXT_FLANKER_LEFT
    );
    qcommon.setDefaultProperty(
        props,
        "ios7ButtonTextFlankerRight",
        UICONSTANTS.IOS7_BUTTON_TEXT_FLANKER_RIGHT
    );
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.buttonTextWhenNull = qcommon.processButtonTextForIos(
        props.buttonTextWhenNull,
        props.ios7ButtonTextFlankerLeft,
        props.ios7ButtonTextFlankerRight
    );

    if (props.randomize) {
        lang.shuffle(props.options);
    }
    this.props = props;

    this.selectedIndex = null;

    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE
    });

    this.indicator = new qcommon.ValidityIndicator({
        size: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE
    });
    this.tiview.add(this.indicator.tiview);

    if (props.readOnly) {
        this.value_as_text = Titanium.UI.createLabel({
            top: 0,
            left: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            font: UICONSTANTS.getQuestionnaireFont(false, true, false), // bold
            color: UICONSTANTS.READONLY_ANSWER_COLOUR,
            text: ""  // will be set later
        });
        this.tiview.add(this.value_as_text);
    } else {
        this.button = Titanium.UI.createButton({
            top: 0,
            left: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            title: "", // will be set later
            color: UICONSTANTS.QUESTIONNAIRE_BUTTON_TEXT_COLOR
        });
        this.tiview.add(this.button);

        this.buttonListener = function () { self.buttonPressed(); };
        this.button.addEventListener('click', this.buttonListener);
    }
}
lang.inheritPrototype(QuestionPickerPopup, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionPickerPopup, {

    getValueAsText: function () {
        if (this.selectedIndex === null) {
            return "";
        }
        return this.props.options[this.selectedIndex].key;
    },

    isInputRequired: function () {
        return this.props.mandatory && this.selectedIndex === null;
    },

    buttonPressed: function () {
        var keys = [],
            i,
            opts,
            self = this;
        for (i = 0; i < this.props.options.length; ++i) {
            keys.push(this.props.options[i].key);
        }
        this.dialog = null; // destroy any old ones; shouldn't be any open as
        // they're meant to be modal
        opts = {
            options: keys,
            cancel: -1  // disable cancel option
        };
        if (this.selectedIndex !== null) {
            opts.selectedIndex = this.selectedIndex;
        }
        this.dialog = Titanium.UI.createOptionDialog(opts);
        this.popupListener = function (e) { self.popupSelected(e); };
        this.dialog.addEventListener("click", this.popupListener);
        this.dialog.show();
    },

    setButtonText: function (text) {
        this.button.setTitle(text);
        this.button.setWidth(Titanium.UI.SIZE);
        this.button.setHeight(Titanium.UI.SIZE);
    },

    popupSelected: function (e) {
        // Titanium.API.trace("QuestionPickerPopup: popupSelected: e = " +
        //                   JSON.stringify(e));
        var index = e.index,
            key,
            value;
        if (index < 0) {
            return; // dialogue cancelled
        }
        this.selectedIndex = index;
        if (this.selectedIndex < 0 ||
                this.selectedIndex >= this.props.options.length) {
            this.selectedIndex = null;
            this.setButtonText(this.buttonTextWhenNull);
        } else {
            key = this.props.options[this.selectedIndex].key;
            value = this.props.options[this.selectedIndex].value;
            this.questionnaire.setFieldValue(this.field, value);
            this.setButtonText(key);
        }
        this.applyMandatory();
    },

    setFromField: function () {
        var value = this.questionnaire.getFieldValue(this.field),
            textvalue;
        this.selectedIndex = lang.kvpGetIndexByValue(this.props.options,
                                                     value);
        textvalue = this.getValueAsText();
        if (this.props.readOnly) {
            this.value_as_text.setText(textvalue);
        } else {
            if (!textvalue) {
                textvalue = this.buttonTextWhenNull;
            }
            this.setButtonText(textvalue);
        }
        this.applyMandatory();
    },

    setMandatory: function () { // any parameters ignored
        this.applyMandatory();
    },

    applyMandatory: function () {
        if (this.isInputRequired()) {
            this.indicator.setRequired();
        } else if (this.selectedIndex === null) {
            this.indicator.setNullButOptional();
        } else {
            this.indicator.clear();
        }
    },

    cleanup: function () {
        if (this.props.readOnly) {
            this.value_as_text = null;
        } else {
            if (this.buttonListener) {
                this.button.removeEventListener("click", this.buttonListener);
                this.buttonListener = null;
            }
            if (this.popupListener) {
                this.dialog.removeEventListener("click", this.popupListener);
                this.popupListener = null;
            }
            this.dialog = null;
            this.indicator.cleanup();
            this.indicator = null;
            this.button = null;
        }
    }

});
module.exports = QuestionPickerPopup;
