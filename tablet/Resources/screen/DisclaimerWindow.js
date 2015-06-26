// DisclaimerWindow.js

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

/*jslint node: true, newcap: true */
"use strict";
/*global Titanium, L */

function DisclaimerWindow(fnAgree) { // second param fnDisagree ignored

    var COLOURS = require('common/COLOURS'),
        UICONSTANTS = require('common/UICONSTANTS'),
        self = this,
        windowprops = {
            backgroundColor: COLOURS.WHITE,
            navBarHidden: true, // removes the top line
        },
        platform = require('lib/platform'),
        view = Titanium.UI.createScrollView({
            left: UICONSTANTS.POPUP_BORDER_SIZE,
            right: UICONSTANTS.POPUP_BORDER_SIZE,
            top: UICONSTANTS.POPUP_BORDER_SIZE,
            bottom: UICONSTANTS.POPUP_BORDER_SIZE,
            layout: 'vertical',
            contentHeight: 'auto',
            scrollType: 'vertical',
            showVerticalScrollIndicator: true,
        });

    if (platform.ios7plus) {
        windowprops.fullscreen = true;
        // for iOS 7, or transparent status bar visible
    }
    Titanium.API.trace("windowprops: " + JSON.stringify(windowprops));
    this.tiview = Titanium.UI.createWindow(windowprops);

    view.add(Titanium.UI.createLabel({
        text: L('disclaimer_title'),
        top: UICONSTANTS.SPACE,
        left: 0,
        right: 0,
        font: UICONSTANTS.EDITING_INFO_FONT,
        color: COLOURS.BLACK,
    }));

    view.add(Titanium.UI.createLabel({
        text: L('disclaimer_subtitle'),
        top: UICONSTANTS.SPACE,
        left: 0,
        right: 0,
        font: UICONSTANTS.EDITING_INFO_FONT,
        color: COLOURS.RED,
    }));

    view.add(Titanium.UI.createLabel({
        text: L('disclaimer_content'),
        top: UICONSTANTS.SPACE,
        left: 0,
        right: 0,
        font: UICONSTANTS.EDITING_LABEL_FONT,
        color: COLOURS.BLACK,
    }));

    this.yesButton = Titanium.UI.createButton({
        top: UICONSTANTS.SPACE,
        center: {x: '50%'},
        title: L('disclaimer_agree'),
        color: COLOURS.BLUE,
    });
    this.yesListener = function () {
        fnAgree();
        self.close();
    };
    this.yesButton.addEventListener('click', this.yesListener);
    view.add(this.yesButton);

    /*
    this.noButton = Titanium.UI.createButton({
        top: UICONSTANTS.SPACE,
        title: L('disclaimer_do_not_agree'),
        color: COLOURS.RED,
    });
    this.noListener = function () {
        fnDisagree();
        self.close();
    };
    this.noButton.addEventListener('click', this.noListener);
    view.add(this.noButton);
    */

    this.tiview.add(view);

}
DisclaimerWindow.prototype = {

    open: function () {
        this.tiview.open();
    },

    close: function () {
        this.tiview.close();
        this.yesButton.removeEventListener('click', this.yesListener);
        this.yesListener = null;
        /*
        this.noButton.removeEventListener('click', this.noListener);
        this.noListener = null;
        */
    },

};
module.exports = DisclaimerWindow;
