// MenuWindow.js

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

function MenuWindow(p) {

    var MenuViewWrapper = require('menulib/MenuViewWrapper'),
        uifunc = require('lib/uifunc'),
        activity,
        self = this;

    // all properties passed to createMenuWindow, MenuView

    this.tiview = uifunc.createMenuWindow(p);
    this.exitOnClose = p.exitOnClose;
    // ... Do not use Titanium.UI.Window's exitOnClose, since keyboard
    // docking/undocking causes a close event.
    this.androidBackListener = function () {
        if (self.exitOnClose) {
            activity = Titanium.Android.currentActivity;
            activity.finish(); // CLOSE THE APP
        } else {
            self.close();
        }
    };
    this.tiview.addEventListener('android:back', this.androidBackListener);

    p.fnBackClicked = function () {
        self.close();
        self = null; // THIS IS THE IMPORTANT BIT to remove memory leaks.
    };

    this.menuview = new MenuViewWrapper(p);
    this.tiview.add(this.menuview.tiview);

    // http://developer.appcelerator.com/question/137094/parasitic-inheritance-and-proxy-objects
}
MenuWindow.prototype = {

    open: function () {
        this.tiview.open();
    },

    close: function () {
        this.tiview.close();
        this.tiview.removeEventListener('android:back',
                                        this.androidBackListener);
        this.androidBackListener = null;
        this.menuview.cleanup();
    }

};
module.exports = MenuWindow;

/*

I am reasonably confident that when an Android tablet undocks from its
keyboard, Titanium windows experience a close() and then an open() call.

Consequently, any window that implements a "close" event listener that
wipes out the window will be wiped out by an undocking event.

*/
