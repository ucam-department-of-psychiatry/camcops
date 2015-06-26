// Cardinal_ExpectationDetection.js

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    N_CUES = 8, // see also magic numbers in startWebview
    // PER-SESSION TABLE (mostly config)
    maintablename = "cardinal_expdet",
    mainfieldlist = dbcommon.standardTaskFields(),
    configfieldlist = [
        // Config
        {name: 'num_blocks', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'stimulus_counterbalancing', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'is_detection_response_on_right', type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: 'pause_every_n_trials', type: DBCONSTANTS.TYPE_BOOLEAN},
        // ... cue
        {name: 'cue_duration_s', type: DBCONSTANTS.TYPE_REAL},
        {name: 'visual_cue_intensity', type: DBCONSTANTS.TYPE_REAL},
        {name: 'auditory_cue_intensity', type: DBCONSTANTS.TYPE_REAL},
        // ... ISI
        {name: 'isi_duration_s', type: DBCONSTANTS.TYPE_REAL},
        // ... target
        {name: 'visual_target_duration_s', type: DBCONSTANTS.TYPE_REAL},
        {name: 'visual_background_intensity', type: DBCONSTANTS.TYPE_REAL}, // 0 to 1
        {name: 'visual_target_0_intensity', type: DBCONSTANTS.TYPE_REAL}, // 0 to 1
        {name: 'visual_target_1_intensity', type: DBCONSTANTS.TYPE_REAL}, // 0 to 1
        {name: 'auditory_background_intensity', type: DBCONSTANTS.TYPE_REAL}, // 0 to 1
        {name: 'auditory_target_0_intensity', type: DBCONSTANTS.TYPE_REAL}, // 0 to 1
        {name: 'auditory_target_1_intensity', type: DBCONSTANTS.TYPE_REAL}, // 0 to 1
        // ... ITI
        {name: 'iti_min_s', type: DBCONSTANTS.TYPE_REAL},
        {name: 'iti_max_s', type: DBCONSTANTS.TYPE_REAL},
    ],
    // PER-GROUP-SPEC TABLE (config)
    trialgroupspectablename = "cardinal_expdet_trialgroupspec",
    TRIALGROUPSPEC_FK_FIELD = {
        name: 'cardinal_expdet_id',
        type: DBCONSTANTS.TYPE_INTEGER,
        mandatory: true
    }, // FK to cardinal_expdet.id
    trialgroupspecfieldlist = dbcommon.standardAncillaryFields(
        TRIALGROUPSPEC_FK_FIELD
    ),
    trialgroupspecconfigfieldlist = [
        // More keys
        {name: 'group_num', type: DBCONSTANTS.TYPE_INTEGER, mandatory: true}, // sequence within a session
        // Group spec
        {name: 'cue', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'target_modality', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'target_number', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'n_target', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'n_no_target', type: DBCONSTANTS.TYPE_INTEGER}
    ],
    // PER-TRIAL TABLE (config and results)
    // If these are edited, then the webview's return event should also be edited.
    trialtablename = "cardinal_expdet_trials",
    TRIAL_FK_FIELD = {
        name: 'cardinal_expdet_id',
        type: DBCONSTANTS.TYPE_INTEGER,
        mandatory: true
    }, // FK to cardinal_expdet.id
    trialfieldlist = dbcommon.standardAncillaryFields(TRIAL_FK_FIELD),
    EVENT_FROM_WEBVIEW = 'EXPDET_EVENT_FROM_WEBVIEW',
    EVENT_TO_WEBVIEW = 'EXPDET_EVENT_TO_WEBVIEW';


mainfieldlist = mainfieldlist.concat(configfieldlist);
mainfieldlist.push(
    // Results
    {name: 'aborted', type: DBCONSTANTS.TYPE_BOOLEAN, defaultValue: false},
    {name: 'finished', type: DBCONSTANTS.TYPE_BOOLEAN, defaultValue: false},
    {name: 'last_trial_completed', type: DBCONSTANTS.TYPE_INTEGER}
);

trialgroupspecfieldlist = trialgroupspecfieldlist.concat(trialgroupspecconfigfieldlist);

trialfieldlist.push(
    // More keys
    {name: 'trial', type: DBCONSTANTS.TYPE_INTEGER, mandatory: true}, // trial number within this session
    // Task determines these (via an autogeneration process from the config):
    {name: 'block', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'group_num', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'cue', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'raw_cue_number', type: DBCONSTANTS.TYPE_INTEGER}, // following counterbalancing
    {name: 'target_modality', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'target_number', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'target_present', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'iti_length_s', type: DBCONSTANTS.TYPE_REAL},
    // Task determines these (on the fly):
    {name: 'pause_given_before_trial', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'pause_start_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'pause_end_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'trial_start_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'cue_start_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'target_start_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'detection_start_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'iti_start_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'iti_end_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'trial_end_time', type: DBCONSTANTS.TYPE_DATETIME},
    // Subject decides these:
    {name: 'responded', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'response_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'response_latency_ms', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'rating', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'correct', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'points', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'cumulative_points', type: DBCONSTANTS.TYPE_INTEGER}
);

// CREATE THE TABLES

dbcommon.createTable(maintablename, mainfieldlist);
dbcommon.createTable(trialgroupspectablename, trialgroupspecfieldlist);
dbcommon.createTable(trialtablename, trialfieldlist);

//=============================================================================
// Group spec record class
//=============================================================================

function TrialGroupSpec(props) {
    dbcommon.DatabaseObject.call(this); // call base constructor
    // Instantiate with some combination of IDs, if specified (will read from the database if enough info given)
    dbcommon.loadOrCreateAncillary(this, props, "cardinal_expdet_id", "group_num");
}
lang.inheritPrototype(TrialGroupSpec, dbcommon.DatabaseObject);
lang.extendPrototype(TrialGroupSpec, {
    // KEY DATABASE FIELDS (USED BY DatabaseObject)
    _objecttype: TrialGroupSpec,
    _tablename: trialgroupspectablename,
    _fieldlist: trialgroupspecfieldlist,
    _sortorder: "id",

    // OTHER

    getAllGroupSpecs: function (cardinal_expdet_id) {
        return dbcommon.getAllRowsByKey("cardinal_expdet_id",
                                        cardinal_expdet_id,
                                        trialgroupspectablename,
                                        trialgroupspecfieldlist,
                                        TrialGroupSpec, "id");
    },

});

//=============================================================================
// Trial info record class
//=============================================================================

function TrialInfo(props) {
    dbcommon.DatabaseObject.call(this); // call base constructor
    // Instantiate with some combination of IDs, if specified (will read from
    // the database if enough info given)
    dbcommon.loadOrCreateAncillary(this, props, "cardinal_expdet_id",
                                   "trial");
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

    getAllTrials: function (cardinal_expdet_id) {
        return dbcommon.getAllRowsByKey("cardinal_expdet_id",
                                        cardinal_expdet_id,
                                        trialtablename, trialfieldlist,
                                        TrialInfo, "id");
    },

});

//=============================================================================
// TASK (inc. webview handler)
//=============================================================================

function Cardinal_ExpectationDetection(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
    // Default values:
    this.num_blocks = 8;
    this.is_detection_response_on_right = true;
    this.pause_every_n_trials = 20;
    // ... cue
    this.cue_duration_s = 1.0;
    this.visual_cue_intensity = 1.0;
    this.auditory_cue_intensity = 1.0;
    // ... ISI
    this.isi_duration_s = 0.2;
    // ... target
    this.visual_target_duration_s = 1.0; // to match auditory
    this.visual_background_intensity = 1.0;
    this.auditory_background_intensity = 1.0;
    // ... ITI
    this.iti_min_s = 0.2;
    this.iti_max_s = 0.8;
}

lang.inheritPrototype(Cardinal_ExpectationDetection, taskcommon.BaseTask);
lang.extendPrototype(Cardinal_ExpectationDetection, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Cardinal_ExpectationDetection,
    _tablename: maintablename,
    _fieldlist: mainfieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _editable: false,

    // OTHER

    // Override dbdelete():
    dbdelete: function () {
        // The subsidiary tables:
        dbcommon.deleteWhere(trialgroupspectablename, TRIALGROUPSPEC_FK_FIELD,
                             this.id);
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
        dbcommon.setSingleValueByKey(trialgroupspectablename,
                                     TRIALGROUPSPEC_FK_FIELD.name, this.id,
                                     DBCONSTANTS.MOVE_OFF_TABLET_FIELDSPEC,
                                     moveoff);
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

    getSummary: function () {
        return "No summary; see detail" + this.isCompleteSuffix();
    },

    getDetail: function () {
        var msg = dbcommon.userObjectMultilineSummary(this, mainfieldlist),
            trials = new TrialInfo().getAllTrials(this.id),
            groups = new TrialGroupSpec().getAllGroupSpecs(this.id);
        msg += "\n";
        msg += dbcommon.userObjectArrayCSVDescription(trials, trialfieldlist);
        msg += "\n";
        msg += dbcommon.userObjectArrayCSVDescription(groups,
                                                      trialgroupspecfieldlist);
        return msg;
    },

    edit: function () {
        var self = this,
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            pages,
            questionnaire;

        pages = [
            {
                title: L("expdet_config_title"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: L("expdet_config_instructions_1"),
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "stimulus_counterbalancing",
                                prompt: L("expdet_config_stimulus_counterbalancing"),
                                min: 0,
                                max: N_CUES - 1
                            },
                        ],
                    },
                    {
                        type: "QuestionText",
                        text: L("expdet_config_instructions_2"),
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "auditory_target_0_intensity",
                                prompt: (
                                    L("expdet_config_intensity_prefix") + " " +
                                    L("expdetthreshold_auditory_target_0")
                                ),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "auditory_target_1_intensity",
                                prompt: (
                                    L("expdet_config_intensity_prefix") + " " +
                                    L("expdetthreshold_auditory_target_1")
                                ),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "visual_target_0_intensity",
                                prompt: (
                                    L("expdet_config_intensity_prefix") + " " +
                                    L("expdetthreshold_visual_target_0")
                                ),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "visual_target_1_intensity",
                                prompt: (
                                    L("expdet_config_intensity_prefix") + " " +
                                    L("expdetthreshold_visual_target_1")
                                ),
                                min: 0.0,
                                max: 1.0
                            },
                        ],
                    },
                    {
                        type: "QuestionText",
                        text: L("expdet_config_instructions_3"),
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "num_blocks",
                                prompt: L("expdet_config_num_blocks"),
                                min: 1,
                                max: 100
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "iti_min_s",
                                prompt: L("expdet_config_iti_min_s"),
                                min: 0.1,
                                max: 100.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "iti_max_s",
                                prompt: L("expdet_config_iti_max_s"),
                                min: 0.1,
                                max: 100.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "pause_every_n_trials",
                                prompt: L("expdet_config_pause_every_n_trials"),
                                min: 0,
                                max: 100
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "cue_duration_s",
                                prompt: L("expdet_config_cue_duration_s"),
                                min: 0.1,
                                max: 10.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "visual_cue_intensity",
                                prompt: L("expdet_config_visual_cue_intensity"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "auditory_cue_intensity",
                                prompt: L("expdet_config_auditory_cue_intensity"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "visual_target_duration_s",
                                prompt: L("expdet_config_visual_target_duration_s"),
                                min: 0.1,
                                max: 10.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "visual_background_intensity",
                                prompt: L("expdet_config_visual_background_intensity"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "auditory_background_intensity",
                                prompt: L("expdet_config_auditory_background_intensity"),
                                min: 0.0,
                                max: 1.0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "isi_duration_s",
                                prompt: L("expdet_config_isi_duration_s"),
                                min: 0.0,
                                max: 100.0
                            },
                        ],
                    },
                    {
                        type: "QuestionBooleanText",
                        field: "is_detection_response_on_right",
                        text: L("expdet_config_is_detection_response_on_right"),
                        bold: false
                    },
                ],
            },
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
            lang = require('lib/lang'),
            soundhandler = require('lib/soundhandler'),
            UICONSTANTS = require('common/UICONSTANTS'),
            moment = require('lib/moment'),
            i,
            gs,
            auditory_background_duration_ms = soundhandler.loadSound({
                filename: UICONSTANTS.EXPDET.AUDITORY_BACKGROUND,
                volume: self.auditory_background_intensity
            }),
            volume,
            params,
            html,
            window,
            editing_time_start,
            editing_time_end,
            editing_time_s;

        //---------------------------------------------------------------------
        // Finalize parameters
        //---------------------------------------------------------------------
        self.dbstore(); // generates self.id (may be blank if all defaults were accepted in questionnaire)
        self.trialGroupSpecs = [];
        for (i = 0; i < 8; ++i) {
            gs = new TrialGroupSpec({ cardinal_expdet_id: self.id });
            gs.group_num = i;
            // CUE             00 01 02 03 04 05 06 07
            // TARGET_MODALITY  0  0  0  0  1  1  1  1  } define the four target types
            // TARGET_NUMBER    0  0  1  1  0  0  1  1  }
            // N_TARGET         2  1  2  1  2  1  2  1    } define the high-/low-probability cues
            // N_NO_TARGET      1  2  1  2  1  2  1  2    }
            gs.cue = i;
            gs.target_modality = lang.div(i, 4);
            gs.target_number   = lang.div(i, 2) % 2;
            gs.n_target =    (i % 2 === 0) ? 2 : 1;
            gs.n_no_target = (i % 2 === 0) ? 1 : 2;

            gs.dbstore();
            self.trialGroupSpecs.push(gs);
        }
        // ... gives 24 trials per block

        //---------------------------------------------------------------------
        // Save finalized parameters
        //---------------------------------------------------------------------
        self.dbstore();

        // Preload sounds
        for (i = 0; i < UICONSTANTS.EXPDET.AUDITORY_CUES.length; ++i) {
            soundhandler.loadSound({
                filename: UICONSTANTS.EXPDET.AUDITORY_CUES[i],
                volume: self.auditory_cue_intensity
            });
        }
        for (i = 0; i < UICONSTANTS.EXPDET.AUDITORY_TARGETS.length; ++i) {
            volume = (i === 0 ?
                    self.auditory_target_0_intensity :
                    self.auditory_target_1_intensity);
            soundhandler.loadSound({
                filename: UICONSTANTS.EXPDET.AUDITORY_TARGETS[i],
                volume: volume
            });
            Titanium.API.trace("Loading target " + i + ", intensity " + volume);
        }

        //---------------------------------------------------------------------
        // Communication with webview
        //---------------------------------------------------------------------
        params = {
            cardinal_expdet_id: self.id,
            trialGroupSpecs: dbcommon.copyRecordArray(
                self.trialGroupSpecs,
                trialgroupspecconfigfieldlist
            ),
            trialfieldlist: trialfieldlist,
            EXPDET_AUDITORY_CUES: UICONSTANTS.EXPDET.AUDITORY_CUES,
            EXPDET_AUDITORY_TARGETS: UICONSTANTS.EXPDET.AUDITORY_TARGETS,
            EXPDET_AUDITORY_BACKGROUND: UICONSTANTS.EXPDET.AUDITORY_BACKGROUND,
            EXPDET_VISUAL_CUES: UICONSTANTS.EXPDET.VISUAL_CUES,
            EXPDET_VISUAL_TARGETS: UICONSTANTS.EXPDET.VISUAL_TARGETS,
            EXPDET_VISUAL_BACKGROUND: UICONSTANTS.EXPDET.VISUAL_BACKGROUND,
            N_CUES: N_CUES,
            auditory_background_duration_ms: auditory_background_duration_ms,
            VISUAL_PROMPTS: [
                L("expdet_detection_q_prefix") + " " +
                    L("expdet_detection_q_visual") + " " +
                    L("expdetthreshold_visual_target_0_short") + "?",
                L("expdet_detection_q_prefix") + " " +
                    L("expdet_detection_q_visual") + " " +
                    L("expdetthreshold_visual_target_1_short") + "?",
            ],
            AUDITORY_PROMPTS: [
                L("expdet_detection_q_prefix") + " " +
                    L("expdet_detection_q_auditory") + " " +
                    L("expdetthreshold_auditory_target_0_short") + "?",
                L("expdet_detection_q_prefix") + " " +
                    L("expdet_detection_q_auditory") + " " +
                    L("expdetthreshold_auditory_target_1_short") + "?",
            ],
            DETECTION_OPTIONS: [
                L("expdet_option_0"),
                L("expdet_option_1"),
                L("expdet_option_2"),
                L("expdet_option_3"),
                L("expdet_option_4"),
            ],
            STIMHEIGHT: UICONSTANTS.EXPDET.STIM_SIZE,
            STIMWIDTH: UICONSTANTS.EXPDET.STIM_SIZE,
            PAUSE_PROMPT: L("expdet_pause_prompt"),
            N_TRIALS_LEFT_MSG: L("expdet_num_trials_left"),
            TIME_LEFT_MSG: L("expdet_time_left"),
            TEXT_THANKS: L("webview_thanks"),
            TEXT_ABORT: L("abort"),
            TEXT_POINTS: L("expdet_points"),
            TEXT_CUMULATIVE_POINTS: L("expdet_cumulative_points"),
            TEXT_START: L("expdetthreshold_start_prompt"),
            INSTRUCTIONS_1: L("expdet_instructions_1"),
            INSTRUCTIONS_2: L("expdet_instructions_2"),
            INSTRUCTIONS_3: L("expdet_instructions_3"),
            TEXT_REALLY_ABORT: L("webview_really_abort"),
            TEXT_CANCEL: L("cancel"),
            SAVING_PLEASE_WAIT: L("saving_please_wait"),
        };
        dbcommon.copyFields(configfieldlist, self, params);
        html = taskcommon.loadHtmlSetParams(
            'task_html/cardinal_expdet_task.html',
            params,
            'task_html/cardinal_expdet_task.jsx'
        );

        function eventFromWebView(e) {
            var dict,
                trialinfo,
                cleanFinish;
            Titanium.API.trace("ExpDet: eventFromWebView: " + e.eventType);
            if (taskcommon.processWebviewSoundRequest(e, EVENT_TO_WEBVIEW)) {
                return;
            }
            switch (e.eventType) {

            case "savetrial":
                dict = taskcommon.parseDataFromWebview(e.data);
                trialinfo = new TrialInfo({
                    cardinal_expdet_id: self.id,
                    trial: dict.trial // this trial record might already exist, so try to load it
                });
                trialinfo.setFromDictAndSave(dict);
                self.defaultSetFieldFn("last_trial_completed",
                                       trialinfo.trial);
                break;

            case "exit":
            case "abort":
                editing_time_end = moment();
                editing_time_s = editing_time_end.diff(editing_time_start,
                                                       'seconds',
                                                       true);  // floating-point
                cleanFinish = (e.eventType === "exit");
                if (cleanFinish) {
                    self.defaultSetFieldFn("finished", true);
                } else {
                    self.defaultSetFieldFn("aborted", true);
                }
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
    },

});

module.exports = Cardinal_ExpectationDetection;
