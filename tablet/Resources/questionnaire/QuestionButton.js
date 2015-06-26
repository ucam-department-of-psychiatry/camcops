// QuestionButton.js

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

var MODULE_NAME = "QuestionButton",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionButton(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        buttonText;
    qcommon.requireProperty(props, "text", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "fnClicked", MODULE_NAME);
    qcommon.setDefaultProperty(props, "inactive", false);
    qcommon.setDefaultProperty(props, "ios7ButtonTextFlankerLeft",
                               UICONSTANTS.IOS7_BUTTON_TEXT_FLANKER_LEFT);
    qcommon.setDefaultProperty(props, "ios7ButtonTextFlankerRight",
                               UICONSTANTS.IOS7_BUTTON_TEXT_FLANKER_RIGHT);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    buttonText = qcommon.processButtonTextForIos(
        props.text,
        props.ios7ButtonTextFlankerLeft,
        props.ios7ButtonTextFlankerRight
    );

    this.tiview = Titanium.UI.createButton({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE,
        title: buttonText,
        color: (
            (props.readOnly || props.inactive) ?
                    UICONSTANTS.QUESTIONNAIRE_READONLY_BUTTON_TEXT_COLOR :
                    UICONSTANTS.QUESTIONNAIRE_BUTTON_TEXT_COLOR
        ),
    });
    if (!props.readOnly && !props.inactive) {
        this.clickListener = function () { props.fnClicked(); };
        this.tiview.addEventListener('click', this.clickListener);
    }
}
lang.inheritPrototype(QuestionButton, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionButton, {

    cleanup: function () {
        if (this.clickListener) {
            this.tiview.removeEventListener("click", this.clickListener);
            this.clickListener = null;
        }
    },

});
module.exports = QuestionButton;
