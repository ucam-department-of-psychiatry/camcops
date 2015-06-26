// QuestionThermometer.js
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

/*jslint node: true */
"use strict";
/*global Titanium */

var MODULE_NAME = "QuestionThermometer",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionThermometer(props) {

    var ImageGroupVertical = require('questionnairelib/ImageGroupVertical');
    qcommon.requireProperty(props, "values", MODULE_NAME);
    qcommon.requireProperty(props, "activeImages", MODULE_NAME);
    qcommon.requireProperty(props, "inactiveImages", MODULE_NAME);
    qcommon.requireProperty(props, "text", MODULE_NAME);
    qcommon.requireSameLength(props, "values", "inactiveImages", MODULE_NAME);
    qcommon.requireSameLength(props, "values", "activeImages", MODULE_NAME);
    qcommon.requireSameLength(props, "values", "text", MODULE_NAME);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    // optional property: imageHeight
    // optional property: imageWidth
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.imagegroup = new ImageGroupVertical({
        readOnly: props.readOnly,
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        activeImages: props.activeImages,
        inactiveImages: props.inactiveImages,
        values: props.values,
        text: props.text,
        imageHeight: props.imageHeight,
        imageWidth: props.imageWidth,
        setFieldValue: function (value) {
            props.questionnaire.setFieldValue(props.field, value);
        },
        mandatory: props.mandatory,
    });
    this.tiview = this.imagegroup.tiview;
}
lang.inheritPrototype(QuestionThermometer, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionThermometer, {

    isInputRequired: function () {
        return this.imagegroup.isInputRequired();
    },

    setFromField: function () {
        this.imagegroup.setValue(this.questionnaire.getFieldValue(this.field));
    },

    setMandatory: function (mandatory) {
        this.imagegroup.setMandatory(mandatory);
    },

    cleanup: function () {
        this.imagegroup.cleanup();
        this.imagegroup = null;
    },

});
module.exports = QuestionThermometer;
