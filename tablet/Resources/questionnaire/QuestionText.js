// QuestionText.js
// Simple text display.

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

var MODULE_NAME = "QuestionText",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionText(props) {

    var UICONSTANTS = require('common/UICONSTANTS');
    if (props.text === undefined && props.field === undefined) {
        throw new Error(MODULE_NAME +
                        " created without text OR field property");
    }
    if (props.text !== undefined && props.field !== undefined) {
        throw new Error(MODULE_NAME + " created with text AND field property");
    }
    qcommon.setDefaultProperty(props, "big", false);
    qcommon.setDefaultProperty(props, "bold", false);
    qcommon.setDefaultProperty(props, "italic", false);
    qcommon.setDefaultProperty(props, "warning", false);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    //var debugfunc = require('lib/debugfunc');
    //debugfunc.dumpObject(props, { maxDepth: 1 });

    this.tiview = Titanium.UI.createLabel({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        // left: 0, top: 0, width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,

        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        font: UICONSTANTS.getQuestionnaireFont(props.big, props.bold,
                                               props.italic),
        color: (props.warning ?
                UICONSTANTS.WARNING_COLOUR :
                (props.field === undefined ?
                        UICONSTANTS.QUESTION_COLOUR :
                        UICONSTANTS.READONLY_ANSWER_COLOUR
                )
        ),
        text: (props.field === undefined ? props.text : ""),
        touchEnabled: false
        // backgroundColor: '#FF0000',
    });
}
lang.inheritPrototype(QuestionText, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionText, {

    setFromField: function () {
        if (this.field === undefined) {
            return;
        }
        this.tiview.setText(this.questionnaire.getFieldValue(this.field));
    }

});
module.exports = QuestionText;
