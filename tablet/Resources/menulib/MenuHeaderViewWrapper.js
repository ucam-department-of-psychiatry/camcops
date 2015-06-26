// MenuHeaderViewWrapper.js

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

function MenuHeaderViewWrapper(p) {

    if (p.backbutton === undefined) { p.backbutton = true; }
    if (p.icon === undefined) { p.icon = ""; }
    if (p.title === undefined) { p.title = "MISSING TITLE"; }
    if (p.patientline === undefined) { p.patientline = true; }
    // other optional parameters:
    //      subtitle
    //      fnBackClicked: function () { ... }

    var uifunc = require('lib/uifunc'),
        useicon = p.icon.length > 0,
        toprow = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL,
        }),
        next_left = 0,
        icon,
        lockbutton_right = uifunc.buttonPosition(0),
        whisker_right = uifunc.buttonPosition(1),
        centreview_right = uifunc.buttonPosition(2),
        title,
        subtitle,
        textVerticalLayout,
        UICONSTANTS = require('common/UICONSTANTS'),
        EVENTS = require('common/EVENTS'),
        whisker = require('lib/whisker'),
        self = this;

    this.tiview = Titanium.UI.createView({
        height: Titanium.UI.SIZE,
        width: Titanium.UI.FILL,
        layout: 'vertical',
    });

    // TOP ROW: STUFF ON THE LEFT
    if (p.backbutton) {
        this.backButton = uifunc.createBackButton({
            left: uifunc.buttonPosition(next_left++)
        });
        toprow.add(this.backButton);
        if (typeof p.fnBackClicked === "function") {
            this.backListener = p.fnBackClicked;
            this.backButton.addEventListener('click', this.backListener);
        }
    }
    if (useicon) {
        icon = uifunc.createGenericButton(
            p.icon,
            {left: uifunc.buttonPosition(next_left++)}
        );
        toprow.add(icon);
    }

    // TOP ROW: STUFF ON THE RIGHT

    this.lockButton = uifunc.createLockButton({right: lockbutton_right});
    toprow.add(this.lockButton);
    this.unlockButton = uifunc.createUnlockButton({right: lockbutton_right});
    toprow.add(this.unlockButton);
    this.deprivilegeButton = uifunc.createDeprivilegeButton(
        {right: lockbutton_right}
    );
    toprow.add(this.deprivilegeButton);

    this.whiskerIcon = uifunc.createGenericButton(
        UICONSTANTS.ICON_WHISKER,
        {
            right: whisker_right,
            visible: whisker.isConnected(),
            // setting the visible flag at creation is necessary on Android,
            // because the show/hide code doesn't seem to be called at creation
        }
    );
    toprow.add(this.whiskerIcon);

    // TEXT
    if (!p.subtitle) {
        title = uifunc.createMenuTitleText({
            left: uifunc.buttonPosition(next_left++),
            right: centreview_right,
            center: {y: '50%'},
            text: p.title,
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        });
        toprow.add(title);
    } else {
        textVerticalLayout = Titanium.UI.createView({
            left: uifunc.buttonPosition(next_left++),
            right: centreview_right,
            height: Titanium.UI.SIZE,
            center: {y: '50%'},
            layout: 'vertical',
        });
        title = uifunc.createMenuTitleText({
            left: 0,
            right: 0,
            text: p.title,
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        }, true);
        subtitle = uifunc.createMenuSubtitleText({
            left: 0,
            right: 0,
            text: p.subtitle,
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        }, true);
        textVerticalLayout.add(title);
        textVerticalLayout.add(subtitle);
        toprow.add(textVerticalLayout);
    }

    this.tiview.add(toprow);
    this.tiview.add(uifunc.createVerticalSpacer());
    this.tiview.add(uifunc.createMenuRule());
    this.tiview.add(uifunc.createVerticalSpacer());

    this.patientListener = null;
    if (p.patientline) {
        this.patientrow = Titanium.UI.createLabel({
            left: UICONSTANTS.SPACE,
            font: UICONSTANTS.PATIENT_FONT,
        });
        this.tiview.add(this.patientrow);
        this.tiview.add(uifunc.createVerticalSpacer());
        this.set_patient_line();
        this.patientListener = function () { self.set_patient_line(); };
        Titanium.App.addEventListener(EVENTS.PATIENT_CHOSEN,
                                      this.patientListener);
        // ... should have a matching removeEventListener call somewhere
    }
    this.set_patient_lock();
    this.set_whisker_icon();
    this.lockListener = function () { self.set_patient_lock(); };
    this.whiskerListener = function () { self.set_whisker_icon(); };
    Titanium.App.addEventListener(EVENTS.PATIENT_LOCK_CHANGED,
                                  this.lockListener);
    // ... should have a matching removeEventListener call somewhere
    Titanium.App.addEventListener(EVENTS.WHISKER_STATUS_CHANGED,
                                  this.whiskerListener);
    // ... should have a matching removeEventListener call somewhere
}
MenuHeaderViewWrapper.prototype = {

    cleanup: function () {
        // Avoid memory leaks:
        // http://docs.appcelerator.com/titanium/2.0/index.html#!/guide/Managing_Memory_and_Finding_Leaks
        var EVENTS = require('common/EVENTS'),
            uifunc = require('lib/uifunc');
        if (this.patientListener) {
            Titanium.App.removeEventListener(EVENTS.PATIENT_CHOSEN,
                                             this.patientListener);
            this.patientListener = null;
        }
        if (this.lockListener) {
            Titanium.App.removeEventListener(EVENTS.PATIENT_LOCK_CHANGED,
                                             this.lockListener);
            this.lockListener = null;
        }
        if (this.whiskerListener) {
            Titanium.App.removeEventListener(EVENTS.WHISKER_STATUS_CHANGED,
                                             this.whiskerListener);
            this.whiskerListener = null;
        }
        if (this.backListener) {
            this.backButton.removeEventListener('click', this.backListener);
            this.backListener = null;
        }
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
        this.patientrow = null;
        this.lockButton = null;
        this.unlockButton = null;
        this.deprivilegeButton = null;
        this.whiskerIcon = null;
    },

    set_patient_line: function () {
        var uifunc = require('lib/uifunc');
        uifunc.setPatientLine(this.patientrow);
    },

    set_patient_lock: function () {
        var uifunc = require('lib/uifunc');
        uifunc.setLockButtons(this.lockButton, this.unlockButton,
                              this.deprivilegeButton);
    },

    set_whisker_icon: function () {
        var whisker = require('lib/whisker'),
            connected = whisker.isConnected();
        if (connected) {
            this.whiskerIcon.show();
        } else {
            this.whiskerIcon.hide();
        }
    }

};
module.exports = MenuHeaderViewWrapper;
