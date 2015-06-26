// ContainerVertical.js

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

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function ContainerVertical(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        i,
        newElement;
    qcommon.requireProperty(props, "elements", "ContainerVertical");
    // ... sub-properties: as for Questionnaire's elements
    qcommon.setDefaultProperty(props, "space", UICONSTANTS.MEDIUMSPACE);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    // View
    this.tiview = Titanium.UI.createView({
        top: props.top,
        left: props.left,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        layout: 'vertical',
    });

    // Iterate through elements property, creating elements
    this.elements = [];
    for (i = 0; i < props.elements.length; ++i) {
        qcommon.setDefaultHorizontalPosLeft(props.elements[i], 0);
        qcommon.setDefaultVerticalPosTop(props.elements[i],
                                         (i > 0 ? props.space : 0));
        newElement = qcommon.makeElement(props.elements[i]);
        this.elements.push(newElement);
        this.tiview.add(newElement.tiview);
    }
}
lang.inheritPrototype(ContainerVertical, qcommon.QuestionElementBase);
// lang.extendPrototype(ContainerVertical, {});
module.exports = ContainerVertical;
