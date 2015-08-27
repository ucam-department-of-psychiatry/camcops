// cardinal_expdetthreshold_task.jsx

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

/*jslint node: true */
"use strict";
/*global unescape */
/*global inTitanium, trace, now, sendEvent,
    preprocess_moments_for_json_stringify,
    randomFloatBetween, randomBool, clip,
    createText, createButton,
    setTouchStartEvent, clearTouchEvents,
    setVolume, playSound,
    assert, copyProperties,
    registerWebviewTask
*/
/*global logisticFitSinglePredictor, logisticDescriptives */
/*global Raphael */

//=============================================================================
// Comments
//=============================================================================
// - Trials are analysed and (in part) numbered retrospectively, so the
//   task does need an array of all trials.

//=============================================================================
// Communication with the "outside world": see taskhtmlcommon.js
//=============================================================================
// Must receive task parameters, and provide incomingEvent(), startTask()

function incomingEvent(e) {
    trace("incomingEvent: " + JSON.stringify(e));
}

    //-------------------------------------------------------------------------
    // Incoming task parameters
    //-------------------------------------------------------------------------
var tp = (inTitanium ?
        //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        // Titanium: config is passed here by replacing this literal:
        //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        JSON.parse(unescape("INSERT_paramsString")) :

        //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        // Web browser debugging (much quicker): test parameters
        //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        {
            // Asus Eee Pad is 1200 x 800 (WXGA), effective size (minus system
            // UI) 1200 x 752. iPad is 1024 x 768
            screenWidth: 1024,
            screenHeight: 752
        }
    ),
    TASKNAME = "ExpDetThreshold HTML/JS",
    EVENTNAME_OUT = "EXPDETTHRESHOLD_EVENT_FROM_WEBVIEW",
    EVENTNAME_IN = "EXPDETTHRESHOLD_EVENT_TO_WEBVIEW",
    SOUND_COMPLETE_EVENT = "soundFinished",
    MODALITY_AUDITORY = 0, // must match Cardinal_ExpDetThreshold.js
    MODALITY_VISUAL = 1, // must match Cardinal_ExpDetThreshold.js
    STROKE = Raphael.rgb(255, 255, 255),
    STROKEWIDTH = 3,
    BGCOLOUR_R = 0,
    BGCOLOUR_G = 0,
    BGCOLOUR_B = 0,
    BGCOLOUR = Raphael.rgb(BGCOLOUR_R, BGCOLOUR_G, BGCOLOUR_B),
    FONT = "20px Fontin-Sans, Arial",
    // Calculate positioning
    // Keep stimuli above all buttons, to avoid screen smudging
    STIMWIDTH = tp.STIMWIDTH,
    STIMHEIGHT = tp.STIMHEIGHT,
    HCENTRE = tp.screenWidth / 2,
    STIMLEFT = HCENTRE - (STIMWIDTH / 2),
    STIMTOP = tp.screenHeight * 0.05,
    YESBUTTON = {
        label: tp.OPTION_YES,
        shapeattr: {
            fill: Raphael.rgb(0, 0, 200),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "text-anchor": "middle" // start, middle, end
        },
        left: tp.screenWidth * 0.6,
        right: tp.screenWidth * 0.8,
        top: tp.screenHeight * 0.7,
        bottom: tp.screenHeight * 0.9,
        radius: 20
    },
    NOBUTTON = {
        label: tp.OPTION_NO,
        shapeattr: {
            fill: Raphael.rgb(0, 0, 200),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "text-anchor": "middle" // start, middle, end
        },
        left: tp.screenWidth * 0.2,
        right: tp.screenWidth * 0.4,
        top: tp.screenHeight * 0.7,
        bottom: tp.screenHeight * 0.9,
        radius: 20
    },
    PROMPT_X = tp.screenWidth * 0.5,
    PROMPT_Y = tp.screenHeight * 0.65,
    PROMPT_Y1 = tp.screenHeight * 0.20,
    PROMPT_Y2 = tp.screenHeight * 0.25,
    PROMPT_Y3 = tp.screenHeight * 0.3,
    PROMPT_ATTR = {
        fill: Raphael.rgb(255, 255, 255),
        font: FONT,
        "text-anchor": "middle" // start, middle, end
    },
    THANKS = {
        label: tp.TEXT_THANKS,
        shapeattr: {
            fill: Raphael.rgb(0, 0, 200),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "text-anchor": "middle" // start, middle, end
        },
        left: tp.screenWidth * 0.3,
        right: tp.screenWidth * 0.7,
        top: tp.screenHeight * 0.6,
        bottom: tp.screenHeight * 0.8,
        radius: 20
    },
    ABORT = {
        label: tp.TEXT_ABORT,
        shapeattr: {
            fill: Raphael.rgb(100, 0, 0)
        },
        textattr: {
            fill: Raphael.rgb(0, 0, 0),
            font: FONT,
            "text-anchor": "middle" // start, middle, end
        },
        left: tp.screenWidth * 0.01,
        right: tp.screenWidth * 0.08,
        top: tp.screenHeight * 0.94,
        bottom: tp.screenHeight * 0.99,
        radius: 20
    },
    START = {
        label: tp.TEXT_START,
        shapeattr: {
            fill: Raphael.rgb(0, 0, 200),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "text-anchor": "middle" // start, middle, end
        },
        left: tp.screenWidth * 0.3,
        right: tp.screenWidth * 0.7,
        top: tp.screenHeight * 0.6,
        bottom: tp.screenHeight * 0.8,
        radius: 20
    },
    //-------------------------------------------------------------------------
    // Graphics
    //-------------------------------------------------------------------------
    paper = new Raphael(0, 0, tp.screenWidth, tp.screenHeight),
    //-------------------------------------------------------------------------
    // Functions defined before use to avoid circularity
    //-------------------------------------------------------------------------
    nextTrial,
    //-------------------------------------------------------------------------
    // Trial record
    //-------------------------------------------------------------------------
    trials = [],
    currentTrial = -1,
    currentTrialIgnoringCatchTrials = -1,
    trialNumberLastYesBeforeFirstNo = null, // termed "trial 1" in Lecluyse & Meddis (2009)
    mainrecord = {
        finished: false
        // other properties copied from LogisticDescriptives (q.v.)
    };

//=============================================================================
// Saving, exiting
//=============================================================================

function saveTrial(t) {
    var tr = trials[t];
    trace("saveTrial: tr = " + JSON.stringify(tr));
    sendEvent({
        eventType: "savetrial",
        data: JSON.stringify(preprocess_moments_for_json_stringify(tr))
    });
}

function saveAllTrials() {
    var t;
    for (t = 0; t < trials.length; t += 1) {
        saveTrial(t);
    }
}

function saveMain() {
    trace("saveMain");
    sendEvent({ eventType: "savemain", data: JSON.stringify(mainrecord) });
}

function savingWait() {
    paper.clear();
    createText(paper, tp.SAVING_PLEASE_WAIT, PROMPT_X, PROMPT_Y, PROMPT_ATTR);
}

function exit(cleanly) {
    if (cleanly) {
        trace("exit: exit");
        sendEvent({eventType: "exit"});
    } else {
        trace("exit: abort");
        sendEvent({eventType: "abort"});
    }
}

function abort() {
    savingWait();
    saveAllTrials();
    saveMain();
    exit(false);
}

//=============================================================================
// Trials
//=============================================================================

function TrialRecord(trialNum) {
    this.cardinal_expdetthreshold_id = tp.cardinal_expdetthreshold_id;
    this.trial = trialNum;
    this.trial_ignoring_catch_trials = null;
    this.target_presented = null; // if false, a catch trial
    this.target_time = null;
    this.intensity = null;
    this.choice_time = null;
    this.responded = null;
    this.response_time = null;
    this.response_latency_ms = null;
    this.yes = null;
    this.no = null;
    this.caught_out_reset = null;
    this.trial_num_in_calculation_sequence = null;
}

function haveWeJustReset() {
    trace("haveWeJustReset()");
    if (currentTrial === 0) {
        return false;
    }
    if (trials[currentTrial - 1].caught_out_reset) {
        return true;
    }
    return false;
}

function inInitialStepPhase() {
    trace("inInitialStepPhase()");
    return (trialNumberLastYesBeforeFirstNo === null);
}

function lastTrialWasFirstNo() {
    trace("lastTrialWasFirstNo()");
    if (trialNumberLastYesBeforeFirstNo === null) {
        return false;
    }
    return (
        trials[currentTrial].trial_ignoring_catch_trials ===
            trials[trialNumberLastYesBeforeFirstNo].trial_ignoring_catch_trials
            + 2
    );
}

function getNBackNonCatchTrialIndex(n, startIndex) {
    if (n === undefined) {
        n = 1;
    }
    if (startIndex === undefined) {
        startIndex = currentTrial;
    }
    trace("getNBackNonCatchTrialIndex(" + n + "," + startIndex + ")");
    var target = trials[startIndex].trial_ignoring_catch_trials - n,
        i;
    for (i = 0; i < trials.length; i += 1) {
        if (trials[i].target_presented &&
                trials[i].trial_ignoring_catch_trials === target) {
            trace("... returning " + i);
            return i;
        }
    }
    trace("... returning null");
    return null;
}

function getIntensity() {
    trace("getIntensity()");
    var tr = trials[currentTrial],
        oneBackTrialNum,
        prevtrial,
        twoBackTrialNum,
        twoBack;
    if (!tr.target_presented) {
        return null;
    }
    if (tr.trial === 0 || haveWeJustReset()) {
        trace("First trial, or we've just reset");
        return randomFloatBetween(tp.start_intensity_min,
                                  tp.start_intensity_max);
    }
    oneBackTrialNum = getNBackNonCatchTrialIndex(1);
    if (oneBackTrialNum === null) {
        trace("!!! Problem in getIntensity: oneBackTrialNum is null");
    }
    prevtrial = trials[oneBackTrialNum];
    if (inInitialStepPhase()) {
        return prevtrial.intensity - tp.initial_large_intensity_step;
    }
    if (lastTrialWasFirstNo()) {
        twoBackTrialNum = getNBackNonCatchTrialIndex(2);
        if (twoBackTrialNum === null) {
            trace("!!! Problem in getIntensity: twoBackTrialNum is null");
        }
        twoBack = trials[twoBackTrialNum];
        return (prevtrial.intensity + twoBack.intensity) / 2;
    }
    if (prevtrial.yes) {
        // In main phase. Detected stimulus last time; make it harder
        return prevtrial.intensity - tp.main_small_intensity_step;
    }
    // In main phase. Didn't detect stimulus last time; make it easier
    return prevtrial.intensity + tp.main_small_intensity_step;
}

function wantCatchTrial() {
    if (currentTrial === 0) {
        return false; // never on the first
    }
    if (trials[currentTrial - 1].caught_out_reset) {
        return false; // never immediately after a reset
    }
    if (currentTrial === 1) {
        return true; // always on the second
    }
    if (trials[currentTrial - 2].caught_out_reset) {
        return true; // always on the second of a fresh run
    }
    return randomBool(tp.p_catch_trial); // otherwise on e.g. 20% of trials
}

function showVisualStimulus(filename, intensity) {
    trace("showVisualStimulus(): " + filename +
          " (intensity " + intensity + ")");
    var image = paper.image(filename, STIMLEFT, STIMTOP, STIMWIDTH,
                            STIMHEIGHT);
    image.attr("opacity", intensity);
}

function reset(currentTrial) {
    trace("reset(): currentTrial = " + currentTrial);
    trials[currentTrial].caught_out_reset = true;
    trialNumberLastYesBeforeFirstNo = null;
}

function recordChoice(trialNumber, yes) {
    trace("recordChoice(): trialNumber = " + trialNumber + ", yes = " + yes);
    trials[trialNumber].responded = true;
    trials[trialNumber].response_time = now();
    trials[trialNumber].response_latency_ms = (
        trials[trialNumber].response_time - trials[trialNumber].choice_time
    );
    trials[trialNumber].yes = yes;
    trials[trialNumber].no = !yes;
    if (!trials[trialNumber].target_presented && yes) {
        // Caught out... Reset.
        reset(trialNumber);
    } else if (trialNumber === 0 && !yes) {
        // No on first trial -- treat as reset
        reset(trialNumber);
    } else if (trials[trialNumber].target_presented
                    && !yes
                    && trialNumberLastYesBeforeFirstNo === null) {
        // First no
        trialNumberLastYesBeforeFirstNo = getNBackNonCatchTrialIndex(
            1,
            trialNumber
        );
        trace("first no response: trialNumberLastYesBeforeFirstNo = " +
              trialNumberLastYesBeforeFirstNo);
    }
    paper.clear();
    setTimeout(nextTrial, tp.iti_s * 1000);
}

function offerChoice(trialNumber) {
    trace("offerChoice(): trialNumber = " + trialNumber);
    // trace("offerChoice(): " + momentToString(now()));
    paper.clear();
    createText(paper, tp.prompt, PROMPT_X, PROMPT_Y, PROMPT_ATTR);
    var Y = createButton(paper, YESBUTTON),
        N = createButton(paper, NOBUTTON),
        A = createButton(paper, ABORT);
    setTouchStartEvent(Y, function () {
        clearTouchEvents(Y);
        recordChoice(trialNumber, true);
    });
    setTouchStartEvent(N, function () {
        clearTouchEvents(N);
        recordChoice(trialNumber, false);
    });
    setTouchStartEvent(A, function () { abort(); });
    trials[trialNumber].choice_time = now();
}

function startTrial(tr) {
    trace("startTrial(): starting trial number " + tr.trial);

    // Determine if it's a catch trial (on which no stimulus is presented)
    if (wantCatchTrial()) {
        tr.target_presented = false;
        trace("Catch trial");
        tr.trial_ignoring_catch_trials = null;
    } else {
        tr.target_presented = true;
        currentTrialIgnoringCatchTrials += 1;
        tr.trial_ignoring_catch_trials = currentTrialIgnoringCatchTrials;
    }

    tr.intensity = getIntensity();
    tr.intensity = clip(tr.intensity, 0, 1); // intensity is in the range [0, 1]
    trace("Using intensity " + tr.intensity);

    // Display stimulus
    if (tr.target_presented) {
        if (tp.modality === MODALITY_AUDITORY) {
            setVolume(tp.target_filename, tr.intensity);
            playSound(tp.background_filename);
            playSound(tp.target_filename);
        } else {
            showVisualStimulus(tp.background_filename, tp.background_intensity);
            showVisualStimulus(tp.target_filename, tr.intensity);
        }
        tr.target_time = now();
    } else {
        // Catch trial
        if (tp.modality === MODALITY_AUDITORY) {
            playSound(tp.background_filename);
        } else {
            showVisualStimulus(tp.background_filename, tp.background_intensity);
        }
    }

    var stimulus_time_ms = (
        (tp.modality === MODALITY_VISUAL) ?
                (tp.visual_target_duration_s * 1000) :
                tp.background_duration_ms
    );
    setTimeout(function () { offerChoice(tr.trial); }, stimulus_time_ms);
    // trace("starting timer: " + momentToString(now()));
}

//=============================================================================
// Task
//=============================================================================

function timeToStop() {
    if (trialNumberLastYesBeforeFirstNo === null) {
        return false;
    }
    var finalTrialIgnoringCatchTrials = (
        trials[trialNumberLastYesBeforeFirstNo].trial_ignoring_catch_trials +
            tp.num_trials_in_main_sequence - 1
    );
    return (trials[currentTrial].trial_ignoring_catch_trials >=
            finalTrialIgnoringCatchTrials);
}

function thanks() {
    paper.clear();
    var T = createButton(paper, THANKS);
    setTouchStartEvent(T, function () {
        clearTouchEvents(T);
        paper.clear();
        exit(true);
    });
}

function labelTrialsForAnalysis() {
    var tnum = 1,
        t;
    for (t = 0; t < trials.length; t += 1) {
        trials[t].trial_num_in_calculation_sequence = null;
        if (t >= trialNumberLastYesBeforeFirstNo
                && trials[t].target_presented) {
            trials[t].trial_num_in_calculation_sequence = tnum;
            tnum += 1;
        }
    }
}

function calculateFit() {
    var intensity = [],
        choice = [],
        t,
        par,
        description;
    for (t = 0; t < trials.length; t += 1) {
        if (trials[t].trial_num_in_calculation_sequence !== null) {
            intensity.push(trials[t].intensity);
            choice.push(trials[t].yes ? 1 : 0);
        }
    }
    par = logisticFitSinglePredictor(intensity, choice);
    description = logisticDescriptives(par);
    trace("logistic fit: par = " + JSON.stringify(par));
    trace("logistic fit: description = " + JSON.stringify(description));
    copyProperties(description, mainrecord);
}

nextTrial = function () {
    trace("nextTrial()");
    paper.clear();
    if (currentTrial >= 0) {
        saveTrial(currentTrial);
    }
    if (timeToStop()) {
        trace("time to stop");
        mainrecord.finished = true;
        savingWait();
        labelTrialsForAnalysis();
        saveAllTrials(); // need to re-save after labelling
        calculateFit();
        saveMain();
        thanks();
        return;
    }

    currentTrial += 1;
    var tr = new TrialRecord(currentTrial);
    trials.push(tr);
    assert(currentTrial === trials.length - 1, "Bug in nextTrial()");
    startTrial(trials[currentTrial]);
};

function startTask() {
    trace("starttask: params = " + JSON.stringify(tp));
    paper.clear();
    createText(paper, tp.INSTRUCTIONS_1, PROMPT_X, PROMPT_Y1, PROMPT_ATTR);
    createText(paper, tp.INSTRUCTIONS_2, PROMPT_X, PROMPT_Y2, PROMPT_ATTR);
    createText(paper, tp.INSTRUCTIONS_3, PROMPT_X, PROMPT_Y3, PROMPT_ATTR);
    var B = createButton(paper, START);
    setTouchStartEvent(B, function () {
        nextTrial();
    });
}

registerWebviewTask(TASKNAME, EVENTNAME_IN, EVENTNAME_OUT,
                    startTask, incomingEvent);
