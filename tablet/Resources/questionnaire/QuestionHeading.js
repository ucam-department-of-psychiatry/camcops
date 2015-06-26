// QuestionHeading.js
// Simple text display, with a different background.

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

var MODULE_NAME = "QuestionHeading",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionHeading(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        uifunc = require('lib/uifunc'),
        text;
    qcommon.requireProperty(props, "text", MODULE_NAME);
    qcommon.setDefaultProperty(props, "big", false);
    qcommon.setDefaultProperty(props, "bold", false);
    qcommon.setDefaultProperty(props, "italic", false);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        backgroundColor: UICONSTANTS.QUESTIONNAIRE_HEADING_BG_COLOUR,
        layout: 'vertical',
    });

    text = Titanium.UI.createLabel({
        left: UICONSTANTS.SPACE,
        right: UICONSTANTS.SPACE,
        height: Titanium.UI.SIZE,
        // ... top = SPACE, bottom = SPACE works on Android but goes giant on
        // iOS
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        font: UICONSTANTS.getQuestionnaireFont(props.big, props.bold,
                                               props.italic),
        color: UICONSTANTS.QUESTION_COLOUR,
        text: props.text,
        touchEnabled: false,
    });

    this.tiview.add(uifunc.createVerticalSpacer());
    this.tiview.add(text);
    this.tiview.add(uifunc.createVerticalSpacer());
}
lang.inheritPrototype(QuestionHeading, qcommon.QuestionElementBase);
// lang.extendPrototype(QuestionHeading, {});
module.exports = QuestionHeading;
