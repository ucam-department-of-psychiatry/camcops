// SelectPatientWindow.js

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

/*jslint node: true, plusplus: true, newcap: true */
"use strict";
/*global Titanium, L */

function select_row(row) {
    var UICONSTANTS = require('common/UICONSTANTS');
    row.setBackgroundColor(UICONSTANTS.HIGHLIGHT_BG_COLOUR);
    row.selected = true;
}

function deselect_row(row) {
    var UICONSTANTS = require('common/UICONSTANTS');
    row.setBackgroundColor(UICONSTANTS.MENU_BG_COLOUR);
    row.selected = false;
}

function sortfunction(a, b) { // comparing two patients
    var x = a.getNameForSearch(),
        y = b.getNameForSearch();
    if (!x && !y) {
        return 0;
    }
    if (!x) {
        return -1;
    }
    if (!y) {
        return 1;
    }
    if (x < y) {
        return -1;
    }
    if (x > y) {
        return 1;
    }
    return 0;
}

/*

*** Titanium bug (https://jira.appcelerator.org/browse/TC-3266):
for this window only, docking/undocking with the Android tablet keyboard causes
a crash - specifically:

    Wrong state class, expecting View State but received class
    android.widget.AbsListView$SavedState instead. This usually happens when
    two views of different type have the same id in the same hierarchy. This
    view's id is id/0x65. Make sure other views do not use the same id.

For other windows, this error was reproducible by calling the cleanup (and
wiping the tiview to null) on a window "close" listener -- because the
dock/undock causes a close/open event on the window. However, that doesn't
still seem to be the case, yet only for this window, it still happens. I must
not be seeing it...

FOUND IT - it happens consistently when a table has a search bar.
BUG REPORT: https://jira.appcelerator.org/browse/TC-3266

*/

function SelectPatientWindow() {

    var UICONSTANTS = require('common/UICONSTANTS'),
        EVENTS = require('common/EVENTS'),
        uifunc = require('lib/uifunc'),
        platform = require('lib/platform'),
        self = this,
        leftbuttonpos = 0,
        backbutton_left = uifunc.buttonPosition(leftbuttonpos++),
        icon_left = uifunc.buttonPosition(leftbuttonpos++),
        title_left = uifunc.buttonPosition(leftbuttonpos++),
        rightbuttonpos = 0,
        addbutton_right = uifunc.buttonPosition(rightbuttonpos++),
        deletebutton_right = uifunc.buttonPosition(rightbuttonpos++),
        editbutton_right = uifunc.buttonPosition(rightbuttonpos++),
        finishflagbutton_right = uifunc.buttonPosition(rightbuttonpos++),
        title_right = uifunc.buttonPosition(rightbuttonpos++),
        icon = uifunc.createGenericButton(UICONSTANTS.ICON_CHOOSE_PATIENT,
                                          { left: icon_left }),
        title = uifunc.createMenuTitleText({
            left: title_left,
            right: title_right,
            text: L('menutitle_choose_patient'),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT
        }),
        toprow = Titanium.UI.createView({
            height: UICONSTANTS.ICONSIZE, // not SIZE; on very narrow displays,
            // it breaks a bit. Truncate instead!
            width: Titanium.UI.FILL
        }),
        tableprops,
        mainview = Titanium.UI.createView({
            height: Titanium.UI.FILL,
            width: Titanium.UI.FILL,
            // backgroundColor: '#FF0000',
            layout: 'vertical'
        });

    this.selectedIndex = null;

    this.tiview = uifunc.createMenuWindow();
    this.wait = uifunc.createWait({ window: this.tiview });

    // BACK
    this.backbutton = uifunc.createBackButton({left: backbutton_left});
    this.backListener = function () { self.back(); };
    this.backbutton.addEventListener('click', this.backListener);

    // ADD
    this.addbutton = uifunc.createAddButton({ right: addbutton_right });
    this.addListener = function () { self.add(); };
    this.addbutton.addEventListener('click', this.addListener);

    // EDIT
    this.editbutton = uifunc.createEditButton({
        right: editbutton_right,
        visible: false
    });
    this.editListener = function () { self.edit(); };
    this.editbutton.addEventListener('click', this.editListener);

    // DELETE
    this.deletebutton = uifunc.createDeleteButton({
        right: deletebutton_right,
        visible: false
    });
    this.deleteListener = function () { self.offer_delete(); };
    this.deletebutton.addEventListener('click', this.deleteListener);

    // FINISHFLAG
    this.finishflagbutton = uifunc.createFinishFlagButton({
        right: finishflagbutton_right,
        visible: false
    });
    this.finishflagListener = function () { self.finishflag(); };
    this.finishflagbutton.addEventListener('click', this.finishflagListener);

    toprow.add(this.backbutton);
    toprow.add(icon);
    toprow.add(title);
    toprow.add(this.addbutton);
    toprow.add(this.editbutton);
    toprow.add(this.deletebutton);
    toprow.add(this.finishflagbutton);

    this.patientline = Titanium.UI.createLabel({
        left: UICONSTANTS.SPACE,
        font: UICONSTANTS.PATIENT_FONT
    });

    this.set_patient_line();

    tableprops = {
        height: Titanium.UI.FILL, // a bit ugly, but it stops it being too
        // short with a search bar on iOS
        // ... also, with SIZE, on iOS it will scroll-bounce back and you won't
        // be able to get to the end
        width: Titanium.UI.FILL,
        top: 0,
        backgroundColor: UICONSTANTS.MENU_BG_COLOUR,
        separatorColor: UICONSTANTS.MENU_SEPARATOR_COLOUR,
        filterAttribute: 'patientNameForFilter',
        filterCaseInsensitive: true,
        allowsSelection: true,
        // ... appears to do nothing! We have to emulate it ourselves.
        showVerticalScrollIndicator: true,
        minRowHeight: UICONSTANTS.MIN_TABLE_ROW_HEIGHT,
        data: this.getTableData()
    };
    if (!platform.mobileweb) {
        tableprops.search = Titanium.UI.createSearchBar({
            top: 0,
            left: 0,
            height: 45,
            showCancel: false,
            backgroundColor: UICONSTANTS.MENU_SEARCHBAR_BG_COLOUR
            // barColor: UICONSTANTS.MENU_SEARCHBAR_BG_COLOUR,
            // ... iOS: colour of the bar itself (with shading effects applied)
            // borderColor: UICONSTANTS.MENU_SEARCHBAR_BG_COLOUR,
            // ... not sure
        });
    }

    this.tableview = Titanium.UI.createTableView(tableprops);
    this.rowListener = function (e) { self.rowClicked(e); };
    this.tableview.addEventListener('click', this.rowListener);

    // REST OF WINDOW CODE
    mainview.add(toprow);
    mainview.add(uifunc.createMenuRule());
    mainview.add(uifunc.createVerticalSpacer());
    mainview.add(this.patientline);
    mainview.add(uifunc.createVerticalSpacer());
    mainview.add(this.tableview);
    this.tiview.add(mainview);

    // OTHER EVENT HANDLERS

    this.openListener = function () { self.set_button_states(); };
    this.tiview.addEventListener('open', this.openListener);
    this.androidBackListener = function () { self.close(); };
    this.tiview.addEventListener('android:back', this.androidBackListener);

    this.editsaveListener = function (data) { self.patient_edit_save(data); };
    Titanium.App.addEventListener(EVENTS.PATIENT_EDIT_SAVE,
                                  this.editsaveListener);
}
SelectPatientWindow.prototype = {

    open: function () {
        this.tiview.open();
    },

    close: function () {
        this.tiview.close();
        this.cleanup();
    },

    cleanup: function () {
        Titanium.API.info("SelectPatientWindow: cleanup");
        var EVENTS = require('common/EVENTS');

        this.backbutton.removeEventListener('click', this.backListener);
        this.backListener = null;
        this.backbutton = null;

        this.addbutton.removeEventListener('click', this.addListener);
        this.addListener = null;
        this.addbutton = null;

        this.editbutton.removeEventListener('click', this.editListener);
        this.editListener = null;
        this.editbutton = null;

        this.deletebutton.removeEventListener('click', this.deleteListener);
        this.deleteListener = null;
        this.deletebutton = null;

        this.finishflagbutton.removeEventListener('click',
                                                  this.finishflagListener);
        this.finishflagListener = null;
        this.finishflagbutton = null;

        this.tableview.removeEventListener('click', this.rowListener);
        this.rowListener = null;
        this.tableview = null;

        this.tiview.removeEventListener('open', this.openListener);
        this.openListener = null;
        this.tiview.removeEventListener('android:back',
                                        this.androidBackListener);
        this.androidBackListener = null;
        this.tiview = null;

        this.wait = null;
        this.patientline = null;

        Titanium.App.removeEventListener(EVENTS.PATIENT_EDIT_SAVE,
                                         this.editsaveListener);
        this.editsaveListener = null;
    },

    set_patient_line: function () {
        var uifunc = require('lib/uifunc');
        uifunc.setPatientLine(this.patientline);
    },

    back: function () {
        Titanium.API.info("SelectPatientWindow: back button clicked");
        this.close(); // will call cleanup
    },

    add: function () {
        Titanium.API.info("SelectPatientWindow: add button clicked");
        var Patient = require('table/Patient'),
            p = new Patient();
        p.edit(); // may fire EVENTS.PATIENT_EDIT_SAVE
    },

    edit: function () {
        Titanium.API.info("SelectPatientWindow: edit button clicked");
        var p = this.getSelectedPatient();
        if (!p) {
            return;
        }
        p.edit(); // may fire EVENTS.PATIENT_EDIT_SAVE
    },

    how_many_associated_tasks: function (patient_id) {
        this.wait.show();
        var ALLTASKS = require('common/ALLTASKS'),
            n = 0,
            t,
            tasktype,
            Taskclass,
            taskdata;
        for (t in ALLTASKS.TASKLIST) {
            if (ALLTASKS.TASKLIST.hasOwnProperty(t)) {
                tasktype = ALLTASKS.TASKLIST[t].task;
                Taskclass = require(tasktype);
                taskdata = new Taskclass().getAllRowsByPatient(patient_id);
                n += taskdata.length;
            }
        }
        this.wait.hide();
        return n;
    },

    delete_patient: function (patient, delete_associated_tasks) {
        var GV = require('common/GV'),
            ALLTASKS = require('common/ALLTASKS'),
            pid = patient.id,
            t,
            tasktype,
            Taskclass,
            taskdata,
            j;
        this.wait.show();
        if (GV.selected_patient_id === pid) {
            this.broadcast_patient_selection(null);
        }
        patient.dbdelete();
        if (delete_associated_tasks) {
            for (t in ALLTASKS.TASKLIST) {
                if (ALLTASKS.TASKLIST.hasOwnProperty(t)) {
                    tasktype = ALLTASKS.TASKLIST[t].task;
                    Taskclass = require(tasktype);
                    taskdata = new Taskclass().getAllRowsByPatient(pid);
                    for (j = 0; j < taskdata.length; ++j) {
                        taskdata[j].dbdelete();
                    }
                }
            }
        }
        this.wait.hide();
        this.repopulate();
    },

    offer_delete: function () {
        Titanium.API.info("SelectPatientWindow: delete button clicked");
        var patient = this.getSelectedPatient(),
            dlg = Titanium.UI.createAlertDialog({
                title: L('delete_patient_q'),
                message: L('delete_this_patient_q') + '\n\n' + patient.getSummary(),
                buttonNames: [L('cancel'), L('delete')]
            }),
            self = this;
        if (!patient) {
            return;
        }
        dlg.addEventListener('click', function (ev) {
            var n,
                dlg2;
            if (ev.index === 1) { // Delete
                n = self.how_many_associated_tasks(patient.id);
                if (n > 0) {
                    dlg2 = Titanium.UI.createAlertDialog({
                        title: L('delete_patient_with_tasks_q'),
                        message: (
                            L('delete_this_patient_with_tasks_q_a') + ' ' + n +
                            ' ' + L('delete_this_patient_with_tasks_q_b') +
                            '\n\n' + patient.getSummary()
                        ),
                        buttonNames: [L('cancel'), L('delete')]
                    });
                    dlg2.addEventListener('click', function (ev) {
                        if (ev.index === 1) { // Delete
                            self.delete_patient(patient, true);
                        }
                        dlg2 = null;
                        self = null;
                    });
                    dlg2.show();
                } else {
                    self.delete_patient(patient, false);
                    self = null;
                }
            } else {
                self = null;
            }
            dlg = null;
        });
        dlg.show();
    },

    finishflag: function () {
        var p = this.getSelectedPatient();
        if (!p) {
            return;
        }

        // 1. The patient
        p.toggleMoveOffTablet();
        // moveoff = p.getMoveOffTablet();

        // 2. Associated tasks -- will be done at upload time

        this.repopulate();
    },

    rowClicked: function (e) {
        // var row_index = e.source.row_index; // for when we're compensating
        // with a custom row_index property of all rows and members of rows
        var row_index = e.index; // raw
        this.select_by_index(row_index);
    },

    getSelectedIndex: function () {
        return this.selectedIndex;
    },

    getSelectedPatientID: function () {
        if (this.selectedIndex === null) {
            return null;
        }
        var section = 0;
        return this.tableview.data[section].rows[this.selectedIndex].patientId;
    },

    getSelectedPatient: function () {
        var id = this.getSelectedPatientID(),
            Patient;
        if (id === null) {
            return null;
        }
        Patient = require('table/Patient');
        return new Patient(id);
    },

    select_by_index: function (index) {
        var section = 0;
        // this.tableview.data is an array of *sections*
        // ... http://developer.appcelerator.com/question/122893/this.tableview---data-property
        // ... http://developer.appcelerator.com/question/9121/getting-this.tableview-data-array
        if (this.selectedIndex === index) {
            // Clicked on what was already selected.
            // We could either return here (nothing to do), but that means
            // being unable to deselect. Let's implement a deselect:
            deselect_row(this.tableview.data[section].rows[this.selectedIndex]);
            this.selectedIndex = null;
        } else if (this.selectedIndex !== null) {
            // don't use if (this.selectedIndex)! That returns false for 0.
            // Something else was previously selected.
            deselect_row(this.tableview.data[section].rows[this.selectedIndex]);
            this.selectedIndex = index;
        } else {
            // Nothing previously selected.
            this.selectedIndex = index;
        }
        // Now process the new selection.
        if (this.selectedIndex !== null) {
            select_row(this.tableview.data[section].rows[this.selectedIndex]);
            // this.tableview.scrollToIndex(this.selectedIndex);
        }
        this.set_button_states();
        this.broadcast_patient_selection(this.selectedIndex === null ?
                null :
                this.tableview.data[section].rows[this.selectedIndex].patientId
            );
    },

    set_button_states: function () {
        // Will only work if called after the window is opened.
        if (this.selectedIndex !== null) {
            this.editbutton.show();
            this.deletebutton.show();
            this.finishflagbutton.show();
        } else {
            this.editbutton.hide();
            this.deletebutton.hide();
            this.finishflagbutton.hide();
        }
    },

    getTableData: function () {
        var Patient = require('table/Patient'),
            GV = require('common/GV'),
            UICONSTANTS = require('common/UICONSTANTS'),
            PatientRow = require('menulib/PatientRow'),
            tabledata = [],
            patientdata = (new Patient()).getAllRows(),
            i,
            r;
        // creates a dummy Patient object to use its getAllRows() method
        Titanium.API.trace("SelectPatientWindow.getTableData(): found " +
                           patientdata.length + " patients");
        patientdata.sort(sortfunction);
        this.selectedIndex = null;
        for (i = 0; i < patientdata.length; ++i) {
            // patientdata[i].row_index = i;
            // ... to compensate for Titanium TableView bug
            r = new PatientRow({
                patientId: patientdata[i].id,
                patientNameForFilter: patientdata[i].getNameForSearch(),
                firstRowText: patientdata[i].getLine1(),
                secondRowText: patientdata[i].getLine2(),
                failsUploadPolicy: !patientdata[i].satisfiesUploadIdPolicy(),
                failsFinalizePolicy: !patientdata[i].satisfiesFinalizeIdPolicy(),
                finishFlag: patientdata[i].getMoveOffTablet()
            });
            if (GV.selected_patient_id !== null &&
                    patientdata[i].id === GV.selected_patient_id) {
                this.selectedIndex = i;
                r.backgroundColor = UICONSTANTS.HIGHLIGHT_BG_COLOUR;
                // need to "preselect" as events to call select() seem not to
                // achieve their aim.
            }
            tabledata.push(r);
        }
        return tabledata;
    },

    repopulate: function () {
        this.wait.show();
        // Repopulate
        // Redisplay
        var tabledata = this.getTableData();
        this.tableview.setData(tabledata);
        if (this.selectedIndex !== null) {
            this.tableview.scrollToIndex(this.selectedIndex);
        }
        this.set_button_states();
        this.wait.hide();
    },

    broadcast_patient_selection: function (id) {
        var uifunc = require('lib/uifunc');
        uifunc.broadcastPatientSelection(id);
        this.set_patient_line();
    },

    patient_edit_save: function (data) {
        this.broadcast_patient_selection(data.id); // we always want to select
        // something we've just edited
        this.repopulate();
    }

};
module.exports = SelectPatientWindow;
