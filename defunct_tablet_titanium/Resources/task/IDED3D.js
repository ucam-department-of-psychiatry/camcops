// IDED3D.js

/*
    Copyright (C) 2015-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.

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

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    platform = require('lib/platform'),
    //-------------------------------------------------------------------------
    // PER-SESSION TABLE (see also below)
    //-------------------------------------------------------------------------
    maintablename = "ided3d",
    mainfieldlist = dbcommon.standardTaskFields(),
    configfieldlist = [
        // Config
        {name: 'last_stage', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'max_trials_per_stage', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'progress_criterion_x', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'progress_criterion_y', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'min_number', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'max_number', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'pause_after_beep_ms', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'iti_ms', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'counterbalance_dimensions', type: DBCONSTANTS.TYPE_INTEGER},
        {name: 'volume', type: DBCONSTANTS.TYPE_REAL},
        {name: 'offer_abort', type: DBCONSTANTS.TYPE_BOOLEAN},
        {name: 'debug_display_stimuli_only', type: DBCONSTANTS.TYPE_BOOLEAN}
    ],
    //-------------------------------------------------------------------------
    // PER-STAGE TABLE (see also below)
    //-------------------------------------------------------------------------
    stagetablename = "ided3d_stages",
    STAGE_FK_FIELD = {
        name: 'ided3d_id',
        type: DBCONSTANTS.TYPE_INTEGER,
        mandatory: true
    }, // FK to ided3d.id
    stagefieldlist = dbcommon.standardAncillaryFields(STAGE_FK_FIELD),
    //-------------------------------------------------------------------------
    // PER-TRIAL TABLE (see also below)
    //-------------------------------------------------------------------------
    trialtablename = "ided3d_trials",
    TRIAL_FK_FIELD = {
        name: 'ided3d_id',
        type: DBCONSTANTS.TYPE_INTEGER,
        mandatory: true
    }, // FK to ided3d.id
    trialfieldlist = dbcommon.standardAncillaryFields(TRIAL_FK_FIELD),
    //-------------------------------------------------------------------------
    // Other
    //-------------------------------------------------------------------------
    EVENT_FROM_WEBVIEW = 'IDED3D_EVENT_FROM_WEBVIEW',
    // EVENT_TO_WEBVIEW = 'IDED3D_EVENT_TO_WEBVIEW',
    // DISPLAY_DP = 3,
    MAX_STAGES = 8,
    MAX_NUMBER = 9,
    MAX_COUNTERBALANCE_DIMENSIONS = 5,
    CORRECT_SOUND_FILENAME = platform.translateFilename(
        'sounds/ided3d/correct.wav'
    ),
    INCORRECT_SOUND_FILENAME = platform.translateFilename(
        'sounds/ided3d/incorrect.wav'
    );

mainfieldlist = mainfieldlist.concat(configfieldlist);
mainfieldlist.push(
    // Config stuff sent to us from the webview
    {name: 'shape_definitions_svg', type: DBCONSTANTS.TYPE_TEXT},
    // Results from task HTML proper
    {name: 'aborted', type: DBCONSTANTS.TYPE_BOOLEAN, defaultValue: false},
    {name: 'finished', type: DBCONSTANTS.TYPE_BOOLEAN, defaultValue: false},
    {name: 'last_trial_completed', type: DBCONSTANTS.TYPE_INTEGER}
);
stagefieldlist.push(
    // More keys
    {name: 'stage', type: DBCONSTANTS.TYPE_INTEGER, mandatory: true}, // 1-based stage number within this session
    // Config
    {name: 'stage_name', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'relevant_dimension', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'correct_exemplar', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'incorrect_exemplar', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'correct_stimulus_shapes', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'correct_stimulus_colours', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'correct_stimulus_numbers', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'incorrect_stimulus_shapes', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'incorrect_stimulus_colours', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'incorrect_stimulus_numbers', type: DBCONSTANTS.TYPE_TEXT},
    // Results
    {name: 'first_trial_num', type: DBCONSTANTS.TYPE_INTEGER},  // 1-based
    {name: 'n_completed_trials', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'n_correct', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'n_incorrect', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'stage_passed', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'stage_failed', type: DBCONSTANTS.TYPE_BOOLEAN}
);
trialfieldlist.push(
    // More keys
    {name: 'trial', type: DBCONSTANTS.TYPE_INTEGER, mandatory: true}, // 1-based trial number within this session
    {name: 'stage', type: DBCONSTANTS.TYPE_INTEGER},
    // Locations
    {name: 'correct_location', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'incorrect_location', type: DBCONSTANTS.TYPE_INTEGER},
    // Stimuli
    {name: 'correct_shape', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'correct_colour', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'correct_number', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'incorrect_shape', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'incorrect_colour', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'incorrect_number', type: DBCONSTANTS.TYPE_INTEGER},
    // Trial
    {name: 'trial_start_time', type: DBCONSTANTS.TYPE_DATETIME},
    // Response
    {name: 'responded', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'response_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'response_latency_ms', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'correct', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'incorrect', type: DBCONSTANTS.TYPE_BOOLEAN}
);

// CREATE THE TABLES

dbcommon.createTable(maintablename, mainfieldlist);
dbcommon.createTable(stagetablename, stagefieldlist);
dbcommon.createTable(trialtablename, trialfieldlist);

//=============================================================================
// Stage info record class
//=============================================================================

function StageInfo(props) {
    dbcommon.DatabaseObject.call(this); // call base constructor
    // Instantiate with some combination of IDs, if specified (will read from the database if enough info given)
    dbcommon.loadOrCreateAncillary(this, props, "ided3d_id", "stage");
}
lang.inheritPrototype(StageInfo, dbcommon.DatabaseObject);
lang.extendPrototype(StageInfo, {
    // KEY DATABASE FIELDS (USED BY DatabaseObject)
    _objecttype: StageInfo,
    _tablename: stagetablename,
    _fieldlist: stagefieldlist,
    _sortorder: "id",
    // OTHER
    setFromDictAndSave: function (dict) {
        dbcommon.copyFields(stagefieldlist, dict, this, 1); // skips first field (PK)
        this.dbstore();
    },
    getAllStages: function (ided3d_id) {
        return dbcommon.getAllRowsByKey("ided3d_id",
                                        ided3d_id, stagetablename,
                                        stagefieldlist, StageInfo, "id");
    }
});

//=============================================================================
// Trial info record class
//=============================================================================

function TrialInfo(props) {
    dbcommon.DatabaseObject.call(this); // call base constructor
    // Instantiate with some combination of IDs, if specified (will read from the database if enough info given)
    dbcommon.loadOrCreateAncillary(this, props, "ided3d_id", "trial");
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
    getAllTrials: function (ided3d_id) {
        return dbcommon.getAllRowsByKey("ided3d_id",
                                        ided3d_id, trialtablename,
                                        trialfieldlist, TrialInfo, "id");
    }
});

//=============================================================================
// TASK (inc. webview handler)
//=============================================================================

function IDED3D(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
    // Default values:
    this.last_stage = MAX_STAGES;
    this.max_trials_per_stage = 50;
    this.progress_criterion_x = 6;  // as per Rogers et al. 1999
    this.progress_criterion_y = 6;  // as per Rogers et al. 1999
    this.min_number = 1;
    this.max_number = MAX_NUMBER;
    this.pause_after_beep_ms = 500;
    this.iti_ms = 500;
    // ... no default for counterbalancing
    this.volume = 1.0;
    this.offer_abort = false;
    this.debug_display_stimuli_only = false;
}

lang.inheritPrototype(IDED3D, taskcommon.BaseTask);
lang.extendPrototype(IDED3D, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: IDED3D,
    _tablename: maintablename,
    _fieldlist: mainfieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _editable: false,

    // OTHER

    // Override dbdelete():
    dbdelete: function () {
        // The subsidiary tables:
        dbcommon.deleteWhere(stagetablename, STAGE_FK_FIELD, this.id);
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
        dbcommon.setSingleValueByKey(stagetablename, STAGE_FK_FIELD.name,
                                     this.id,
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
        var trials = new TrialInfo().getAllTrials(this.id),
            msg = "Performed " + trials.length + " trials";
        if (trials.length === 0) {
            return msg;
        }
        return (
            msg + "; last trial was at stage " +
            trials[trials.length - 1].stage
        );
    },

    getDetail: function () {
        var msg = dbcommon.userObjectMultilineSummary(this, mainfieldlist),
            stages = new StageInfo().getAllStages(this.id),
            trials = new TrialInfo().getAllTrials(this.id);
        msg += "\n";
        msg += dbcommon.userObjectArrayCSVDescription(stages, stagefieldlist);
        msg += "\n";
        msg += dbcommon.userObjectArrayCSVDescription(trials, trialfieldlist);
        return msg;
    },

    edit: function () {
        var self = this,
            UICONSTANTS = require('common/UICONSTANTS'),
            Questionnaire = require('questionnaire/Questionnaire'),
            pages,
            questionnaire;

        pages = [
            {
                title: L("t_ided3d"),
                clinician: true,
                elements: [
                    {
                        type: "QuestionTypedVariables",
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "last_stage",
                                prompt: L("ided3d_last_stage"),
                                min: 1,
                                max: MAX_STAGES
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "max_trials_per_stage",
                                prompt: L("ided3d_max_trials_per_stage"),
                                min: 1
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "progress_criterion_x",
                                prompt: L("ided3d_progress_criterion_x"),
                                min: 1
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "progress_criterion_y",
                                prompt: L("ided3d_progress_criterion_y"),
                                min: 1
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "min_number",
                                prompt: L("ided3d_min_number"),
                                min: 1,
                                max: MAX_NUMBER
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "max_number",
                                prompt: L("ided3d_max_number"),
                                min: 1,
                                max: MAX_NUMBER
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "pause_after_beep_ms",
                                prompt: L("ided3d_pause_after_beep_ms"),
                                min: 0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "iti_ms",
                                prompt: L("ided3d_iti_ms"),
                                min: 0
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "counterbalance_dimensions",
                                prompt: L("ided3d_counterbalance_dimensions"),
                                min: 0,
                                max: MAX_COUNTERBALANCE_DIMENSIONS
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "volume",
                                prompt: L("volume"),
                                min: 0.0,
                                max: 1.0
                            }
                        ]
                    },
                    {
                        type: "QuestionBooleanText",
                        text: L("ided3d_offer_abort"),
                        field: "offer_abort",
                        bold: false
                    },
                    {
                        type: "QuestionBooleanText",
                        text: L("ided3d_debug_display_stimuli_only"),
                        field: "debug_display_stimuli_only",
                        bold: false
                    }
                ]
            }
        ];

        questionnaire = new Questionnaire({
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            okIconAtEnd: true,
            fnShowNext: function (currentPage, pageTag) {
                if (self.progress_criterion_x > self.progress_criterion_y) {
                    return {care: true, showNext: false};
                }
                return {care: false};
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
            params,
            html,
            window,
            correct_sound_duration_ms = null,
            incorrect_sound_duration_ms = null,
            editing_time_start,
            editing_time_end,
            editing_time_s;

        //---------------------------------------------------------------------
        // Finalize parameters
        //---------------------------------------------------------------------
        if (self.min_number < 1) {
            uifunc.alert("Minimum number must be >= 1");
            return;
        }
        if (self.min_number > MAX_NUMBER) {
            uifunc.alert("Maximum number must be <= " + MAX_NUMBER);
            return;
        }
        if (self.min_number > self.max_number) {
            uifunc.alert("Minimum number exceeds maximum number");
            return;
        }
        if (self.counterbalance_dimensions < 0) {
            uifunc.alert("counterbalance_dimensions must be >= 0");
            return;
        }
        if (self.counterbalance_dimensions > MAX_COUNTERBALANCE_DIMENSIONS) {
            uifunc.alert("counterbalance_dimensions must be <= " +
                         MAX_COUNTERBALANCE_DIMENSIONS);
            return;
        }

        //---------------------------------------------------------------------
        // Save finalized parameters
        //---------------------------------------------------------------------
        self.dbstore();

        //---------------------------------------------------------------------
        // Preload sounds
        //---------------------------------------------------------------------
        correct_sound_duration_ms = soundhandler.loadSound({
            filename: CORRECT_SOUND_FILENAME,
            volume: self.volume
        });
        incorrect_sound_duration_ms = soundhandler.loadSound({
            filename: INCORRECT_SOUND_FILENAME,
            volume: self.volume
        });

        //---------------------------------------------------------------------
        // Communication with webview
        //---------------------------------------------------------------------
        params = {
            // Key
            ided3d_id: self.id,
            // Config: see copyFields below
            // Constants
            correct_sound_duration_ms: correct_sound_duration_ms,
            incorrect_sound_duration_ms: incorrect_sound_duration_ms,
            CORRECT: L("correct"),
            INCORRECT: L("wrong"),
            TEXT_THANKS: L("webview_thanks"),
            TEXT_ABORT: L("abort"),
            TEXT_START: L("expdetthreshold_start_prompt"),
            INSTRUCTIONS: L("ided3d_instructions"),
            SAVING_PLEASE_WAIT: L("saving_please_wait")
        };
        dbcommon.copyFields(configfieldlist, self, params);
        html = taskcommon.loadHtmlSetParams(
            'task_html/ided3d_task.html',
            params,
            'task_html/ided3d_task.jsx'
        );

        function eventFromWebView(e) {
            var dict,
                stageinfo,
                trialinfo,
                cleanFinish;
            Titanium.API.trace("IDED3D: eventFromWebView: " + e.eventType);
            switch (e.eventType) {
            case "correctsound":
                soundhandler.playSound(CORRECT_SOUND_FILENAME);
                break;

            case "incorrectsound":
                soundhandler.playSound(INCORRECT_SOUND_FILENAME);
                break;

            case "saveshapes":
                // e.data is a JSON.stringify()'d version of the shapedefs,
                // which we'd like to store directly.
                self.shape_definitions_svg = e.data;
                self.dbstore();
                break;

            case "savestage":
                dict = taskcommon.parseDataFromWebview(e.data);
                stageinfo = new StageInfo({
                    ided3d_id: self.id,
                    stage: dict.stage // this stage record might already exist, so try to load it
                });
                stageinfo.setFromDictAndSave(dict);
                break;

            case "savetrial":
                dict = taskcommon.parseDataFromWebview(e.data);
                trialinfo = new TrialInfo({
                    ided3d_id: self.id,
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
    }

});

module.exports = IDED3D;
