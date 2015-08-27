// ChangePasswordWindow.js

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

function ChangePasswordWindow(setPrivilegePassword) {

    var uifunc = require('lib/uifunc'),
        UICONSTANTS = require('common/UICONSTANTS'),
        storedvars = require('table/storedvars'),
        GV = require('common/GV'),
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
            bottom: UICONSTANTS.POPUP_BORDER_SIZE,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            layout: 'vertical',
            backgroundColor: UICONSTANTS.POPUP_BG_COLOUR
        }),
        old_caption = uifunc.createSettingsLabel(
            L(setPrivilegePassword ? 'old_privilegepw' : 'old_unlockpw')
        ),
        caption_1 = uifunc.createSettingsLabel(
            L(setPrivilegePassword ? 'set_privilegepw_1' : 'set_unlockpw_1')
        ),
        caption_2 = uifunc.createSettingsLabel(
            L(setPrivilegePassword ? 'set_privilegepw_2' : 'set_unlockpw_2')
        ),
        self = this,
        buttonview = Titanium.UI.createView({
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            center: {x: '50%'}
        });

    this.tiview = uifunc.createMenuWindow();
    this.setPrivilegePassword = setPrivilegePassword;

    this.wait = uifunc.createEncryptionWait(this.tiview);

    this.oldhashedpw = (setPrivilegePassword ?
            storedvars.privilegePasswordHash.getValue() :
            storedvars.unlockPasswordHash.getValue()
    );
    // Only exemption from entering old password is for a superuser
    // changing the user-mode password... or if there isn't one:
    this.must_enter_old_pw = !(GV.privileged && !setPrivilegePassword);
    if (!this.oldhashedpw) {
        this.must_enter_old_pw = false;
    }

    this.old_pwfield = uifunc.createSettingsEditPassword("",
                                                         L('hint_password'));
    this.pwfield_1 = uifunc.createSettingsEditPassword("",
                                                       L('hint_password'));
    this.pwfield_2 = uifunc.createSettingsEditPassword("",
                                                       L('hint_password'));

    this.okbutton = uifunc.createGenericButton(UICONSTANTS.ICON_OK, {left: 0});
    this.okListener = function () { self.ok(); };
    this.okbutton.addEventListener('click', this.okListener);

    this.moveListener1 = function () { self.pwfield_1.focus(); };
    this.moveListener2 = function () { self.pwfield_2.focus(); };
    this.old_pwfield.addEventListener('return', this.moveListener1);
    this.pwfield_1.addEventListener('return', this.moveListener2);
    this.pwfield_2.addEventListener('return', this.okListener);

    this.cancelbutton = uifunc.createGenericButton(
        UICONSTANTS.ICON_CANCEL,
        {left: UICONSTANTS.ICONSIZE * 2}
    );
    this.cancelListener = function () { self.cancel(); };
    this.cancelbutton.addEventListener('click', this.cancelListener);

    this.openListener = function () { self.reset(); };
    this.tiview.addEventListener('open', this.openListener);
    this.androidBackListener = function () { self.close(); };
    this.tiview.addEventListener('android:back', this.androidBackListener);

    buttonview.add(this.okbutton);
    buttonview.add(this.cancelbutton);

    if (this.must_enter_old_pw) {
        view.add(old_caption);
        view.add(this.old_pwfield);
    }
    view.add(caption_1);
    view.add(this.pwfield_1);
    view.add(caption_2);
    view.add(this.pwfield_2);
    view.add(buttonview);

    borderview.add(view);

    this.tiview.add(transparentview);
    this.tiview.add(borderview);

}
ChangePasswordWindow.prototype = {

    open: function () {
        this.tiview.open();
    },

    close: function () {
        this.tiview.close();
        this.cleanup();
    },

    cleanup: function () {

        this.old_pwfield.removeEventListener('return', this.moveListener1);
        this.moveListener1 = null;
        this.pwfield_1.removeEventListener('return', this.moveListener2);
        this.moveListener2 = null;
        this.pwfield_2.removeEventListener('return', this.okListener);
        this.okbutton.removeEventListener('click', this.okListener);
        this.okListener = null;
        this.okbutton = null;

        this.cancelbutton.removeEventListener('click', this.cancelListener);
        this.cancelListener = null;
        this.cancelbutton = null;

        this.wait = null;

        this.old_pwfield = null;
        this.pwfield_1 = null;
        this.pwfield_2 = null;

        this.tiview.removeEventListener('open', this.openListener);
        this.openListener = null;
        this.tiview.removeEventListener('android:back',
                                        this.androidBackListener);
        this.androidBackListener = null;
        this.tiview = null;
    },

    reset: function () {
        this.old_pwfield.setValue("");
        this.pwfield_1.setValue("");
        this.pwfield_2.setValue("");
        if (this.must_enter_old_pw) {
            this.old_pwfield.focus();
        } else {
            this.pwfield_1.focus();
        }
    },

    ok: function () {
        var uifunc = require('lib/uifunc'),
            rnc_crypto = require('lib/rnc_crypto'),
            storedvars = require('table/storedvars'),
            old_pw_ok = true,
            hash;

        if (this.pwfield_1.value !== this.pwfield_2.value) {
            uifunc.alert(L('passwords_mismatch'), L('change_passwords'));
            this.reset();
            return;
        }
        if (this.pwfield_1.value === "") {
            uifunc.alert(L('passwords_blank'), L('change_passwords'));
            this.reset();
            return;
        }
        // Slow stuff...
        this.wait.show();
        if (this.must_enter_old_pw) {
            old_pw_ok = rnc_crypto.isPasswordValid(this.old_pwfield.value,
                                                   this.oldhashedpw);
        }
        hash = rnc_crypto.hashPassword(this.pwfield_1.value);
        this.wait.hide();
        // Tests
        if (!old_pw_ok) {
            uifunc.alert(L('old_password_wrong'), L('change_passwords'));
            this.reset();
            return;
        }

        // Success...
        if (this.setPrivilegePassword) {
            storedvars.privilegePasswordHash.setValue(hash);
        } else {
            storedvars.unlockPasswordHash.setValue(hash);
        }
        this.tiview.close(); // should call cleanup
    },

    cancel: function () {
        this.close(); // should call cleanup
    }

};
module.exports = ChangePasswordWindow;
