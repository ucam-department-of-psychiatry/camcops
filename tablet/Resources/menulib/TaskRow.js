// TaskRow.js

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

module.exports = function TaskRow(props) {
    // some of:
    //      taskTitle, patientName, showFinishFlag, finishFlag,
    //      taskSummaryView [a view!], date, isComplete...
    // plus others you'd like...

    props.className = (props.patientName ?
                       (props.taskTitle ? 'rc1_tr' : 'rc2_tr') :
                       (props.taskTitle ? 'rc3_tr' : 'rc4_tr'));
    props.selected = false;
    props.touchEnabled = true;
    props.taskSummaryView.setTouchEnabled(false);

    var UICONSTANTS = require('common/UICONSTANTS'),
        extraColumn = props.patientName || props.taskTitle,
        iconLeft,
        patientLeft,
        patientWidth,
        dateLeft,
        dateWidth,
        contentLeft,
        contentWidth,
        self,
        layout = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL,
            horizontalWrap: false,
            touchEnabled: false
        }),
        spacer = Titanium.UI.createView({
            height: UICONSTANTS.ICONSIZE,
            width: UICONSTANTS.SPACE,
            left: 0,
            center: {y: '50%'},
            touchEnabled: false
        }),
        finishFlagIcon,
        patientLabel,
        taskLabel,
        dateLabel,
        content;

    if (props.showFinishFlag) {
        iconLeft = '0%';
        patientLeft = '10%';
        patientWidth = '10%';
        // ... probably won't be used; only anonymous tasks
        dateLeft = extraColumn ? '20%' : '10%';
        dateWidth = '25%';
        contentLeft = extraColumn ? '45%' : '35%';
        contentWidth = extraColumn ? '55%' : '65%';
    } else {
        iconLeft = '0%'; // unused
        patientLeft = '0%';
        patientWidth = '25%';
        dateLeft = extraColumn ? '25%' : '0%';
        dateWidth = '25%';
        contentLeft = extraColumn ? '50%' : '25%';
        contentWidth = extraColumn ? '50%' : '75%';
    }

    self = Titanium.UI.createTableViewRow(props);

    // Do NOT specify height/width for table rows! They can vanish.
    layout.add(spacer);

    if (props.showFinishFlag && props.finishFlag) {
        finishFlagIcon = Titanium.UI.createImageView({
            image: UICONSTANTS.ICON_FINISHFLAG,
            top: 0,
            height: UICONSTANTS.ICONSIZE,
            width: UICONSTANTS.ICONSIZE,
            left: iconLeft,
            touchEnabled: false
        });
        layout.add(finishFlagIcon);
    }
    if (props.patientName) {
        patientLabel = Titanium.UI.createLabel({
            text: props.patientName,
            font: UICONSTANTS.TASK_PATIENT_FONT,
            color: UICONSTANTS.TASK_PATIENT_COLOUR,
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
            center: {y: '50%'},
            left: patientLeft,
            height: Titanium.UI.SIZE,
            width: patientWidth,
            touchEnabled: false
        });
        layout.add(patientLabel);
    } else if (props.taskTitle) {
        // Used for the patient summary view: only one patient, but we need to
        // know what the tasks are.
        // Use the same constants as for a patient label, except colour:
        taskLabel = Titanium.UI.createLabel({
            text: props.taskTitle,
            font: UICONSTANTS.TASK_PATIENT_FONT,
            color: (
                props.isComplete ?
                        UICONSTANTS.TASK_TITLE_COLOUR_COMPLETE :
                        UICONSTANTS.TASK_TITLE_COLOUR_INCOMPLETE
            ),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
            center: {y: '50%'},
            left: patientLeft,
            height: Titanium.UI.SIZE,
            width: patientWidth,
            touchEnabled: false
        });
        layout.add(taskLabel);
    }

    dateLabel = Titanium.UI.createLabel({
        text: props.date,
        font: UICONSTANTS.TASK_DATE_FONT,
        color: (
            props.isComplete ?
                    UICONSTANTS.TASK_DATE_COLOUR_COMPLETE :
                    UICONSTANTS.TASK_DATE_COLOUR_INCOMPLETE
        ),
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        center: {y: '50%'},
        left: dateLeft,
        height: Titanium.UI.SIZE,
        width: dateWidth,
        touchEnabled: false
    });
    layout.add(dateLabel);

    content = Titanium.UI.createView({
        center: {y: '50%'},
        left: contentLeft,
        height: Titanium.UI.SIZE,
        width: contentWidth,
        touchEnabled: false
    });
    content.add(props.taskSummaryView);
    layout.add(content);

    self.add(layout);

    return self;
};
