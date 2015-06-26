// MenuTableViewWrapper.js

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

/*jslint node: true, plusplus: true, newcap: true */
"use strict";
/*global Titanium, L */

function MenuTableViewWrapper(data) {
    // data: array of properties, each passed to MenuTableRow

    var UICONSTANTS = require('common/UICONSTANTS'),
        MenuTableRow = require('menulib/MenuTableRow'),
        uifunc = require('lib/uifunc'),
        tbldata = [],
        i,
        self = this;

    for (i = 0; i < data.length; ++i) {
        // data[i].row_index = i;
        // ... to compensate for Titanium TableView bug; see below
        tbldata.push(new MenuTableRow(data[i]));
    }
    // debugfunc.traceTiming("+++ MenuTableView(): rows inserted into "
    //                       "tbldata[]");
    // create table view:
    //      https://wiki.appcelerator.org/display/guides/TableViews
    this.tiview = Titanium.UI.createTableView({
        height: Titanium.UI.FILL, // was SIZE, but on iOS this made it
        // scroll-bounce back and you couldn't get to the end
        width: Titanium.UI.FILL,
        data: tbldata,
        separatorColor: UICONSTANTS.MENU_SEPARATOR_COLOUR,
        minRowHeight: UICONSTANTS.MIN_TABLE_ROW_HEIGHT,
        backgroundColor: UICONSTANTS.MENU_BG_COLOUR,
        // backgroundSelectedColor: UICONSTANTS.TABLE_BG_SELECTED_COLOUR,
    });
    this.wait = uifunc.createWait({ window: this.tiview });

    // create table view event listener
    this.clickListener = function (e) { self.clicked(e); };
    this.tiview.addEventListener('click', this.clickListener);
    this.taskFinishedListener = null;

    // If you add to the rowData stuff that's checked, the field(s) need to be
    // copied in the MenuTableRow creation process too.
}
MenuTableViewWrapper.prototype = {

    cleanup: function () {
        var uifunc = require('lib/uifunc');
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview.removeEventListener('click', this.clickListener);
        this.clickListener = null;
        this.tiview = null;
        this.wait = null;
        this.deregister_chain_handler();
    },

    clicked: function (e) {
        var uifunc = require('lib/uifunc'),
            GV = require('common/GV'),
            // row_index = e.source.row_index; // for when we're compensating
            // with a custom row_index property of all rows and members of rows
            row_index = e.index, // raw
            r,
            modulewinclass,
            win,
            TaskSelectorWindow;

        // IF YOU READ VARIABLES HERE, MAKE SURE YOU COPIED THEM IN
        //      MenuTableRow
        // e contains, amongst others: index, row, rowData

        /*
            We're getting some oddness... the appearance of non-rows being
            clicked?
            tableview selection bug:
            https://jira.appcelerator.org/browse/TIMOB-8802
                row and rowData don't match
                my example: touch "Choose patient";
                e.source and e.row contain "Choose patient";
                e.rowData contains "menu/AddictionMenu" etc.
            AWAIT TITANIUM 2.2; fixed there.
            --- Titanium v2.1 bug: rowData can be wrong. Manifestation: looks
            like the last row is clicked. We'll try "row" instead of rowData

            Experimenting: e.index, e.row, and e.rowData can all refer to the
            wrong row (e.g. 2 rows down from that clicked).
            The only thing that looks correct is e.source (e.g. e.source.text).
            So let's implement a row_index member for everything.
            COMPENSATE FOR TABLEVIEW BUG WITH CUSTOM row_index PROPERTY OF ALL
            ROWS/MEMBERS OF ROWS
        */

        Titanium.API.info("MenuTableView/click: row index=" + row_index);
        if (row_index === undefined || row_index === null) {
            return;
        }
        // r = tbldata[row_index]; // should really be e.rowData
        r = e.rowData; // this is what Titanium advertises

        if (r === undefined || r === null) {
            Titanium.API.trace("MenuTableView: undefined/null row selected");
        } else if (r.notImplemented) {
            uifunc.alert(L('not_implemented_yet'), r.maintitle);
        } else if (r.unsupported) {
            uifunc.alert(L('not_supported_on_this_platform'), r.maintitle);
        } else if (r.needsPrivilege && !GV.privileged) {
            uifunc.alert(L('needs_privilege'), r.maintitle);
        } else if (r.notIfLocked && GV.patient_locked) {
            uifunc.notWhenLocked();
        } else if (r.window) {
            this.wait.show();
            modulewinclass = require(r.window);
            win = new modulewinclass();
            win.open(); // {animated:true}
            this.wait.hide();
        } else if (r.event) {
            // http://developer.appcelerator.com/question/66291/how-to-pass-parameters-from-tableview-to-another-view
            Titanium.API.trace("MenuTableView/click: fireEvent " + r.event);
            Titanium.App.fireEvent(r.event, {rowdata: r});
        } else if (r.func) {
            Titanium.API.trace("MenuTableView/click: call function");
            r.func();
        } else if (r.task) {
            this.wait.show();
            TaskSelectorWindow = require('screen/TaskSelectorWindow');
            new TaskSelectorWindow(r.task, r.maintitle, r.info).open();
            this.wait.hide();
        } else if (r.html) {
            uifunc.showHtml(r.html, r.maintitle);
        } else if (r.chain) {
            Titanium.API.trace("MenuTableView/click: run chain");
            this.start_chain(r.chainList);
        } else if (r.labelOnly) {
            // do nothing
            Titanium.API.trace("Label-only row touched; ignored");
        }
    },

    start_chain: function (chainList) {
        Titanium.API.trace("MenuTableViewWrapper.start_chain");
        var GV = require('common/GV'),
            uifunc = require('lib/uifunc'),
            i,
            taskclass,
            task,
            anonymous,
            permitted;

        // validate chain
        for (i = 0; i < chainList.length; ++i) {
            taskclass = require(chainList[i].task);
            task = new taskclass();
            anonymous = task.isAnonymous();
            permitted = task.isTaskPermissible();
            // Is each task permissible?
            if (!permitted) {
                uifunc.ipFail(task);
                return;
            }
            // If the task is not anonymous, do we have a patient?
            if (!anonymous && GV.selected_patient_id === null) {
                uifunc.alert(L('no_patient_selected'), L('cannot_run_task'));
                return;
            }
        }

        // begin the chain
        this.register_chain_handler();
        GV.inChain = true;
        GV.chainList = chainList;
        GV.chainIndex = 0;
        GV.chainTablenames = [];
        GV.chainIds = [];
        for (i = 0; i < chainList.length; ++i) {
            GV.chainTablenames[i] = null;
            GV.chainIds[i] = null;
        }
        this.wait.show();
        this.launch_next_in_chain();
    },

    launch_next_in_chain: function () {
        Titanium.API.trace("MenuTableViewWrapper.launch_next_in_chain");
        this.debug_chain();
        var GV = require('common/GV'),
            taskclass = require(GV.chainList[GV.chainIndex].task),
            task = new taskclass(GV.selected_patient_id);
        // ... parameter will be ignored by anonymous tasks
        task.edit(); // may fire EVENTS.TASK_FINISHED
    },

    task_finished: function (e) {
        // called when each task in the chain finishes
        Titanium.API.trace("MenuTableViewWrapper.task_finished");
        this.debug_chain();
        //Titanium.API.trace("MenuTableViewWrapper.task_finished: e = " +
        //                   JSON.stringify(e));
        var GV = require('common/GV'),
            UICONSTANTS = require('common/UICONSTANTS');
        if (!GV.inChain) {
            return;
            // this only handles chains (plain task ending is handled
            // by TaskWindowCommon
        }
        GV.chainTablenames[GV.chainIndex] = e.tablename;
        GV.chainIds[GV.chainIndex] = e.id;
        if (e.result === UICONSTANTS.FINISHED ||
                e.result === UICONSTANTS.READONLYVIEWFINISHED) {
            GV.chainIndex += 1;
            if (GV.chainIndex >= GV.chainList.length) {
                this.chain_finished();
            } else {
                this.launch_next_in_chain();
            }
        } else if (e.result === UICONSTANTS.ABORTED) {
            this.chain_finished();
        } else {
            Titanium.API.trace("MenuTableViewWrapper.task_finished: " +
                               "unexpected e.result code " + e.result);
            this.wait.hide();
        }
    },

    chain_finished: function () {
        Titanium.API.trace("MenuTableViewWrapper.chain_finished");
        this.debug_chain();
        var uifunc = require('lib/uifunc');

        this.deregister_chain_handler();
        this.reset_gv_chain();
        this.wait.hide();
        uifunc.task_finished_offer_upload(this.tiview);
    },

    register_chain_handler: function () {
        var EVENTS = require('common/EVENTS'),
            self = this;
        this.taskFinishedListener = function (e) { self.task_finished(e); };
        Titanium.App.addEventListener(EVENTS.TASK_FINISHED,
                                      this.taskFinishedListener);
        // ... should have a matching removeEventListener call somewhere
    },

    deregister_chain_handler: function () {
        var EVENTS = require('common/EVENTS');
        if (this.taskFinishedListener !== null) {
            Titanium.App.removeEventListener(EVENTS.TASK_FINISHED,
                                             this.taskFinishedListener);
            this.taskFinishedListener = null;
        }
    },

    debug_chain: function () {
        var GV = require('common/GV');
        Titanium.API.trace("inChain = " + GV.inChain +
                           ", chainList.length = " + GV.chainList.length +
                           ", chainIndex = " + GV.chainIndex);
    },

    reset_gv_chain: function () {
        var GV = require('common/GV');
        GV.inChain = false;
        GV.chainList = [];
        GV.chainIndex = 0;
        GV.chainTablenames = [];
        GV.chainIds = [];
    },

};
module.exports = MenuTableViewWrapper;
