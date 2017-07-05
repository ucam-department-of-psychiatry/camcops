// HelpMenu.js

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

/*jslint node: true, newcap: true */
"use strict";
/*global Titanium, L */

module.exports = function HelpMenu() {

    var MenuWindow = require('menulib/MenuWindow'),
        uifunc = require('lib/uifunc'),
        platform = require('lib/platform'),
        UICONSTANTS = require('common/UICONSTANTS'),
        ALLTASKS = require('common/ALLTASKS'),
        data,
        self;

    function visit_website() {
        Titanium.Platform.openURL(UICONSTANTS.CAMCOPS_URL);
    }

    function missing_tasks() {
        uifunc.showHtml(UICONSTANTS.MISSING_TASKS_HTML, L('t_missing_tasks'));
    }

    /*
    function camcops_html() {
        uifunc.showHtml(UICONSTANTS.CAMCOPS_HTML, L('t_camcops_html'));
    }
    */

    function documentation() {
        Titanium.Platform.openURL(UICONSTANTS.CAMCOPS_URL_DOCS);
    }

    function show_versions() {
        var VERSION = require('common/VERSION'),
            moment = require('lib/moment'),
            sqlite_version = "",
            dbdump;
        if (platform.isDatabaseSupported) {
            dbdump = require('lib/dbdump');
            sqlite_version = dbdump.sqlite_version();
        } else {
            sqlite_version = L('not_supported_on_this_platform');
        }
        uifunc.alert(
            (
                L('camcops_version') + ": " + VERSION.CAMCOPS_VERSION + "\n" +
                L('sqlite_version') + ": " + sqlite_version + "\n" +
                "moment.js version: " + moment.version + "\n" +
                "Titanium version: " + Titanium.version +
                    " (build date " + Titanium.buildDate + ")"
            ),
            L('t_versions')
        );
    }

    function show_id() {
        var DBCONSTANTS = require('common/DBCONSTANTS');
        uifunc.alert(DBCONSTANTS.DEVICE_ID, L('device_id_title'));
    }

    function view_terms_conditions() {
        var storedvars = require('table/storedvars');
        uifunc.alert(L('disclaimer_content'), L('you_agreed_to_terms_at') +
                     " " + storedvars.agreedTermsOfUseAt.getValue());
    }

    function black_white_test() {
        uifunc.showHtml(UICONSTANTS.BLACK_WHITE_TEST_HTML,
                        L('t_black_white_test'));
    }

    function scale_scroll_test() {
        var taskcommon = require('lib/taskcommon'),
            params = {},
            html = taskcommon.loadHtmlSetParams(
                'task_html/scaletest.html',
                params,
                'task_html/scaletest.jsx'
            ),
            EVENT_FROM_WEBVIEW = 'SCALETEST_EVENT_FROM_WEBVIEW',
            window;
        function eventFromWebView(e) {
            Titanium.API.trace("scale_scroll_test: eventFromWebView: " + e.eventType);
            switch (e.eventType) {
            case "test":
                break;
            case "exit":
            case "abort":
                if (window !== null) {
                    window.close();
                    window = null;
                }
                break;
            }
        }
        window = taskcommon.createFullscreenWebviewWindow(
            html,
            EVENT_FROM_WEBVIEW,
            eventFromWebView
        );
        window.open();
        /*
        uifunc.showHtml(html, L('t_scale_scroll_test'), true, true);
        // ... disable bouncing, pass raw HTML
        */
    }

    function sound_test() {
        uifunc.soundTest(self.tiview, UICONSTANTS.SOUND_TEST);
    }

    data = [
        {maintitle: L('t_documentation'), func: documentation },
        {maintitle: L('t_visit_website'), func: visit_website },
        ALLTASKS.TASKLIST.DEMOQUESTIONNAIRE,
        {maintitle: L('t_missing_tasks'), func: missing_tasks },
        {maintitle: L('t_show_versions'), func: show_versions },
        {maintitle: L('t_view_device_id'), func: show_id },
        {maintitle: L('t_view_terms_conditions'), func: view_terms_conditions },
        {maintitle: L('t_black_white_test'), func: black_white_test },
        {maintitle: L('t_scale_scroll_test'), func: scale_scroll_test },
        {maintitle: L('t_sound_test'), func: sound_test }
    ];

    self = new MenuWindow({
        title: L('menutitle_help'),
        icon: UICONSTANTS.ICON_MENU_HELP,
        data: data
    });

    return self;
};
