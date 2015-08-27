// QuestionnaireHeader.js

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

function QuestionnaireHeader(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        GV = require('common/GV'),
        uifunc = require('lib/uifunc'),
        qcommon = require('questionnairelib/qcommon'),
        MODULE_NAME = "QuestionnaireHeader",
        tiprops = {
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL
        },
        exitbutton_left = uifunc.buttonPosition(0),
        readonlyicon_left = uifunc.buttonPosition(1), // may not be used
        title_left = uifunc.buttonPosition(props.readOnly ? 2 : 1),
        nextbutton_right = uifunc.buttonPosition(0),
        backbutton_right = uifunc.buttonPosition(1),
        jumpbutton_right = uifunc.buttonPosition(2), // may not be used
        title_right = uifunc.buttonPosition(props.jumpAllowed ? 3 : 2),
        elemTitle,
        inChainAndNotLast = (GV.inChain &&
                             GV.chainIndex < GV.chainList.length - 1),
        finishIcon = (inChainAndNotLast ?
                UICONSTANTS.ICON_NEXT_IN_CHAIN :
                UICONSTANTS.ICON_FINISH
        ),
        finishIconT = (inChainAndNotLast ?
                UICONSTANTS.ICON_NEXT_IN_CHAIN_T :
                UICONSTANTS.ICON_FINISH_T
        ),
        nextButtonIcon,
        nextButtonIconT;

    qcommon.requireProperty(props, "title", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "fnAbort", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "fnNext", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "fnBack", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "fnJump", MODULE_NAME);
    qcommon.setDefaultProperty(props, "backAllowed", true);
    qcommon.setDefaultProperty(props, "jumpAllowed", false);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "firstQuestion", false);
    qcommon.setDefaultProperty(props, "lastQuestion", false);
    qcommon.setDefaultProperty(props, "okIconAtEnd", false);
    if (props.backgroundColor !== undefined) {
        tiprops.backgroundColor = props.backgroundColor;
    }

    this.tiview = Titanium.UI.createView(tiprops);
    this.exitbutton = uifunc.createCancelButton({left: exitbutton_left});
    this.exitListener = props.fnAbort;
    this.exitbutton.addEventListener('click', this.exitListener);

    elemTitle = Titanium.UI.createLabel({
        left: title_left,
        right: title_right,
        center: {y: '50%'},
        height: Titanium.UI.SIZE,
        font: UICONSTANTS.getQuestionnaireFont(),
        color: UICONSTANTS.QUESTIONNAIRE_TITLE_COLOUR,
        textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
        text: props.title,
        touchEnabled: false
    });

    this.backbutton = uifunc.createBackButton({
        right: backbutton_right,
        visible: (!props.firstQuestion && props.backAllowed)
    });
    this.backListener = props.fnBack;
    this.backbutton.addEventListener('click', this.backListener);

    nextButtonIcon = (props.lastQuestion ?
            (props.okIconAtEnd ? UICONSTANTS.ICON_OK : finishIcon) :
            UICONSTANTS.ICON_NEXT
    );
    nextButtonIconT = (props.lastQuestion ?
            (props.okIconAtEnd ? UICONSTANTS.ICON_OK_T : finishIconT) :
            UICONSTANTS.ICON_NEXT_T
    );
    this.nextbutton = uifunc.createGenericButton(
        nextButtonIcon,
        {
            right: nextbutton_right,
            visible: false
            // the showNext() function should be called to make it visible
        },
        nextButtonIconT
    );
    this.nextListener = props.fnNext;
    this.nextbutton.addEventListener('click', this.nextListener);

    this.tiview.add(this.exitbutton);
    this.tiview.add(elemTitle);
    this.tiview.add(this.backbutton);
    this.tiview.add(this.nextbutton);

    if (props.jumpAllowed) {
        this.jumpbutton = uifunc.createGenericButton(
            UICONSTANTS.ICON_CHOOSE_PAGE,
            {
                right: jumpbutton_right
            },
            UICONSTANTS.ICON_CHOOSE_PAGE_T
        );
        this.jumpListener = props.fnJump;
        this.jumpbutton.addEventListener('click', this.jumpListener);
        this.tiview.add(this.jumpbutton);
    } else {
        this.jumpbutton = null;
        this.jumpListener = null;
    }
    if (props.readOnly) {
        this.tiview.add(Titanium.UI.createImageView({
            image: UICONSTANTS.ICON_READ_ONLY,
            height: UICONSTANTS.ICONSIZE,
            width: UICONSTANTS.ICONSIZE,
            top: 0,
            left: readonlyicon_left,
            touchEnabled: false
        }));
    }
}
QuestionnaireHeader.prototype = {

    showNext: function (show) {
        if (show) {
            this.nextbutton.show();
        } else {
            this.nextbutton.hide();
        }
    },

    cleanup: function () {
        var uifunc = require('lib/uifunc');
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
        this.nextbutton.removeEventListener('click', this.nextListener);
        this.nextbutton = null;
        this.nextListener = null;
        this.backbutton.removeEventListener('click', this.backListener);
        this.backbutton = null;
        this.backListener = null;
        this.exitbutton.removeEventListener('click', this.exitListener);
        this.exitbutton = null;
        this.exitListener = null;
        if (this.jumpListener) {
            this.jumpbutton.removeEventListener('click', this.jumpListener);
            this.jumpbutton = null;
            this.jumpListener = null;
        }
    }

};
module.exports = QuestionnaireHeader;
