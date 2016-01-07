// QuestionHorizontalRule.js
// Simple text display.

/*
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
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

var qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionHorizontalRule(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        tiprops = {};

    qcommon.setDefaultProperty(props, "height", UICONSTANTS.GRID_RULE_HEIGHT);
    qcommon.setDefaultProperty(props, "width", Titanium.UI.FILL);
    qcommon.setDefaultProperty(props, "backgroundColor",
                               UICONSTANTS.GRID_RULE_COLOUR);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    qcommon.copyStandardTiProps(props, tiprops);
    lang.copyProperty(props, tiprops, "backgroundColor");
    this.tiview = Titanium.UI.createView(tiprops);
}
lang.inheritPrototype(QuestionHorizontalRule, qcommon.QuestionElementBase);
// lang.extendPrototype(QuestionHorizontalRule, {});
module.exports = QuestionHorizontalRule;
