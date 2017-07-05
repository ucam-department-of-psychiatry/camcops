// PatientRow.js

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

module.exports = function PatientRow(props) {
    // patientId, patientNameForFilter, firstRowText, secondRowText, finishFlag
    // failsUploadPolicy, failsFinalizePolicy

    props.className = 'rc1_pr'; // only one type of row
    props.selected = false;
    props.touchEnabled = true;

    var UICONSTANTS = require('common/UICONSTANTS'),
        uifunc = require('lib/uifunc'),
        self = Titanium.UI.createTableViewRow(props),
        // Do NOT specify height/width for table rows! They can vanish.
        warningIcon = null,
        iconVerticalLayout,
        icon,
        absentIconSpacer,
        textVerticalLayout,
        primaryLabel,
        secondaryLabel;

    if (props.failsUploadPolicy) {
        warningIcon = UICONSTANTS.ICON_STOP;
    } else if (props.failsFinalizePolicy) {
        warningIcon = UICONSTANTS.ICON_WARNING;
    } else if (props.finishFlag) {
        warningIcon = UICONSTANTS.ICON_FINISHFLAG;
    }

    if (warningIcon !== null) {
        iconVerticalLayout = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            width: UICONSTANTS.ICONSIZE,
            left: UICONSTANTS.SPACE,
            center: {y: '50%'},
            layout: 'vertical',
            touchEnabled: false
        });
        icon = Titanium.UI.createImageView({
            image: warningIcon,
            top: UICONSTANTS.SPACE,
            height: UICONSTANTS.ICONSIZE,
            width: UICONSTANTS.ICONSIZE,
            left: 0,
            touchEnabled: false
        });
        iconVerticalLayout.add(icon);
        iconVerticalLayout.add(uifunc.createVerticalSpacer());
        self.add(iconVerticalLayout);
    } else {
        // Ensure all rows are always as tall as they would be with an icon
        // present
        absentIconSpacer = Titanium.UI.createView({
            height: UICONSTANTS.SPACE * 2 + UICONSTANTS.ICONSIZE,
            width: UICONSTANTS.SPACE,
            left: 0,
            center: {y: '50%'},
            touchEnabled: false
        });
        self.add(absentIconSpacer);
    }

    textVerticalLayout = Titanium.UI.createView({
        height: Titanium.UI.SIZE,
        width: Titanium.UI.FILL,
        left: (2 * UICONSTANTS.SPACE + UICONSTANTS.ICONSIZE),
        center: {y: '50%'},
        layout: 'vertical',
        touchEnabled: false
    });
    primaryLabel = Titanium.UI.createLabel({
        text: props.firstRowText,
        font: UICONSTANTS.PATIENT_ROW1_FONT,
        color: UICONSTANTS.PATIENT_ROW1_COLOUR,
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        top: 0,
        left: 0,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.SIZE,
        touchEnabled: false
    });
    secondaryLabel = Titanium.UI.createLabel({
        text: props.secondRowText,
        font: UICONSTANTS.PATIENT_ROW2_FONT,
        color: UICONSTANTS.PATIENT_ROW2_COLOUR,
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        top: 0,
        left: 0,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.SIZE,
        touchEnabled: false
    });
    textVerticalLayout.add(primaryLabel);
    textVerticalLayout.add(secondaryLabel);

    self.add(textVerticalLayout);

    return self;
};
