// AskUsernamePasswordWindow.js

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

function AskUsernamePasswordWindow(props) {
    // props:
    //      askUsername
    //      captionUsername
    //      hintUsername
    //      captionPassword
    //      hintPassword
    //      showCancel
    //      verifyAgainstHash
    //      hashedPassword
    //      callbackFn: function (username, password, verified,
    //                            cancelled) { ... }

    if (props.showCancel === undefined) { props.showCancel = true; }

    var uifunc = require('lib/uifunc'),
        UICONSTANTS = require('common/UICONSTANTS'),
        transparentview = Titanium.UI.createView({
            width: Titanium.UI.FILL,
            height: Titanium.UI.FILL,
            backgroundColor: UICONSTANTS.POPUP_BORDER_COLOUR,
            opacity: 0.5
        }),
        borderview = Titanium.UI.createView({
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            center: {x: '50%', y: '30%'},
            // towards the top of the screen, as virtual keyboards may be below
            backgroundColor: UICONSTANTS.POPUP_BG_COLOUR
        }),
        view = Titanium.UI.createView({
            left: UICONSTANTS.POPUP_BORDER_SIZE,
            right: UICONSTANTS.POPUP_BORDER_SIZE,
            top: UICONSTANTS.POPUP_BORDER_SIZE,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            layout: 'vertical',
            backgroundColor: UICONSTANTS.POPUP_BG_COLOUR
        }),
        buttonview = Titanium.UI.createView({
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            center: {x: '50%'}
        }),
        self = this;

    this.props = props;
    this.tiview = uifunc.createPasswordPopupWindow();
    this.wait = uifunc.createEncryptionWait(this.tiview);

    this.usernamefield = uifunc.createSettingsEditText("",
                                                       props.hintUsername);
    this.passwordfield = uifunc.createSettingsEditPassword("",
                                                           props.hintPassword);

    this.moveListener = function () { self.passwordfield.focus(); };
    this.usernamefield.addEventListener('return', this.moveListener);

    this.okbutton = uifunc.createGenericButton(UICONSTANTS.ICON_OK, {left: 0});
    this.okListener = function () { self.ok(); };
    this.okbutton.addEventListener('click', this.okListener);

    this.passwordfield.addEventListener('return', this.okListener);

    this.cancelbutton = uifunc.createGenericButton(
        UICONSTANTS.ICON_CANCEL,
        {left: UICONSTANTS.ICONSIZE * 2}
    );
    this.cancelListener = function () { self.cancel(); };
    this.cancelbutton.addEventListener('click', this.cancelListener);

    buttonview.add(this.okbutton);
    if (props.showCancel) {
        buttonview.add(this.cancelbutton);
    }

    if (props.askUsername) {
        view.add(uifunc.createSettingsLabel(props.captionUsername));
        view.add(this.usernamefield);
    }
    view.add(uifunc.createSettingsLabel(props.captionPassword));
    view.add(this.passwordfield);
    view.add(buttonview);

    borderview.add(view);

    this.tiview.add(transparentview);
    this.tiview.add(borderview);

    this.openListener = function () {
        if (self.props.askUsername) {
            self.usernamefield.focus();
        } else {
            self.passwordfield.focus();
        }
    };
    this.tiview.addEventListener('open', this.openListener);
    this.androidBackListener = function () { self.close(); };
    this.tiview.addEventListener('android:back', this.androidBackListener);
}
AskUsernamePasswordWindow.prototype = {

    open: function () {
        this.tiview.open();
    },

    cleanup: function () {
        this.usernamefield.removeEventListener('return', this.moveListener);
        this.moveListener = null;
        this.passwordfield.removeEventListener('return', this.okListener);
        this.okbutton.removeEventListener('click', this.okListener);
        this.okListener = null;
        this.okbutton = null;

        this.cancelbutton.removeEventListener('click', this.cancelListener);
        this.cancelListener = null;
        this.cancelbutton = null;

        this.tiview.removeEventListener('open', this.openListener);
        this.openListener = null;
        this.tiview.removeEventListener('android:back',
                                        this.androidBackListener);
        this.androidBackListener = null;
        this.tiview = null;

        this.usernamefield = null;
        this.passwordfield = null;
        this.wait = null;
    },

    close: function () {
        this.tiview.close();
        this.cleanup();
    },

    cancel: function () {
        this.close();
        this.props.callbackFn(null, null, null, true);
    },

    ok: function () {
        var username = this.usernamefield.value,
            password = this.passwordfield.value,
            verified = false,
            rnc_crypto;
        if (this.props.verifyAgainstHash) {
            rnc_crypto = require('lib/rnc_crypto');
            this.wait.show();
            verified = rnc_crypto.isPasswordValid(password,
                                                  this.props.hashedPassword);
            this.wait.hide();
        }
        this.close();
        // ... should call cleanup (will also destroy window elements)
        this.props.callbackFn(username, password, verified, false);
    }

};
module.exports = AskUsernamePasswordWindow;
