// QuestionMCQ.js
// One-from-many.

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

var MODULE_NAME = "QuestionMCQ",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionMCQ(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        RadioGroup = require('questionnairelib/RadioGroup'),
        elemInstruction;

    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.setDefaultProperty(props, "randomize", false);
    qcommon.setDefaultProperty(props, "showInstruction", true);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "horizontal", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.setDefaultProperty(props, "asTextButton", false);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    if (props.randomize) {
        lang.shuffle(props.options);
    }

    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        layout: 'vertical'
    });

    if (props.showInstruction) {
        elemInstruction = Titanium.UI.createLabel({
            left: 0,
            top: 0,
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
            font: UICONSTANTS.getQuestionnaireFont(),
            color: UICONSTANTS.INSTRUCTION_COLOUR,
            text: L('pick') + " 1:",
            touchEnabled: false
        });
        this.tiview.add(elemInstruction);
    }

    this.elemOptions = new RadioGroup({
        readOnly: props.readOnly,
        options: props.options,
        horizontal: props.horizontal,
        asTextButton: props.asTextButton,
        mandatory: props.mandatory,
        setFieldValue: function (value) {
            props.questionnaire.setFieldValue(props.field, value);
        }
    });
    this.tiview.add(this.elemOptions.tiview);
}
lang.inheritPrototype(QuestionMCQ, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionMCQ, {

    isInputRequired: function () {
        return this.elemOptions.isInputRequired();
    },

    setFromField: function () {
        var value = this.questionnaire.getFieldValue(this.field);
        //Titanium.API.trace("QuestionMCQ.setFromField: field = " + this.field +
        //                   ", value = " + value);
        this.elemOptions.setValue(value);
    },

    setMandatory: function (mandatory) {
        this.elemOptions.setMandatory(mandatory);
    },

    cleanup: function () {
        this.elemOptions.cleanup();
        this.elemOptions = null;
    }

});
module.exports = QuestionMCQ;
