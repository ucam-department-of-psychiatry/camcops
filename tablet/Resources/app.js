// app.js

/*
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com)
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
/*global Titanium, alert */

function bugtest(bugtestfile) {
    // Plain "include" for bug testing:
    //      http://stackoverflow.com/questions/5797852/
    //      http://stackoverflow.com/questions/5625569/
    //      http://developer.appcelerator.com/question/5481/reading-a-text-file

    var readFile = Titanium.Filesystem.getFile(
            Titanium.Filesystem.resourcesDirectory,
            bugtestfile
        ),
        fileContents = readFile.read().toString(),
        EVAL_IS_EVIL = eval;
    EVAL_IS_EVIL(fileContents);
    // http://stackoverflow.com/questions/13147289
}

function quit() {
    return;
}

function launch_main_menu() {
    var MainMenu = require('menu/MainMenu'),
        rootWindow = new MainMenu();
    rootWindow.open();
}

function agree_to_disclaimer() {
    var storedvars = require('table/storedvars'),
        moment = require('lib/moment'),
        conversion = require('lib/conversion'),
        now = moment(),
        now_string = conversion.momentToString(now);
    storedvars.agreedTermsOfUseAt.setValue(now_string);
    launch_main_menu();
}

function ensure_disclaimer_agreed() {
    var storedvars = require('table/storedvars'),
        DisclaimerWindow,
        win;
    if (storedvars.agreedTermsOfUseAt.getValue()) {
        // Already agreed
        launch_main_menu();
        return;
    }
    DisclaimerWindow = require('screen/DisclaimerWindow');
    win = new DisclaimerWindow(agree_to_disclaimer, quit);
    win.open();
}

function ensure_database_ok() {
    var storedvars,
        ALLTASKS = require('common/ALLTASKS'),
        t;
    Titanium.API.info("Ensuring database is set up and tables exist");

    Titanium.API.info("... storedvars");
    storedvars = require('table/storedvars');
    storedvars.createStoredVariables();

    Titanium.API.info("... dbinit");
    require('lib/dbinit'); // initialize database

    // 9 Mar 2015: was still possible to crash app by using tables that didn't
    // exist. Simplest solution is therefore to ensure all tables are
    // created, always.

    Titanium.API.info("... blob table");
    require('table/Blob');

    Titanium.API.info("... patient table");
    require('table/Patient');

    Titanium.API.info("... all task tables");
    for (t in ALLTASKS.TASKLIST) {
        if (ALLTASKS.TASKLIST.hasOwnProperty(t)) {
            Titanium.API.debug("... ... " + ALLTASKS.TASKLIST[t].task);
            require(ALLTASKS.TASKLIST[t].task);
        }
    }

}

function launch_camcops() {
    Titanium.API.info("CamCOPS: main launch point");
    ensure_database_ok();
    var storedvars = require('table/storedvars'),
        UICONSTANTS = require('common/UICONSTANTS');
    if (storedvars.sendAnalytics.getValue()) {
        // You can disable this if you insist on not sending any analytics back
        // to CamCOPS "base" -- but we'd really appreciate it if you allowed
        // this! See lib/analytics.js for details.
        require('lib/analytics').reportAnalytics();
    }
    Titanium.UI.setBackgroundColor(UICONSTANTS.MENU_BG_COLOUR);
    // ... set the background colour of the master UIView (when there are no
    // windows/tab groups on it)
    ensure_disclaimer_agreed();
}

/*
// Doesn't work - wait is shown only after main menu loads!
function mobileweb_loading_wait() {
    var uifunc = require('lib/uifunc'),
        win = Titanium.UI.createWindow(),
        wait = uifunc.createWait({window: win});
    wait.show();
    win.open();
    launch_camcops();
}
*/

function camcops() {
    Titanium.API.info("CamCOPS starting");
    var floatTitaniumVersion = parseFloat(Titanium.version),
        platform,
        storedvars;
    // Titanium.version can be e.g. "3.0.0"
    Titanium.API.info("Titanium version: " + Titanium.version +
                      " (as float: " + floatTitaniumVersion + ")");

    if (floatTitaniumVersion < 2.0) {
        Titanium.API.error("Titanium version too old");
        alert("Sorry - this application requires Titanium Mobile SDK 2.0" +
              " or later");
        // As of Titanium 3.0.0 (approx.), a "return" statement here fails
    } else {
        Titanium.API.info("Language = " + Titanium.Locale.currentLanguage);
        platform = require('lib/platform');
        if (platform.mobileweb) {
            Titanium.API.trace("Using mobileweb. Asking for server " +
                               "authentication details.");
            storedvars = require('table/storedvars');
            storedvars.askUserForSpecialMobilewebVariables(launch_camcops);
        } else {
            launch_camcops();
        }
    }
}

// bugtest("titanium_bug_testing/bugtest_table_searchbar_android_dock_undock_crash.jsx");
// bugtest("titanium_bug_testing/bugtest_ti_paint.jsx");
// bugtest("titanium_bug_testing/bugtest_listview_search_select.jsx");
// bugtest("titanium_bug_testing/bugtest_ios_layout_speed.jsx");
// bugtest("titanium_bug_testing/bugtest_horizontal_scroll_bigtext.jsx");
// bugtest("titanium_bug_testing/minimalist_app.jsx");
// bugtest("titanium_bug_testing/sqlite_bigint.jsx");
// bugtest("titanium_bug_testing/bugtest_mobileweb_optiondialogclicked.jsx");
// bugtest("titanium_bug_testing/bugtest_mobileweb_tables_with_sections.jsx");
// bugtest("titanium_bug_testing/alert_dialogue_scroll.jsx");
// bugtest("titanium_bug_testing/sqlite_many_accesses.jsx");
// bugtest("titanium_bug_testing/android_dequeuebuffer_crash.jsx");

// bugtest("titanium_bug_testing/test_html_to_attributed_string.jsx");

camcops();
