// SettingsMenu.js

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

/*jslint node: true, newcap: true, unparam: true, plusplus: true */
"use strict";
/*global Titanium, L */

module.exports = function SettingsMenu() {

    var MenuWindow = require('menulib/MenuWindow'),
        uifunc = require('lib/uifunc'),
        platform = require('lib/platform'),
        UICONSTANTS = require('common/UICONSTANTS'),
        data,
        self,
        wait;

    function set_user_password() {
        wait.show();
        var ChangePasswordWindow = require('screen/ChangePasswordWindow'),
            win = new ChangePasswordWindow(false);
        win.open();
        wait.hide();
    }

    function set_privileged_password() {
        wait.show();
        var ChangePasswordWindow = require('screen/ChangePasswordWindow'),
            win = new ChangePasswordWindow(true);
        win.open();
        wait.hide();
    }

    function dump_view() {
        wait.show();
        Titanium.API.trace("--- Database dump");
        var dbdump = require('lib/dbdump'),
            dump = dbdump.dump();
        uifunc.alert(dump, L('db_dump_title'));
        wait.hide();
    }

    function dump_usb() {
        wait.show();
        Titanium.API.trace("--- Database dump");
        var dbdump = require('lib/dbdump'),
            dump = dbdump.dump(),
            lines = dump.split("\n"),
            i;
        Titanium.API.info("Database SQL:");
        // Android: will truncate very long lines. So:
        for (i = 0; i < lines.length; ++i) {
            Titanium.API.info(lines[i]);
        }
        uifunc.alert(L('db_dumped_to_usb'), L('db_dump_title'));
        wait.hide();
    }

    function dump_file() {
        if (!Titanium.Filesystem.isExternalStoragePresent()) {
            uifunc.alert(L('no_external_storage'), L('t_dump_sql_file'));
            return;
        }
        var dlg = Titanium.UI.createAlertDialog({
            title: L('export_title'),
            message: L('export_sure'),
            buttonNames: [L('cancel'), L('save')]
        });
        dlg.addEventListener('click', function (e) {
            if (e.index === 1) { // Save
                wait.show();
                var filename = (
                        Titanium.Filesystem.getExternalStorageDirectory() +
                        Titanium.Filesystem.getSeparator() +  "camcops_db.txt"
                    ),
                    // This tends to look like appdata:///camcops_db.txt, and ends
                    // up in e.g. /sdcard/org.camcops.camcops/camcops_db.txt
                    dbdump = require('lib/dbdump'),
                    file = Titanium.Filesystem.getFile(filename);
                file.write(dbdump.dump());
                wait.hide();
                uifunc.alert(L('database_written_to') + " " + filename,
                             L('t_dump_sql_file'));
                // http://developer.appcelerator.com/question/116587/opensaveasdialog---option-defaultfile-doesnt-work
                // http://developer.appcelerator.com/question/44701/save-as-vs-save
                // http://developer.appcelerator.com/question/3041/be-honest--when-are-the-docs-going-to-be-complete
                // https://github.com/appcelerator/titanium_desktop/blob/master/apidoc/Titanium/UI/UserWindow/openSaveAsDialog.yml
                // ... Titanium.UI.currentWindow.openSaveAsDialog
                // ... looks like the dialogues are/were part of Titanium
                //     Desktop, now defunct
                // https://gist.github.com/283026
            }
            dlg = null;
        });
        dlg.show();
    }

    function configure_server() {
        var conf_server = require('screen/configure_server');
        conf_server.configure();
    }

    function configure_user() {
        var conf_user = require('screen/configure_user');
        conf_user.configure();
    }

    function configure_ip() {
        var conf_ip = require('screen/configure_ip');
        conf_ip.configure();
    }

    function server_info() {
        var show_server_info = require('screen/show_server_info');
        show_server_info.configure();
    }

    function set_privilege() {
        var storedvars = require('table/storedvars'),
            hashedpw = storedvars.privilegePasswordHash.getValue(),
            AskUsernamePasswordWindow,
            win;
        if (!hashedpw) {
            // no security
            uifunc.setPrivilege();
        } else {
            AskUsernamePasswordWindow = require(
                'screen/AskUsernamePasswordWindow'
            );
            win = new AskUsernamePasswordWindow({
                askUsername: false,
                captionPassword: L("enter_privilege_password"),
                hintPassword: L('hint_password'),
                showCancel: true,
                verifyAgainstHash: true,
                hashedPassword: hashedpw,
                callbackFn: function (username, password, verified,
                                      cancelled) {
                    if (cancelled) {
                        return;
                    }
                    if (verified) {
                        uifunc.setPrivilege();
                    } else {
                        uifunc.alert(L('wrong_password'), L('set_privilege'));
                    }
                }
            });
            win.open();
        }
    }

    function fetch_id_descriptions_main() {
        var dbupload = require('lib/dbupload');
        dbupload.fetch_id_descriptions(self.tiview);
    }

    function fetch_id_descriptions() {
        var netcore = require('lib/netcore');
        netcore.setTempServerPasswordAndCall(fetch_id_descriptions_main);
    }

    function fetch_extrastrings_main() {
        var dbupload = require('lib/dbupload');
        dbupload.fetch_extrastrings(self.tiview);
    }

    function fetch_extrastrings() {
        var netcore = require('lib/netcore');
        netcore.setTempServerPasswordAndCall(fetch_extrastrings_main);
    }

    function wipe_extrastrings() {
        var extrastrings = require('table/extrastrings');
        Titanium.API.trace("--- Wiping extra strings");
        extrastrings.delete_all_strings();
        uifunc.alert(L('extrastrings_wiped'), L('t_extrastrings_wiped'));
    }

    function register_device_main() {
        var dbupload = require('lib/dbupload');
        dbupload.register(self.tiview);
    }

    function register_device() {
        var netcore = require('lib/netcore');
        netcore.setTempServerPasswordAndCall(register_device_main);
    }

    function unit_test() {
        wait.show();
        var unittest = require('unittest/unittest');
        unittest.unittest();
        wait.hide();
        uifunc.alert(L('unit_tests_complete'), L('unit_tests_complete'));
    }

    data = [
        {
            notIfLocked: true,
            maintitle: L('t_configure_questionnaire'),
            window: 'screen/ConfigureQuestionnaireWindow'
        },
        {
            notIfLocked: true,
            maintitle: L('t_configure_user'),
            func: configure_user
        },
        {
            notIfLocked: true,
            maintitle: L('t_configure_ip'),
            func: configure_ip
        },
        {
            notIfLocked: true,
            maintitle: L('t_set_user_password'),
            func: set_user_password
        },
        {
            notIfLocked: true,
            maintitle: L('t_server_info'),
            func: server_info
        },
        {
            notIfLocked: true,
            maintitle: L('t_fetch_id_descriptions'),
            func: fetch_id_descriptions
        },
        {
            notIfLocked: true,
            maintitle: L('t_fetch_extrastrings'),
            func: fetch_extrastrings
        },
        {
            notIfLocked: true,
            maintitle: L('menutitle_whisker'),
            arrowOnRight: true,
            icon: UICONSTANTS.ICON_WHISKER,
            window: 'menu/WhiskerMenu'
        },
        {
            notIfLocked: true,
            maintitle: L('t_set_privilege'),
            icon: UICONSTANTS.ICON_PRIVILEGED,
            func: set_privilege
        },
        // ====================================================================
        // PRIVILEGED FUNCTIONS BELOW HERE
        // ====================================================================
        {
            notIfLocked: true,
            maintitle: L('t_configure_server'),
            func: configure_server,
            needsPrivilege: true
        },
        {
            notIfLocked: true,
            maintitle: L('t_register_device'),
            func: register_device,
            needsPrivilege: true
        },
        {
            notIfLocked: true,
            maintitle: L('t_set_privileged_password'),
            func: set_privileged_password,
            needsPrivilege: true
        },
        {
            notIfLocked: true,
            maintitle: L('t_wipe_extrastrings'),
            func: wipe_extrastrings,
            needsPrivilege: true
        },
        {
            notIfLocked: true,
            maintitle: L('t_dump_sql_view'),
            func: dump_view,
            needsPrivilege: true,
            unsupported: (!platform.isDatabaseSupported)
        },
        {
            notIfLocked: true,
            maintitle: L('t_dump_sql_usb'),
            func: dump_usb,
            needsPrivilege: true,
            unsupported: (!platform.isDatabaseSupported)
        },
        {
            notIfLocked: true,
            maintitle: L('t_dump_sql_file'),
            func: dump_file,
            needsPrivilege: true,
            unsupported: (!platform.isDatabaseSupported ||
                          !platform.isFileExportSupported)
        },
        {
            notIfLocked: true,
            maintitle: L('t_unit_test'),
            func: unit_test,
            needsPrivilege: true
        }
    ];

    self = new MenuWindow({
        title: L('menutitle_settings'),
        icon: UICONSTANTS.ICON_MENU_SETTINGS,
        data: data
    });

    wait = uifunc.createWait({ window: self.tiview });

    return self;
};
