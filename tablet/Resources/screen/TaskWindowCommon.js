// TaskWindowCommon.js

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

/*jslint node: true, newcap: true, plusplus: true */
"use strict";
/*global Titanium, L */

var platform = require('lib/platform'),
    NO_SECTIONS = platform.mobileweb,
    // ... workaround for: https://jira.appcelerator.org/browse/TIMOB-18112
    TYPE_CHOOSE_PATIENT = 'choose',
    TYPE_INFO = 'info',
    TYPE_TASK = 'task';
    // TASK_SECTION = 1; // tasks are in the second section of the table

function sortfunction(a, b) { // comparing two tasks
    var x = a.dateRaw,
        y = b.dateRaw,
        xnull = (x === null || x === undefined),
        ynull = (y === null || y === undefined);
    if (xnull && ynull) {
        return 0;
    }
    if (xnull) {
        return -1;
    }
    if (ynull) {
        return 1;
    }
    return y.diff(x);
}

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

/*
function dump(x) {
    // Deals with circular objects more happily!
    var debugfunc = require('lib/debugfunc');
    debugfunc.dumpObject(x, {
        traceNotReturnString: true,
        showLevelNotDots: true,
        maxDepth: 2,
        lineLimit: 1000
    });
}
*/

function taskInfoFromTask(task, taskType, taskTitle, addPatientName,
                          showFinishFlag) {
    return {
        taskType: taskType, // may be null for single-task views
        taskTitle: taskTitle, // may be null for single-task views
        taskID: task.getPK(),
        patientName: addPatientName ? task.getPatientName() : null,
        dateRaw: task.getCreationDateTime(), // used for sorting
        date: task.getCreationDateTimeNice(),
        taskSummaryView: task.getSummaryView(),
        isComplete: task.isComplete(),
        showFinishFlag: showFinishFlag,
        finishFlag: showFinishFlag && task.getMoveOffTablet()
    };
}

function makeChoosePatient() {
    var MenuTableRow = require('menulib/MenuTableRow'),
        UICONSTANTS = require('common/UICONSTANTS');
    return new MenuTableRow({
        maintitle: L('menutitle_choose_patient'),
        icon: UICONSTANTS.ICON_CHOOSE_PATIENT,
        rowType: TYPE_CHOOSE_PATIENT
    });
}

function makeTaskInfo() {
    var MenuTableRow = require('menulib/MenuTableRow'),
        UICONSTANTS = require('common/UICONSTANTS');
    return new MenuTableRow({
        maintitle: L('task_info'),
        icon: UICONSTANTS.ICON_INFO,
        rowType: TYPE_INFO
    });
}

//var instanceCounter = 1;

function TaskWindowCommon(isPatientSummary, tasktype, tasktitle, taskhtml) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        uifunc = require('lib/uifunc'),
        EVENTS = require('common/EVENTS'),
        taskPermitted = true,
        crippled = false,
        self = this,
        leftpos = 0,
        rightpos = 0,
        mainview = Titanium.UI.createView({
            height: Titanium.UI.FILL,
            width: Titanium.UI.FILL,
            layout: 'vertical'
        }),
        toprowprops = {
            height: UICONSTANTS.ICONSIZE, // not SIZE, on very narrow displays, it
            // breaks a bit. Truncate instead!
            width: Titanium.UI.FILL
        },
        backbutton_left,
        icon_left,
        heading_left,
        lockbutton_right,
        addbutton_right,
        deletebutton_right,
        editbutton_right,
        zoombutton_right,
        finishflagbutton_right,
        heading_right,
        title,
        toprow,
        icon;

    this.isPatientSummary = isPatientSummary;
    this.tasktitle = tasktitle;
    this.taskhtml = taskhtml;
    this.taskrows = [];

    this.TaskClass = null;
    this.dummytask = null;
    this.anonymous = false;
    if (!isPatientSummary) {
        this.TaskClass = require(tasktype);
        this.dummytask = new this.TaskClass();
        this.anonymous = this.dummytask.isAnonymous();
        taskPermitted = this.dummytask.isTaskPermissible();
        crippled = this.dummytask.isTaskCrippled();
    }
    this.offerAdd = !isPatientSummary;
    this.offerFinishFlag = this.anonymous;

    backbutton_left = uifunc.buttonPosition(leftpos++);
    if (isPatientSummary) {
        icon_left = uifunc.buttonPosition(leftpos++);
    }
    heading_left = uifunc.buttonPosition(leftpos++);

    lockbutton_right = uifunc.buttonPosition(rightpos++);
    if (this.offerAdd) {
        addbutton_right = uifunc.buttonPosition(rightpos++);
    }
    deletebutton_right = uifunc.buttonPosition(rightpos++);
    editbutton_right = uifunc.buttonPosition(rightpos++);
    zoombutton_right = uifunc.buttonPosition(rightpos++);
    if (this.offerFinishFlag) {
        finishflagbutton_right = uifunc.buttonPosition(rightpos++);
    }
    heading_right = uifunc.buttonPosition(rightpos++);

    this.tiview = uifunc.createMenuWindow();
    //this.instance = instanceCounter++;
    //Titanium.API.trace("TaskWindowCommon (" + this.instance +
    //                   "): constructor");

    // WAIT
    this.wait = uifunc.createWait({ window: this.tiview });
    this.repopulating_wait = uifunc.createWait({ window: this.tiview });

    // BACK
    this.backbutton = uifunc.createBackButton({ left: backbutton_left });
    this.backListener = function () { self.back(); };
    this.backbutton.addEventListener('click', this.backListener);

    // LOCKS
    this.lockButton = uifunc.createLockButton({right: lockbutton_right});
    this.unlockButton = uifunc.createUnlockButton({right: lockbutton_right});
    this.deprivilegeButton = uifunc.createDeprivilegeButton({
        right: lockbutton_right
    });

    // ADD
    if (this.offerAdd) {
        this.addbutton = uifunc.createAddButton({right: addbutton_right});
        this.addListener = function () { self.add(); };
        this.addbutton.addEventListener('click', this.addListener);
    }

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

    // ZOOM
    this.zoombutton = uifunc.createZoomButton({
        right: zoombutton_right,
        visible: false
    });
    this.zoomListener = function () { self.zoom(); };
    this.zoombutton.addEventListener('click', this.zoomListener);

    // FINISHFLAG -- ONLY USED FOR *ANONYMOUS* TASKS (patient-based tasks are
    // finish-flagged on a per-patient basis)
    if (this.offerFinishFlag) {
        this.finishflagbutton = uifunc.createFinishFlagButton({
            right: finishflagbutton_right,
            visible: false
        });
        this.finishflagListener = function () {
            self.finishflag();
        };
        this.finishflagbutton.addEventListener('click',
                                               this.finishflagListener);
    }

    // REST OF HEADER
    title = uifunc.createMenuTitleText({
        left: heading_left,
        right: heading_right,
        text: isPatientSummary ? L('patient_summary_title') : tasktitle,
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT
        // ... Titanium.UI.TEXT_ALIGNMENT_CENTER,
    });

    if (!taskPermitted) {
        toprowprops.backgroundColor = UICONSTANTS.NOT_PERMISSIBLE_BACKGROUND_COLOUR;
    } else if (crippled) {
        toprowprops.backgroundColor = UICONSTANTS.CRIPPLED_BACKGROUND_COLOUR;
    }
    toprow = Titanium.UI.createView(toprowprops);
    toprow.add(this.backbutton);
    toprow.add(this.lockButton);
    toprow.add(this.unlockButton);
    toprow.add(this.deprivilegeButton);
    toprow.add(title);
    if (this.offerAdd) {
        toprow.add(this.addbutton);
    }
    toprow.add(this.editbutton);
    toprow.add(this.deletebutton);
    toprow.add(this.zoombutton);
    if (this.offerFinishFlag) {
        toprow.add(this.finishflagbutton);
    }
    if (isPatientSummary) {
        icon = uifunc.createGenericButton(
            UICONSTANTS.ICON_PATIENT_SUMMARY,
            { left: icon_left }
        );
        toprow.add(icon);
    }

    // PATIENT
    this.patientrow = Titanium.UI.createLabel({
        left: UICONSTANTS.SPACE,
        font: UICONSTANTS.PATIENT_FONT
    });
    this.set_patient_line();

    // TABLE VIEW
    this.tableview = Titanium.UI.createTableView({
        height: Titanium.UI.FILL, // with SIZE, on iOS it will scroll-bounce
        // back and you won't be able to get to the end
        width: Titanium.UI.FILL,
        top: 0,
        backgroundColor: UICONSTANTS.MENU_BG_COLOUR,
        separatorColor: UICONSTANTS.MENU_SEPARATOR_COLOUR,
        allowsSelection: true,
        // ... appears to do nothing! We have to emulate it ourselves.
        showVerticalScrollIndicator: true,
        minRowHeight: UICONSTANTS.MIN_TABLE_ROW_HEIGHT
    });
    this.rowListener = function (e) { self.rowClicked(e); };
    this.tableview.addEventListener('click', this.rowListener);

    this.selectedIndex = null;

    // REST OF WINDOW CODE
    mainview.add(toprow);
    mainview.add(uifunc.createMenuRule());
    mainview.add(uifunc.createVerticalSpacer());
    mainview.add(this.patientrow);
    mainview.add(uifunc.createVerticalSpacer());
    mainview.add(this.tableview);
    this.tiview.add(mainview);

    this.pending_patient_update = true;
    this.have_focus = false;

    this.suppress_repopulate = true;
    this.set_patient_lock();
    this.suppress_repopulate = false;

    // OTHER EVENT HANDLERS

    this.openListener = function () { self.set_button_states(); };
    this.tiview.addEventListener('open', this.openListener);
    this.androidBackListener = function () { self.close(); };
    this.tiview.addEventListener('android:back', this.androidBackListener);
    this.focusListener = function () { self.gain_focus(); };
    this.tiview.addEventListener('focus', this.focusListener);
    this.blurListener = function () { self.lose_focus(); };
    this.tiview.addEventListener('blur', this.blurListener);
    // ... their name for "lose focus"

    this.taskFinishedListener = function (e) { self.task_finished(e); };
    Titanium.App.addEventListener(EVENTS.TASK_FINISHED,
                                  this.taskFinishedListener);
    // ... should have a matching removeEventListener call somewhere
    this.patientChosenListener = function () {
        self.patient_chosen_maybe_wait();
    };
    Titanium.App.addEventListener(EVENTS.PATIENT_CHOSEN,
                                  this.patientChosenListener);
    // ... should have a matching removeEventListener call somewhere
    this.setLockListener = function () { self.set_patient_lock(); };
    Titanium.App.addEventListener(EVENTS.PATIENT_LOCK_CHANGED,
                                  this.setLockListener);
    // ... should have a matching removeEventListener call somewhere
}
TaskWindowCommon.prototype = {

    open: function () {
        //Titanium.API.trace("TaskWindowCommon (" + this.instance + "): open");
        this.tiview.open();
    },

    close: function () {
        //Titanium.API.trace("TaskWindowCommon (" + this.instance +
        //                   "): close");
        this.tiview.close();
        this.cleanup_base();
    },

    cleanup: function () {
        // can be overridden
        return;
    },

    cleanup_base: function () {
        var EVENTS = require('common/EVENTS');
        //Titanium.API.trace("TaskWindowCommon (" + this.instance +
        //                   "): cleanup_base");

        this.cleanup(); // for child classes

        this.backbutton.removeEventListener('click', this.backListener);
        this.backListener = null;
        this.backbutton = null;

        this.editbutton.removeEventListener('click', this.editListener);
        this.editListener = null;
        this.editbutton = null;

        this.deletebutton.removeEventListener('click', this.deleteListener);
        this.deleteListener = null;
        this.deletebutton = null;

        this.zoombutton.removeEventListener('click', this.zoomListener);
        this.zoomListener = null;
        this.zoombutton = null;

        if (this.offerAdd) {
            this.addbutton.removeEventListener('click', this.addListener);
            this.addListener = null;
            this.addbutton = null;
        }

        if (this.offerFinishFlag) {
            this.finishflagbutton.removeEventListener('click',
                                                      this.finishflagListener);
            this.finishflagListener = null;
            this.finishflagbutton = null;
        }

        this.tableview.removeEventListener('click', this.rowListener);
        this.rowListener = null;
        this.tableview = null;

        this.lockButton = null;
        this.unlockButton = null;
        this.deprivilegeButton = null;

        this.tiview.removeEventListener('open', this.openListener);
        this.openListener = null;
        this.tiview.removeEventListener('android:back',
                                        this.androidBackListener);
        this.androidBackListener = null;
        this.tiview.removeEventListener('focus', this.focusListener);
        this.focusListener = null;
        this.tiview.removeEventListener('blur', this.blurListener);
        this.blurListener = null;
        this.tiview = null;

        this.repopulating_wait = null;
        this.wait = null;
        //Titanium.API.trace("TaskWindowCommon (" + this.instance +
        //                   "): ... setting this.wait = null");

        Titanium.App.removeEventListener(EVENTS.TASK_FINISHED,
                                         this.taskFinishedListener);
        this.taskFinishedListener = null;
        Titanium.App.removeEventListener(EVENTS.PATIENT_CHOSEN,
                                         this.patientChosenListener);
        this.patientChosenListener = null;
        Titanium.App.removeEventListener(EVENTS.PATIENT_LOCK_CHANGED,
                                         this.setLockListener);
        this.setLockListener = null;
    },

    task_finished: function (e) {
        //Titanium.API.trace("TaskWindowCommon.task_finished: e = " +
        //                   JSON.stringify(e));
        var GV = require('common/GV'),
            UICONSTANTS,
            uifunc,
            self = this;
        if (GV.inChain) {
            return; // chains are handled by MenuTableViewWrapper instead
        }
        UICONSTANTS = require('common/UICONSTANTS');
        if (e.result !== UICONSTANTS.READONLYVIEWFINISHED) {
            this.repopulate();
            uifunc = require('lib/uifunc');
            uifunc.task_finished_offer_upload(self, function () {
                self.repopulate();
            });
        }
    },

    back: function () {
        Titanium.API.info("TaskWindowCommon: back button clicked");
        this.close(); // should call cleanup
    },

    set_button_states: function () {
        // Will only work if called after the window is opened.
        if (this.selectedIndex !== null) {
            this.editbutton.show();
            this.deletebutton.show();
            this.zoombutton.show();
            if (this.offerFinishFlag) {
                if (this.anonymous) {
                    this.finishflagbutton.show();
                } else {
                    this.finishflagbutton.hide();
                }
            }
        } else {
            this.editbutton.hide();
            this.deletebutton.hide();
            this.zoombutton.hide();
            if (this.offerFinishFlag) {
                this.finishflagbutton.hide();
            }
        }
    },

    info: function () {
        if (this.isPatientSummary) {
            return;
        }
        var uifunc = require('lib/uifunc');
        // The webview breaks slightly when the user goes browsing (e.g.
        // "open-in-new-window" links fail).
        // So we'd like to use Titanium.Platform.openURL(); however, that
        // doesn't have access to our resources. One can get round this:
        //  http://developer.appcelerator.com/blog/2011/09/sharing-project-assets-with-android-intents.html
        // ... but a bit of a faff.
        // Therefore, use a webview for now:
        uifunc.showHtml(this.taskhtml, this.tasktitle);
        // ... the nested webview breaks slightly when the user browses to
        // other sites
    },

    edit: function () {
        var uifunc = require('lib/uifunc'),
            task = this.getSelectedTask();
        Titanium.API.info("TaskWindowCommon: edit button clicked");
        uifunc.editTask(task, this.wait);
    },

    offer_delete: function () {
        var uifunc = require('lib/uifunc'),
            task = this.getSelectedTask(),
            self = this;
        Titanium.API.info("TaskWindowCommon: delete button clicked");
        uifunc.deleteTask(task, function () { self.repopulate(); });
    },

    zoom: function () {
        var uifunc = require('lib/uifunc'),
            task = this.getSelectedTask();
        uifunc.zoomTask(task, this.wait);
    },

    finishflag: function () {
        var task = this.getSelectedTask();
        task.toggleMoveOffTablet();
        this.repopulate();
    },

    set_patient_line: function () {
        var uifunc = require('lib/uifunc');
        uifunc.setPatientLine(this.patientrow);
    },

    getSelectedIndex: function () {
        return this.selectedIndex;
    },

    isTaskSelected: function () {
        return this.selectedIndex !== null;
    },

    getSelectedTask: function () {
        if (this.selectedIndex === null || this.selectedIndex < 0 ||
                this.selectedIndex >= this.taskrows.length) {
            return null;
        }
        this.wait.show();
        var row = this.taskrows[this.selectedIndex],
            id = row.taskID,
            task,
            taskType,
            TaskClass;
        if (this.isPatientSummary) {
            taskType = row.taskType;
            TaskClass = require(taskType);
            task = new TaskClass();
        } else {
            task = new this.TaskClass();
        }
        task.dbread(id);
        this.wait.hide();
        return task;
    },

    select_by_index: function (index) {
        // tableview.data is an array of *sections*
        // ... http://developer.appcelerator.com/question/122893/tableview---data-property
        // ... http://developer.appcelerator.com/question/9121/getting-tableview-data-array

        // Titanium.API.trace("select_by_index()");
        // dump(this.tableview.data); // on mobileweb: useless

        if (this.selectedIndex !== null) {
            // don't use if (this.selectedIndex)! That returns false for 0.
            if (this.selectedIndex === index) {
                return; // nothing to do
            }
            deselect_row(this.taskrows[this.selectedIndex]);
        }
        this.selectedIndex = index;
        if (this.selectedIndex === null) {
            return;
        }
        select_row(this.taskrows[this.selectedIndex]);
        // this.tableview.scrollToIndex(selectedIndex);
        this.set_button_states();
    },

    add: function () {
        var uifunc = require('lib/uifunc');
        Titanium.API.info("TaskWindowCommon: add button clicked");
        uifunc.addTask(this.TaskClass, this.wait);
    },

    rowClicked: function (e) {
        var uifunc = require('lib/uifunc'),
            r = uifunc.getRowDataFromTableViewClickEvent(e);
        // IF YOU READ VARIABLES HERE, MAKE SURE YOU COPIED THEM IN MenuTableRow
        // Titanium.API.trace("TaskWindowCommon: tableview clicked: e stringify = " + JSON.stringify(e));
        // Titanium.API.trace("TaskWindowCommon: tableview clicked: e = " + e);
        // Titanium.API.trace("TaskWindowCommon: tableview clicked: e props = " + uifunc.dumpProps(e));
        // Titanium.API.trace("TaskWindowCommon: tableview clicked: source = " + e.source);
        // other more basic way: if (e.source && e.source.rowType) { ... }

        // Titanium.API.trace("TaskWindowCommon: rowClicked: e:");
        // dump(e);
        // Titanium.API.trace("TaskWindowCommon: rowClicked: r:");
        // dump(r);
        if (r) {
            // MobileWeb, Sep 2015: r is circular; avoid JSON.stringify
            //Titanium.API.trace(
            //    "TaskWindowCommon: tableview clicked: row data = " +
            //    JSON.stringify(r)
            //);
            if (r.rowType === TYPE_CHOOSE_PATIENT) {
                uifunc.choosePatient();
            } else if (r.rowType === TYPE_INFO) {
                this.info();
            } else if (r.rowType === TYPE_TASK) {
                this.select_by_index(r.rowIndex);
            }
        } else {
            Titanium.API.trace("TaskWindowCommon: tableview clicked, but no row data");
        }
    },

    repopulate: function () {
        this.repopulating_wait.show();
        var GV = require('common/GV'),
            TaskRow = require('menulib/TaskRow'),
            taskdata = [],
            i,
            ALLTASKS,
            t,
            tasktitle,
            tasktype,
            TaskClass,
            dummytask,
            anonymous,
            singletaskdata,
            tasks = [],
            addPatientName = false,
            sectionTools = (
                NO_SECTIONS
                ? null
                : Titanium.UI.createTableViewSection({headerTitle: L('options')})
            ),
            sectionList = (
                NO_SECTIONS
                ? null
                : Titanium.UI.createTableViewSection({
                        headerTitle: L('task_list') + (
                            this.isPatientSummary ? "" : (": " + this.tasktitle)
                        )
                    })
            ),
            noSectionArray = [];

        this.taskrows = [];
        // Gather task instances info into taskdata
        if (this.isPatientSummary) {
            if (GV.selected_patient_id !== null) {
                ALLTASKS = require('common/ALLTASKS');
                for (t in ALLTASKS.TASKLIST) {
                    if (ALLTASKS.TASKLIST.hasOwnProperty(t)) {
                        tasktitle = ALLTASKS.TASKLIST[t].title;
                        this.repopulating_wait.setMessage(L('scanning_tasks') +
                                                          "\n\n" + tasktitle);
                        Titanium.API.trace("PatientSummaryWindow - processing " +
                                           "task " + t + " / " + tasktitle);
                        tasktype = ALLTASKS.TASKLIST[t].task;
                        TaskClass = require(tasktype);
                        dummytask = new TaskClass();
                        anonymous = dummytask.isAnonymous();
                        if (!anonymous) {
                            singletaskdata = dummytask.getAllRowsByPatient(
                                GV.selected_patient_id
                            );
                            // creates a dummy object to use its
                            // getAllRowsByPatient() method
                            Titanium.API.trace("... yields " +
                                               singletaskdata.length + " rows");
                            for (i = 0; i < singletaskdata.length; ++i) {
                                taskdata.push(
                                    taskInfoFromTask(singletaskdata[i],
                                                     tasktype, tasktitle,
                                                     false, false)
                                );
                            }
                        }
                    }
                }
            }
        } else {
            if (this.anonymous) {
                // anonymous task; show all
                tasks = this.dummytask.getAllRows();
            } else if (GV.selected_patient_id === null && !GV.patient_locked) {
                // specific task: show all instances, may be multiple patients
                tasks = this.dummytask.getAllRows();
                addPatientName = true;
            } else if (GV.selected_patient_id !== null) {
                // specific task: show all instances for a patient
                tasks = this.dummytask.getAllRowsByPatient(
                    GV.selected_patient_id
                );
            }
            // if locked; no patient selected; not viewing an anonymous task --
            // therefore, show nothing

            // Make them into our standard row-feeding format
            for (i = 0; i < tasks.length; ++i) {
                taskdata.push(taskInfoFromTask(tasks[i], null, null,
                                               addPatientName,
                                               this.anonymous));
            }
        }
        taskdata.sort(sortfunction);
        Titanium.API.trace("TaskWindowCommon.repopulate(): found " +
                           taskdata.length + " records");

        // Tasks
        for (i = 0; i < taskdata.length; ++i) {
            taskdata[i].rowIndex = i;
            taskdata[i].rowType = TYPE_TASK;
            this.taskrows.push(new TaskRow(taskdata[i]));
        }
        if (NO_SECTIONS) {
            if (!this.anonymous) {
                noSectionArray.push(makeChoosePatient());
            }
            if (!this.isPatientSummary) {
                noSectionArray.push(makeTaskInfo());
            }
            for (i = 0; i < this.taskrows.length; ++i) {
                noSectionArray.push(this.taskrows[i]);
            }
            this.tableview.setData(noSectionArray);
        } else {
            if (!this.anonymous) {
                sectionTools.add(makeChoosePatient());
            }
            if (!this.isPatientSummary) {
                sectionTools.add(makeTaskInfo());
            }
            for (i = 0; i < this.taskrows.length; ++i) {
                sectionList.add(this.taskrows[i]);
            }
            this.tableview.setData([sectionTools, sectionList]);
        }

        this.selectedIndex = null;
            // We can't maintain a selection index through a repopulate() call,
            // because even the selected patient might have changed.
        this.set_button_states();
        this.repopulating_wait.hide();
    },

    patient_chosen_maybe_wait: function () {
        // We distinguish between focused/not focused because otherwise
        // we might waste CPU processing a change of patient while this
        // window is invisible.
        if (this.have_focus) {
            this.patient_chosen_do_update();
        } else {
            this.pending_patient_update = true;
        }
    },

    patient_chosen_do_update: function () {
        var uifunc = require('lib/uifunc');
        uifunc.setPatientLine(this.patientrow);
        this.repopulate();
        this.pending_patient_update = false;
    },

    set_patient_lock: function () {
        var uifunc = require('lib/uifunc'),
            GV;
        uifunc.setLockButtons(this.lockButton, this.unlockButton,
                              this.deprivilegeButton);
        if (this.isPatientSummary || this.anonymous ||
                this.suppress_repopulate) {
            return;
        }
        GV = require('common/GV');
        if (GV.selected_patient_id === null) {
            // we are a per-task view...
            // ... with no patient selected
            // ... and it's not an anonymouse task...

            // ... so if the lock status changes when we have no patient
            //     selected, we're likely to need to redo the list
            // ... because we show all task instances when unlocked,
            //     and none when locked.

            this.repopulate();
        }
    },

    gain_focus: function () {
        Titanium.API.trace("TaskWindowCommon: gain_focus, " +
                           "pending_patient_update = " +
                           this.pending_patient_update);
        this.have_focus = true;
        if (this.pending_patient_update) {
            this.patient_chosen_do_update();
        }
    },

    lose_focus: function () {
        Titanium.API.trace("TaskWindowCommon: lose_focus, " +
                           "pending_patient_update = " +
                           this.pending_patient_update);
        this.have_focus = false;
    }

};
module.exports = TaskWindowCommon;
