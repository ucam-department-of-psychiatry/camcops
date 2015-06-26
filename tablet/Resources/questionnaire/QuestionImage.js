// QuestionImage.js
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

/*jslint node: true */
"use strict";
/*global Titanium */

// var MODULE_NAME = "QuestionImage";

var qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionImage(props) {

    // some properties passed to Titanium.UI.createImageView
    // other properties:
    //      field
    // other vital properties: see qcommon.copyVitalPropsToSelf

    props.touchEnabled = false;
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    var tiprops = {};
    qcommon.copyStandardTiProps(props, tiprops);
    lang.copyProperty(props, tiprops, "image");
    this.tiview = Titanium.UI.createImageView(tiprops);
}
lang.inheritPrototype(QuestionImage, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionImage, {

    setFromField: function () {
        if (this.field === undefined) {
            return;
        }
        var blob = this.questionnaire.getFieldValue(this.field);
        this.tiview.setImage(blob);
    },

});
module.exports = QuestionImage;
