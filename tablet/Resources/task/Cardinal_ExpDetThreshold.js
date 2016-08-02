// Cardinal_ExpDetThreshold.js

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

// Logistic regression plotting: http://stackoverflow.com/questions/9258708/plot-two-curves-in-logistic-regression-in-r

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // PER-SESSION TABLE
    maintablename = "cardinal_expdetthreshold",
    mainfieldlist = dbcommon.standardTaskFields(),
    configfieldlist = [
        // Config
        {name: 'modality', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'target_number', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'background_filename', type: DBCONSTANTS.TYPE_TEXT}, // set automatically
        {name: 'target_filename', type: DBCONSTANTS.TYPE_TEXT}, // set automatically
        {name: 'visual_target_duration_s', type: DBCONSTANTS.TYPE_REAL},
        {name: 'background_intensity', type: DBCONSTANTS.TYPE_REAL},
        {name: 'start_intensity_min', type: DBCONSTANTS.TYPE_REAL},
        {name: 'start_intensity_max', type: DBCONSTANTS.TYPE_REAL},
        {name: 'initial_large_intensity_step', type: DBCONSTANTS.TYPE_REAL},
        {name: 'main_small_intensity_step', type: DBCONSTANTS.TYPE_REAL},
        {name: 'num_trials_in_main_sequence', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'p_catch_trial', type: DBCONSTANTS.TYPE_REAL},
        {name: 'prompt', type: DBCONSTANTS.TYPE_TEXT},
        {name: 'iti_s', type: DBCONSTANTS.TYPE_REAL}
    ],
    trialtablename = "cardinal_expdetthreshold_trials",
    TRIAL_FK_FIELD = {
        name: 'cardinal_expdetthreshold_id',
        type: DBCONSTANTS.TYPE_INTEGER,
        mandatory: true
    }, // FK to cardinal_expdetthreshold.id
    trialfieldlist = dbcommon.standardAncillaryFields(TRIAL_FK_FIELD),
    PAGE_TARGET = "page_target",
    MODALITY_AUDITORY = 0, // must match cardinal_expdetthreshold_task.html
    MODALITY_VISUAL = 1, // must match cardinal_expdetthreshold_task.html
    EVENT_FROM_WEBVIEW = 'EXPDETTHRESHOLD_EVENT_FROM_WEBVIEW',
    EVENT_TO_WEBVIEW = 'EXPDETTHRESHOLD_EVENT_TO_WEBVIEW',
    DISPLAY_DP = 3;

mainfieldlist = mainfieldlist.concat(configfieldlist);
mainfieldlist.push(
    // Results from task HTML proper
    {name: 'finished', type: DBCONSTANTS.TYPE_BOOLEAN},
    // Results copied by task HTML from LogisticDescriptives function
    {name: 'intercept', type: DBCONSTANTS.TYPE_REAL},
    {name: 'slope', type: DBCONSTANTS.TYPE_REAL},
    {name: 'k', type: DBCONSTANTS.TYPE_REAL},
    {name: 'theta', type: DBCONSTANTS.TYPE_REAL}
);

trialfieldlist.push(
    // More keys
    {name: 'trial', type: DBCONSTANTS.TYPE_INTEGER, mandatory: true}, // trial number within this session
    // Results
    {name: 'trial_ignoring_catch_trials', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'target_presented', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'target_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'intensity', type: DBCONSTANTS.TYPE_REAL},
    {name: 'choice_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'responded', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'response_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'response_latency_ms', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'yes', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'no', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'caught_out_reset', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'trial_num_in_calculation_sequence', type: DBCONSTANTS.TYPE_INTEGER} // 0 for trials not used
);

// CREATE THE TABLES

dbcommon.createTable(maintablename, mainfieldlist);
dbcommon.createTable(trialtablename, trialfieldlist);

//=============================================================================
// Trial info record class
//=============================================================================

function TrialInfo(props) {
    dbcommon.DatabaseObject.call(this); // call base constructor
    // Instantiate with some combination of IDs, if specified (will read from the database if enough info given)
    dbcommon.loadOrCreateAncillary(this, props, "cardinal_expdetthreshold_id", "trial");
}
lang.inheritPrototype(TrialInfo, dbcommon.DatabaseObject);
lang.extendPrototype(TrialInfo, {
    // KEY DATABASE FIELDS (USED BY DatabaseObject)
    _objecttype: TrialInfo,
    _tablename: trialtablename,
    _fieldlist: trialfieldlist,
    _sortorder: "id",

    // OTHER

    setFromDictAndSave: function (dict) {
        dbcommon.copyFields(trialfieldlist, dict, this, 1); // skips first field (PK)
        this.dbstore();
    },

    getAllTrials: function (cardinal_expdetthreshold_id) {
        return dbcommon.getAllRowsByKey("cardinal_expdetthreshold_id",
                                        cardinal_expdetthreshold_id, trialtablename,
                                        trialfieldlist, TrialInfo, "id");
    }

});

//=============================================================================
// TASK (inc. webview handler)
//=============================================================================

function logisticFindXWhereP(p, slope, intercept) { // see also maths.jsx
    return (Math.log(p / (1 - p)) - intercept) / slope;
}

function Cardinal_ExpDetThreshold(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
    // Default values:
    this.visual_target_duration_s = 1.0;
    this.background_intensity = 1.0;
    this.start_intensity_min = 0.9;
    this.start_intensity_max = 1.0;
    this.initial_large_intensity_step = 0.1;
    this.main_small_intensity_step = 0.01;
    this.num_trials_in_main_sequence = 14;
    this.p_catch_trial = 0.2;
    this.iti_s = 0.2;
}

lang.inheritPrototype(Cardinal_ExpDetThreshold, taskcommon.BaseTask);
lang.extendPrototype(Cardinal_ExpDetThreshold, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Cardinal_ExpDetThreshold,
    _tablename: maintablename,
    _fieldlist: mainfieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _editable: false,

    // OTHER

    // Override dbdelete():
    dbdelete: function () {
        // The subsidiary table:
        dbcommon.deleteWhere(trialtablename, TRIAL_FK_FIELD, this.id);
        // Then the usual:
        dbcommon.deleteByPK(maintablename, mainfieldlist[0], this);
        // No BLOBs to look after.
    },

    // Override setMoveOffTablet():
    setMoveOffTablet: function (moveoff) {
        var DBCONSTANTS = require('common/DBCONSTANTS');
        this[DBCONSTANTS.MOVE_OFF_TABLET_FIELDNAME] = moveoff;
        this.dbstore();
        dbcommon.setSingleValueByKey(trialtablename, TRIAL_FK_FIELD.name,
                                     this.id,
                                     DBCONSTANTS.MOVE_OFF_TABLET_FIELDSPEC,
                                     moveoff);
        // No BLOBs to look after.
    },

    // Standard task functions
    isComplete: function () {
        return this.finished;
    },

    getDescriptiveModality: function () {
        switch (this.modality) {
        case MODALITY_AUDITORY:
            return L("auditory");
        case MODALITY_VISUAL:
            return L("visual");
        default:
            return L("unknown");
        }
    },

    getTargetName: function () {
        switch (this.modality) {
        case MODALITY_AUDITORY:
            switch (this.target_number) {
            case 0:
                return L("expdetthreshold_auditory_target_0");
            case 1:
                return L("expdetthreshold_auditory_target_1");
            default:
                return L("unknown");
            }
        case MODALITY_VISUAL:
            switch (this.target_number) {
            case 0:
                return L("expdetthreshold_visual_target_0");
            case 1:
                return L("expdetthreshold_visual_target_1");
            default:
                return L("unknown");
            }
        default:
            return L("unknown");
        }
    },

    getSummary: function () {
        return (
            this.getTargetName() +
            ": x75 = " +
            lang.toFixedOrNull(
                    logisticFindXWhereP(0.75, this.slope, this.intercept),
                    DISPLAY_DP
                ) +
            this.isCompleteSuffix()
        );
    },

    getDetail: function () {
        var msg = dbcommon.userObjectMultilineSummary(this, mainfieldlist),
            trials = new TrialInfo().getAllTrials(this.id);
        msg += "\n";
        msg += dbcommon.userObjectArrayCSVDescription(trials, trialfieldlist);
        return msg;
    },

    edit: function () {
        var self = this,
            UICONSTANTS = require('common/UICONSTANTS'),
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire;

        pages = [
            {
                title: L("expdetthreshold_config_title") + " (1)",
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("expdetthreshold_config_main_instructions_1"),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: L("expdetthreshold_config_main_instructions_2")
                    },
                    {
                        type: "QuestionText",
                        text: L("expdetthreshold_config_main_instructions_3")
                    },
                    {
                        type: "QuestionText",
                        text: L("expdetthreshold_config_instructions_1"),
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "modality",
                        options: [
                            new KeyValuePair(L("auditory"), MODALITY_AUDITORY),
                            new KeyValuePair(L("visual"), MODALITY_VISUAL)
                        ]
                    }
                ]
            },
            {
                onTheFly: true,
                pageTag: PAGE_TARGET
            },
            {
                title: L("expdetthreshold_config_title") + " (3)",
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("expdetthreshold_config_info")
                    },
                    {
                        type: "QuestionTypedVariables",
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "visual_target_duration_s",
                                prompt: L("expdet_config_visual_target_duration_s"),
                                min: 0.1,
                                max: 10.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "background_intensity",
                                prompt: L("expdetthreshold_config_background_intensity"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "start_intensity_min",
                                prompt: L("expdetthreshold_config_start_intensity_min"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "start_intensity_max",
                                prompt: L("expdetthreshold_config_start_intensity_max"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "initial_large_intensity_step",
                                prompt: L("expdetthreshold_config_initial_large_intensity_step"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "main_small_intensity_step",
                                prompt: L("expdetthreshold_config_main_small_intensity_step"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "num_trials_in_main_sequence",
                                prompt: L("expdetthreshold_config_num_trials_in_main_sequence"),
                                min: 0,
                                max: 100
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "p_catch_trial",
                                prompt: L("expdetthreshold_config_p_catch_trial"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "iti_s",
                                prompt: L("expdetthreshold_config_iti_s"),
                                min: 0.0,
                                max: 100.0
                            }
                        ]
                    }
                ]
            }
        ];

        questionnaire = new Questionnaire({
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: function (fieldname, getBlobsAsFilenames) {
                return self.defaultGetFieldValueFn(fieldname,
                                                   getBlobsAsFilenames);
            },
            fnSetField: function (fieldname, value) {
                self.defaultSetFieldFn(fieldname, value);
            },
            okIconAtEnd: true,
            /* jshint unused:true */
            fnMakePageOnTheFly: function (currentPage, pageTag) {
                if (pageTag !== PAGE_TARGET) {
                    throw new Error("Cardinal_ExpDetThreshold/fnMakePageOnTheFly: " +
                                    "called for invalid page");
                }
                var elements = [
                    {
                        type: "QuestionText",
                        text: L("expdetthreshold_config_instructions_2"),
                        bold: true
                    }
                ];
                if (self.modality === MODALITY_AUDITORY) {
                    elements.push({
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "target_number",
                        options: [
                            new KeyValuePair(L("expdetthreshold_auditory_target_0"), 0),
                            new KeyValuePair(L("expdetthreshold_auditory_target_1"), 1)
                        ]
                    });
                } else {
                    elements.push({
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "target_number",
                        options: [
                            new KeyValuePair(L("expdetthreshold_visual_target_0"), 0),
                            new KeyValuePair(L("expdetthreshold_visual_target_1"), 1)
                        ]
                    });
                }
                return {
                    title: L("expdetthreshold_config_title") + " (2)",
                    clinician: true,
                    elements: elements
                };
            },
            fnFinished: function (result, editing_time_s) {
                if (result === UICONSTANTS.FINISHED) {
                    // OK! Configured. Proceed.
                    self.editing_time_s += editing_time_s;
                    self.startWebview();
                } else if (result === UICONSTANTS.ABORTED) {
                    self.defaultFinishedFn(result, editing_time_s);
                }
            }
        });

        questionnaire.open();
    },

    startWebview: function () {
        var self = this,
            uifunc = require('lib/uifunc'),
            soundhandler = require('lib/soundhandler'),
            UICONSTANTS = require('common/UICONSTANTS'),
            moment = require('lib/moment'),
            background_duration_ms = null,
            params,
            html,
            window,
            editing_time_start,
            editing_time_end,
            editing_time_s;

        //---------------------------------------------------------------------
        // Finalize parameters
        //---------------------------------------------------------------------
        if (self.modality === MODALITY_AUDITORY) {
            self.background_filename = UICONSTANTS.EXPDET.AUDITORY_BACKGROUND;
            if (self.target_number === 0) {
                self.target_filename = UICONSTANTS.EXPDET.AUDITORY_TARGETS[0];
                self.prompt = (
                    L("expdetthreshold_detection_q_auditory") + " " +
                    L("expdetthreshold_auditory_target_0_short") + "?"
                );
            } else if (self.target_number === 1) {
                self.target_filename = UICONSTANTS.EXPDET.AUDITORY_TARGETS[1];
                self.prompt = (
                    L("expdetthreshold_detection_q_auditory") + " " +
                    L("expdetthreshold_auditory_target_1_short") + "?"
                );
            } else {
                uifunc.alert("Invalid auditory target!");
                return;
            }
        } else if (self.modality === MODALITY_VISUAL) {
            self.background_filename = UICONSTANTS.EXPDET.VISUAL_BACKGROUND;
            if (self.target_number === 0) {
                self.target_filename = UICONSTANTS.EXPDET.VISUAL_TARGETS[0];
                self.prompt = (
                    L("expdetthreshold_detection_q_visual") + " " +
                    L("expdetthreshold_visual_target_0_short") + "?"
                );
            } else if (self.target_number === 1) {
                self.target_filename = UICONSTANTS.EXPDET.VISUAL_TARGETS[1];
                self.prompt = (
                    L("expdetthreshold_detection_q_visual") + " " +
                    L("expdetthreshold_visual_target_1_short") + "?"
                );
            } else {
                uifunc.alert("Invalid visual target!");
                return;
            }
        } else {
            uifunc.alert("Invalid modality!");
            return;
        }

        //---------------------------------------------------------------------
        // Save finalized parameters
        //---------------------------------------------------------------------
        self.dbstore();

        //---------------------------------------------------------------------
        // Preload sounds
        //---------------------------------------------------------------------
        if (self.modality === MODALITY_AUDITORY) {
            background_duration_ms = soundhandler.loadSound({
                filename: self.background_filename,
                volume: self.background_intensity
            });
            soundhandler.loadSound({
                filename: self.target_filename,
                volume: 1.0
            });
        }

        //---------------------------------------------------------------------
        // Communication with webview
        //---------------------------------------------------------------------
        params = {
            cardinal_expdetthreshold_id: self.id,
            background_duration_ms: background_duration_ms,
            STIMHEIGHT: UICONSTANTS.EXPDET.STIM_SIZE,
            STIMWIDTH: UICONSTANTS.EXPDET.STIM_SIZE,
            OPTION_YES: L("Yes"),
            OPTION_NO: L("No"),
            TEXT_THANKS: L("webview_thanks"),
            TEXT_ABORT: L("abort"),
            TEXT_START: L("expdetthreshold_start_prompt"),
            INSTRUCTIONS_1: L("expdet_instructions_1"),
            INSTRUCTIONS_2: L("expdet_instructions_2"),
            INSTRUCTIONS_3: L("expdet_instructions_3"),
            SAVING_PLEASE_WAIT: L("saving_please_wait")
        };
        dbcommon.copyFields(configfieldlist, self, params);
        html = taskcommon.loadHtmlSetParams(
            'task_html/cardinal_expdetthreshold_task.html',
            params,
            'task_html/cardinal_expdetthreshold_task.jsx'
        );

        function eventFromWebView(e) {
            var dict,
                trialinfo,
                cleanFinish;
            Titanium.API.trace("Cardinal_ExpDetThreshold: eventFromWebView: " + e.eventType);
            if (taskcommon.processWebviewSoundRequest(e, EVENT_TO_WEBVIEW)) {
                return;
            }
            switch (e.eventType) {

            case "savemain":
                dict = taskcommon.parseDataFromWebview(e.data);
                lang.copyProperties(dict, self);
                self.dbstore();
                break;

            case "savetrial":
                dict = taskcommon.parseDataFromWebview(e.data);
                trialinfo = new TrialInfo({
                    cardinal_expdetthreshold_id: self.id,
                    trial: dict.trial // this trial record might already exist, so try to load it
                });
                trialinfo.setFromDictAndSave(dict);
                break;

            case "exit":
            case "abort":
                editing_time_end = moment();
                editing_time_s = editing_time_end.diff(editing_time_start,
                                                       'seconds',
                                                       true);  // floating-point
                cleanFinish = (e.eventType === "exit");
                self.defaultFinishedFn(
                    cleanFinish ?
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

module.exports = Cardinal_ExpDetThreshold;
