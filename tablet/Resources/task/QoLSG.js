// QoLSG.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    tablename = "qolsg",
    fieldlist = dbcommon.standardTaskFields(),
    EVENT_FROM_WEBVIEW = 'QOLSG_EVENT_FROM_WEBVIEW',
    EVENT_TO_WEBVIEW = 'QOLSG_EVENT_TO_WEBVIEW';

fieldlist.push(
    // Results
    {name: 'category_start_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'category_responded', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'category_response_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'category_chosen', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'gamble_fixed_option', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'gamble_lottery_option_p', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'gamble_lottery_option_q', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'gamble_lottery_on_left', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'gamble_starting_p', type: DBCONSTANTS.TYPE_REAL},
    {name: 'gamble_start_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'gamble_responded', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'gamble_response_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'gamble_p', type: DBCONSTANTS.TYPE_REAL},
    {name: 'utility', type: DBCONSTANTS.TYPE_REAL}
);

// CREATE THE TABLES

dbcommon.createTable(tablename, fieldlist);

//=============================================================================
// TASK (inc. webview handler)
//=============================================================================

function QoLSG(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(QoLSG, taskcommon.BaseTask);
lang.extendPrototype(QoLSG, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: QoLSG,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _editable: false,

    // OTHER

    // Standard task functions
    isComplete: function () {
        return this.utility !== null;
    },

    getSummary: function () {
        return L("qolsg_utility") + " " + lang.toFixedOrNull(this.utility, 3) +
                this.isCompleteSuffix();
    },

    getDetail: function () {
        var msg = "",
            i;
        for (i = 0; i < fieldlist.length; ++i) {
            msg += (
                fieldlist[i].name + ": " +
                dbcommon.userString(this, fieldlist[i]) + "\n"
            );
        }
        return msg;
    },

    edit: function () {  // readOnly ignored
        var self = this,
            UICONSTANTS = require('common/UICONSTANTS'),
            moment = require('lib/moment'),
            params = {
                TEXT_INITIAL_INSTRUCTION: L("qolsg_initial_instruction"),
                TEXT_CURRENT_STATE: L("qolsg_current_state"),
                TEXT_DEAD: L("qolsg_dead"),
                TEXT_HEALTHY: L("qolsg_healthy"),
                TEXT_INDIFFERENT: L("qolsg_indifferent"),
                TEXT_BACK: L("back"),
                TEXT_THANKS: L("webview_thanks"),
                TEXT_H_ABOVE_1: L("qolsg_h_above_1"),
                TEXT_H_0_TO_1: L("qolsg_h_0_to_1"),
                TEXT_H_BELOW_0: L("qolsg_h_below_0"),
                TEXT_LEFT: L("qolsg_left"),
                TEXT_RIGHT: L("qolsg_right"),
                TEXT_INSTRUCTION_PREFIX_2: L("qolsg_instruction_prefix_2"),
                TEXT_INSTRUCTION_MEDIUM: L("qolsg_instruction_medium"),
                TEXT_INSTRUCTION_LOW: L("qolsg_instruction_low"),
                TEXT_INSTRUCTION_HIGH: L("qolsg_instruction_high"),
                TEXT_INSTRUCTION_SUFFIX: L("qolsg_instruction_suffix")
            },
            html = taskcommon.loadHtmlSetParams(
                "task_html/qolsg_task.html",
                params,
                "task_html/qolsg_task.jsx"
            ),
            editing_time_start,
            editing_time_end,
            editing_time_s,
            window;

        self.dbstore(); // sets self.id

        //---------------------------------------------------------------------
        // Communication with webview
        //---------------------------------------------------------------------

        function eventFromWebView(e) {
            Titanium.API.trace("QoLSG: eventFromWebView: " + e.eventType);
            var conversion = require('lib/conversion'),
                dict;
            switch (e.eventType) {

            case "savetrial":
                dict = JSON.parse(e.data,
                                  conversion.json_decoder_reviver);
                lang.copyProperties(dict, self);
                self.dbstore();
                break;

            case "exit":
            case "abort":
                editing_time_end = moment();
                editing_time_s = editing_time_end.diff(editing_time_start,
                                                       'seconds',
                                                       true);  // floating-point
                self.defaultFinishedFn(
                    e.eventType === "exit" ?
                            UICONSTANTS.FINISHED :
                            UICONSTANTS.ABORTED,
                    editing_time_s
                );
                if (window !== null) {
                    window.close();
                    window = null;
                }
                break;
            }
        }

        //---------------------------------------------------------------------
        // Launch webview
        //---------------------------------------------------------------------
        window = taskcommon.createFullscreenWebviewWindow(
            html,
            EVENT_FROM_WEBVIEW,
            eventFromWebView
        );
        editing_time_start = moment();
        window.open();
    }

});

module.exports = QoLSG;
