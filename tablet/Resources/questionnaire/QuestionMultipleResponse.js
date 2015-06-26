// QuestionMultipleResponse.js

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

/*jslint node: true, newcap: true, plusplus: true */
"use strict";
/*global Titanium, L */

var MODULE_NAME = "QuestionMultipleResponse";

var qcommon = require('questionnairelib/qcommon');
var lang = require('lib/lang');

function getDefaultInstruction(min_answers, max_answers) {
    if (min_answers === max_answers) {
        return L('pick') + " " + min_answers + ":";
    }
    if (min_answers <= 0) {
        return L('pick') + " " + L('up_to') + " " + max_answers + ":";
    }
    if (max_answers <= 0) {
        return L('pick') + " " + min_answers + L('or_more') + ":";
    }
    return (L('pick') + " " + L('from') + " " + min_answers + " " +
            L('to') + " " + max_answers + ":");
}

function QuestionMultipleResponse(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        MultiCheckVertical = require('questionnairelib/MultiCheckVertical'),
        KeyValuePair = require('lib/KeyValuePair'),
        optionFieldMap = [],
        i,
        instruction,
        elemInstruction;
    qcommon.requireProperty(props, "fields", MODULE_NAME);
    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.requireSameLength(props, "fields", "options", MODULE_NAME);
    qcommon.setDefaultProperty(props, "min_answers", 0);
    qcommon.setDefaultProperty(props, "max_answers", props.options.length);
    qcommon.setDefaultProperty(props, "randomize", false);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "showInstruction", true);
    qcommon.setDefaultProperty(props, "instruction", "");
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.setDefaultProperty(props, "asTextButton", false);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    if (props.min_answers > props.max_answers ||
            props.min_answers < 0 ||
            props.max_answers < 0) {
        throw new Error("Invalid possible options given to " +
                        "QuestionMultipleResponse");
    }

    for (i = 0; i < props.options.length; ++i) {
        optionFieldMap.push(new KeyValuePair(props.options[i],
                                             props.fields[i]));
    }
    if (props.randomize) {
        lang.shuffle(props.optionFieldMap);
    }

    this.fields = props.fields;
    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        layout: 'vertical',
    });

    if (props.showInstruction) {
        instruction = props.instruction || getDefaultInstruction(
            props.min_answers,
            props.max_answers
        );
        elemInstruction = Titanium.UI.createLabel({
            left: 0,
            top: 0,
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
            font: UICONSTANTS.getQuestionnaireFont(),
            color: UICONSTANTS.INSTRUCTION_COLOUR,
            text: instruction,
            touchEnabled: false,
        });
        this.tiview.add(elemInstruction);
    }

    this.elemOptions = new MultiCheckVertical({
        readOnly: props.readOnly,
        asTextButton: props.asTextButton,
        tiprops: {
            left: 0,
            top: 0,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL,
        },
        optionFieldMap: optionFieldMap,
        min: props.min_answers,
        max: props.max_answers,
        setFieldValue: function (field, booleanValue) {
            var value = booleanValue ? 1 : 0;
            // RETURN INTEGERS or something will try to write the value "false"
            // as a string to an SQLite integer field - later to be interpreted
            // as true!
            props.questionnaire.setFieldValue(field, value);
        },
        mandatory: props.mandatory,
    });
    this.tiview.add(this.elemOptions.tiview);

}
lang.inheritPrototype(QuestionMultipleResponse, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionMultipleResponse, {

    isInputRequired: function () {
        return this.elemOptions.isInputRequired();
    },

    setFromField: function () {
        var i,
            field,
            value;
        for (i = 0; i < this.fields.length; ++i) {
            field = this.fields[i];
            value = this.questionnaire.getFieldValue(field);
            this.elemOptions.setFieldToValue(field, value);
        }
    },

    setMandatory: function (mandatory) {
        this.elemOptions.setMandatory(mandatory);
    },

    cleanup: function () {
        this.elemOptions.cleanup();
        this.elemOptions = null;
    },

});
module.exports = QuestionMultipleResponse;
