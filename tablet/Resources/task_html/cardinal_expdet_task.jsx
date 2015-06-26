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
    randomFloatBetween, shuffle,
    createText, createButton,
    setTouchStartEvent, clearTouchEvents,
    setVolume, playSound, stopSound,
    assert, copyProperties,
    rotateArray, appendArray,
    registerWebviewTask
*/
/*global logisticFitSinglePredictor, logisticDescriptives */
/*global Raphael */
/*global moment */

/*
===============================================================================
Comments
===============================================================================
- Trials are created en masse and randomized, so the task does need an array of all trials.
- Testing on the Asus tablet: maximum volume, maximum brightness, default ExpDetThreshold settings, RNC:
    visual / circle (target 0):        0.065
    visual / word (target 1):          0.030
    auditory / tone (target 0):  x50 = 0.007
    auditory / voice (target 1):       0.013
*/

//=============================================================================
// Communication with the "outside world": see taskhtmlcommon.js
//=============================================================================
// Must receive task parameters, and provide incomingEvent(), startTask()

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
            screenHeight: 752,
        }
    ),
    TASKNAME = "Expectation-Detection HTML/JS",
    EVENTNAME_OUT = "EXPDET_EVENT_FROM_WEBVIEW",
    EVENTNAME_IN = "EXPDET_EVENT_TO_WEBVIEW",
    SOUND_COMPLETE_EVENT = "soundFinished",
    // Calculate positioning
    STIMWIDTH = tp.STIMWIDTH,
    STIMHEIGHT = tp.STIMHEIGHT,
    HCENTRE = tp.screenWidth / 2,
    STIMLEFT = HCENTRE - (STIMWIDTH / 2),
    //     VCENTRE = tp.screenHeight / 2,
    //     STIMTOP = VCENTRE - (STIMHEIGHT / 2),
    STIMTOP = tp.screenHeight * 0.05,
    STROKE = Raphael.rgb(255, 255, 255),
    STROKEWIDTH = 3,
    BGCOLOUR = Raphael.rgb(0, 0, 0),
    FONT = "20px Fontin-Sans, Arial",
    BUTTONTEXTATTR = {
        fill: Raphael.rgb(255, 255, 255),
        font: FONT,
        "text-anchor": "middle" // start, middle, end
    },
    USERPAUSEBUTTON = {
        label: tp.PAUSE_PROMPT,
        shapeattr: {
            fill: Raphael.rgb(0, 100, 0),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        textattr: BUTTONTEXTATTR,
        left: tp.screenWidth * 0.3,
        right: tp.screenWidth * 0.7,
        top: tp.screenHeight * 0.6,
        bottom: tp.screenHeight * 0.8,
        radius: 20,
    },
    PROMPT_X = tp.screenWidth * 0.5,
    PROMPT_Y = tp.screenHeight * 0.20,
    PROMPT_Y2 = tp.screenHeight * 0.25,
    PROMPT_Y3 = tp.screenHeight * 0.3,
    PROMPT_ATTR = {
        fill: Raphael.rgb(255, 255, 255),
        font: FONT,
        "text-anchor": "middle" // start, middle, end
    },
    NRATINGS = tp.DETECTION_OPTIONS.length,
    RATINGBUTTON_WIDTH = 0.8 * (tp.screenWidth / NRATINGS),
    RATINGBUTTONS = [],
    POINTS_MULTIPLIER = [],
    POINTS_PER_RATING = 10,
    RATING_MEANS_YES = [],
    RATING_MEANS_DONT_KNOW = [],
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
        radius: 20,
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
        radius: 20,
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
        radius: 20,
    },
    CANCEL_ABORT = {
        label: tp.TEXT_CANCEL,
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
        top: tp.screenHeight * 0.6,
        bottom: tp.screenHeight * 0.8,
        radius: 20,
    },
    REALLY_ABORT = {
        label: tp.TEXT_ABORT,
        shapeattr: {
            fill: Raphael.rgb(100, 0, 0),
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
        top: tp.screenHeight * 0.6,
        bottom: tp.screenHeight * 0.8,
        radius: 20,
    },
    // Stimuli, counterbalancing, etc.
    MODALITIES = {
        AUDITORY: 0,
        VISUAL: 1,
    },
    // Stimulus counterbalancing is simply the assignment of cues.
    // Start with a sequence:
    rawCueIndices = [],
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
    currentTrial = -1;

function soundFinished() {
    trace("Webview JS notified of sound having finished " +
          "(ignored; using timer instead)");
}

function incomingEvent(e) {
    trace("incomingEvent: " + JSON.stringify(e));
    if (e.eventType === SOUND_COMPLETE_EVENT) {
        soundFinished();
    }
}

function getRatingButtonEdges(x, n) { // x is zero-based
    var centre = tp.screenWidth * (2 * x + 1) / (2 * n);
    return {
        left:   centre - (RATINGBUTTON_WIDTH / 2),
        right:  centre + (RATINGBUTTON_WIDTH / 2),
        top:    tp.screenHeight * 0.7,
        bottom: tp.screenHeight * 0.9,
    };
}

function makeRatingButtonsAndPoints() {
    var centrerating = (NRATINGS - 1) / 2,
        // ... for 5 ratings, internal number 0-4, centre is 2;
        // ... for 6 ratings, internal number 0-5, centre is 2.5
        i,
        pos,
        edges,
        b,
        points,
        yes,
        dont_know;
    for (i = 0; i < NRATINGS; i += 1) {
        // Rating button
        pos = tp.is_detection_response_on_right ? i : (NRATINGS - 1 - i);
        edges = getRatingButtonEdges(pos, NRATINGS);
        b = {
            label: tp.DETECTION_OPTIONS[i],
            shapeattr: {
                fill: Raphael.rgb(0, 0, 200),
                stroke: STROKE,
                "stroke-width": STROKEWIDTH
            },
            textattr: BUTTONTEXTATTR,
            left: edges.left,
            right: edges.right,
            top: edges.top,
            bottom: edges.bottom,
            radius: 20,
        };
        // trace("RATINGBUTTON: " + JSON.stringify(b));
        RATINGBUTTONS.push(b);
        // Points
        points = Math.abs(i - centrerating) * POINTS_PER_RATING; // e.g. 5 ratings: (2,1,0,1,2)*POINTS_PER_RATING; 6 ratings, (2.5,1.5,0.5,0.5,1.5,2.5)*POINTS_PER_RATING
        POINTS_MULTIPLIER.push(points);
        // Rating means yes
        yes = (i > centrerating);
        RATING_MEANS_YES.push(yes);
        dont_know = (i === centrerating);
        RATING_MEANS_DONT_KNOW.push(dont_know);
    }
}


function doCounterbalancing() {
    var i;
    for (i = 0; i < tp.N_CUES; i += 1) {
        rawCueIndices.push(i);
    }
    // Then rotate it by the counterbalancing number:
    rawCueIndices = rotateArray(rawCueIndices, tp.stimulus_counterbalancing);
}

//=====================================================================
// Counterbalancing/lookup functions
//=====================================================================

function getAuditoryCueFilename(cue) {
    return tp.EXPDET_AUDITORY_CUES[rawCueIndices[cue]];
}

function getAuditoryCueDuration(cue) {
    return tp.auditory_cue_durations_ms[rawCueIndices[cue]];
}

function getVisualCueFilename(cue) {
    return tp.EXPDET_VISUAL_CUES[rawCueIndices[cue]];
}

function getAuditoryTargetFilename(target_number) {
    return tp.EXPDET_AUDITORY_TARGETS[target_number];
}

function getVisualTargetFilename(target_number) {
    return tp.EXPDET_VISUAL_TARGETS[target_number];
}

function getAuditoryBackgroundFilename() {
    return tp.EXPDET_AUDITORY_BACKGROUND;
}

function getVisualBackgroundFilename() {
    return tp.EXPDET_VISUAL_BACKGROUND;
}

function getPromptText(modality, target_number) {
    // trace("getPromptText: modality=" + modality + ", target_number=" + target_number);
    if (modality === MODALITIES.AUDITORY) {
        return tp.AUDITORY_PROMPTS[target_number];
    }
    return tp.VISUAL_PROMPTS[target_number];
}

function reportCounterbalancing() {
    var spacer = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
        i;
    trace(spacer);
    trace("COUNTERBALANCING = " + tp.stimulus_counterbalancing);
    trace("rawCueIndices = " + JSON.stringify(rawCueIndices));
    for (i = 0; i < rawCueIndices.length; i += 1) {
        trace("Cue " + i + " maps to raw cue " + rawCueIndices[i]);
    }
    trace(spacer);
}

//=====================================================================
// Saving, exiting
//=====================================================================

function saveTrial() {
    trace("saveTrial()");
    if (currentTrial < 0 || currentTrial > trials.length) {
        trace("ERROR: attempting to saveTrial() with currentTrial = " +
              currentTrial + "; ignoring");
        return;
    }
    sendEvent({
        eventType: "savetrial",
        data: JSON.stringify(
            preprocess_moments_for_json_stringify(trials[currentTrial])
        )
    });
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

function savingWait() {
    paper.clear();
    createText(paper, tp.SAVING_PLEASE_WAIT, PROMPT_X, PROMPT_Y, PROMPT_ATTR);
}

function abort() {
    trace("abort()");
    savingWait();
    saveTrial();
    exit(false);
}

function thanks() {
    trace("thanks()");
    paper.clear();
    var T = createButton(paper, THANKS);
    setTouchStartEvent(T, function () {
        clearTouchEvents(T);
        paper.clear();
        exit(true);
    });
}

//=====================================================================
// Trial plan and results
//=====================================================================

function Trial(trialparams) { // object
    // trace("Trial()");
    var i;
    // Create all the fields
    for (i = 0; i < tp.trialfieldlist.length; i += 1) {
        this[tp.trialfieldlist[i]] = null;
    }
    // Apply parameters
    copyProperties(trialparams, this);
    this.cardinal_expdet_id = tp.cardinal_expdet_id;
    this.iti_length_s = randomFloatBetween(tp.iti_min_s, tp.iti_max_s);
}

function makeTrialGroup(block, groupnum, groupspec) {
    // trace("makeTrialGroup()");
    var groupoftrials = [],
        trialparams = {
            block: block,
            group_num: groupnum,
            cue: groupspec.cue,
            raw_cue_number: rawCueIndices[groupspec.cue],
            target_modality: groupspec.target_modality,
            target_number: groupspec.target_number
        },
        i;
    trialparams.target_present = true;
    for (i = 0; i < groupspec.n_target; i += 1) {
        groupoftrials.push(new Trial(trialparams));
    }
    trialparams.target_present = false;
    for (i = 0; i < groupspec.n_no_target; i += 1) {
        groupoftrials.push(new Trial(trialparams));
    }
    return groupoftrials;
}

function createTrials() {
    var b,
        blockoftrials,
        g,
        groupoftrials,
        t;
    trace("createTrials()");
    for (b = 0; b < tp.num_blocks; b += 1) {
        blockoftrials = [];
        for (g = 0; g < tp.trialGroupSpecs.length; g += 1) {
            groupoftrials = makeTrialGroup(b, g, tp.trialGroupSpecs[g]);
            appendArray(blockoftrials, groupoftrials);
        }
        shuffle(blockoftrials); // Randomize in blocks
        appendArray(trials, blockoftrials);
    }
    // Write trial numbers
    for (t = 0; t < trials.length; t += 1) {
        trials[t].trial = t;
    }
}

//=====================================================================
// Task
//=====================================================================

function startTask() {
    trace("starttask: params = " + JSON.stringify(tp));
    reportCounterbalancing();
    paper.clear();
    createText(paper, tp.INSTRUCTIONS_1, PROMPT_X, PROMPT_Y, PROMPT_ATTR);
    createText(paper, tp.INSTRUCTIONS_2, PROMPT_X, PROMPT_Y2, PROMPT_ATTR);
    createText(paper, tp.INSTRUCTIONS_3, PROMPT_X, PROMPT_Y3, PROMPT_ATTR);
    var B = createButton(paper, START);
    setTouchStartEvent(B, function () { nextTrial(); });
}

function estimateRemaining() {
    // trace("estimateRemaining()");
    var nTrialsLeft = trials.length - currentTrial,
        avgTrialDurationSec = (
            tp.cue_duration_s +
            ((tp.visual_target_duration_s +
                    (tp.auditory_background_duration_ms / 1000.0)) / 2) +
            1.0 + // rough guess for user response time
            2.0 + // rough guess for user confirmation time
            ((tp.iti_min_s + tp.iti_max_s) / 2)
        );
    return {
        trials: nTrialsLeft,
        timeMin: nTrialsLeft * avgTrialDurationSec / 60.0
    };
}

function trial(t) {
    trace("trial(): t.trial = " + t.trial);

    function endTrial() {
        trace("endTrial()");
        var now = moment();
        t.iti_end_time = now;
        t.trial_end_time = now;
        nextTrial();
    }

    function iti() {
        paper.clear();
        t.iti_start_time = moment();
        setTimeout(endTrial, t.iti_length_s * 1000);
    }

    function askAbort(returnfunc) {
        trace("askAbort()");
        paper.clear();
        createText(paper, tp.TEXT_REALLY_ABORT, PROMPT_X, PROMPT_Y,
                   PROMPT_ATTR);
        var C = createButton(paper, CANCEL_ABORT),
            A = createButton(paper, REALLY_ABORT);
        setTouchStartEvent(C, function () { returnfunc(); });
        setTouchStartEvent(A, function () { abort(); });
    }

    function displayScore() {
        trace("displayScore()");
        paper.clear();
        var points_msg = (tp.TEXT_POINTS + " " + (t.points > 0 ? "+" : "") +
                          t.points),
            cumpoints_msg = (tp.TEXT_CUMULATIVE_POINTS + " " +
                             (t.cumulative_points > 0 ? "+" : "") +
                             t.cumulative_points),
            B = createButton(paper, USERPAUSEBUTTON),
            A = createButton(paper, ABORT);
        createText(paper, points_msg, PROMPT_X, PROMPT_Y,  PROMPT_ATTR);
        createText(paper, cumpoints_msg,   PROMPT_X, PROMPT_Y2, PROMPT_ATTR);
        setTouchStartEvent(B, function () { iti(); });
        setTouchStartEvent(A, function () { askAbort(displayScore); });
    }

    function processResponse(rating) {
        trace("processResponse(): rating = " + rating);
        t.responded = true;
        t.response_time = moment();
        t.response_latency_ms = t.response_time.diff(t.detection_start_time);
        t.rating = rating;
        if (RATING_MEANS_DONT_KNOW[rating]) {
            t.correct = false;
        } else {
            t.correct = (t.target_present === RATING_MEANS_YES[rating]);
        }
        t.points = (t.correct ? 1 : -1) * POINTS_MULTIPLIER[rating];
        trace("processResponse(): correct = " + t.correct + ", points = " + t.points);
        if (t.trial === 0) {
            t.cumulative_points = t.points;
        } else {
            t.cumulative_points = trials[t.trial - 1].cumulative_points + t.points;
        }
        displayScore();
    }

    function detection() {
        var prompttext = getPromptText(t.target_modality, t.target_number),
            prompt,
            i,
            b;

        function makeRatingFunction(rating) { // Beware the Javascript Callback Loop Bug
            // http://stackoverflow.com/questions/3023874/arguments-to-javascript-anonymous-function
            return function () {
                processResponse(rating);
            };
        }

        trace("detection()");
        // Clear preceding
        paper.clear();
        // Start detection
        t.detection_start_time = moment();
        trace("prompttext: " + prompttext);
        prompt = paper.text(PROMPT_X, PROMPT_Y).attr(PROMPT_ATTR);
        prompt.attr("text", prompttext);
        for (i = 0; i < NRATINGS; i += 1) {
            b = createButton(paper, RATINGBUTTONS[i]);
            setTouchStartEvent(b, makeRatingFunction(i));
        }
        // trace("detection_end");

    }

    function target() {
        trace("target(): t.target_present = " + t.target_present +
              ", t.target_number = " + t.target_number);
        var intensity,
            targetimage,
            targetbackground;
        // Start target
        t.target_start_time = moment();
        if (t.target_modality === MODALITIES.AUDITORY) {
            // AUDITORY
            playSound(getAuditoryBackgroundFilename());
            if (t.target_present) {
                // volume was preset when the sound was loaded
                playSound(getAuditoryTargetFilename(t.target_number));
                trace("auditory target: present");
            } else {
                trace("auditory target: absent");
            }
            setTimeout(detection, tp.auditory_background_duration_ms);
        } else {
            // VISUAL
            targetbackground = paper.image(getVisualBackgroundFilename(),
                                           STIMLEFT, STIMTOP,
                                           STIMWIDTH, STIMHEIGHT);
            targetbackground.attr({opacity: tp.visual_background_intensity });
            if (t.target_present) {
                intensity = (t.target_number === 0 ?
                        tp.visual_target_0_intensity :
                        tp.visual_target_1_intensity
                );
                targetimage = paper.image(
                    getVisualTargetFilename(t.target_number),
                    STIMLEFT,
                    STIMTOP,
                    STIMWIDTH,
                    STIMHEIGHT
                );
                targetimage.attr({opacity: intensity});
                trace("visual target: intensity " + intensity);
            } else {
                trace("visual target: absent");
            }
            setTimeout(detection, tp.visual_target_duration_s * 1000);
        }
    }

    function isi() {
        trace("isi()");
        // Clear preceding
        paper.clear();
        stopSound(getAuditoryCueFilename(t.cue));
        setTimeout(target, tp.isi_duration_s * 1000);
    }

    function cue() {
        trace("cue()");
        paper.clear();
        t.cue_start_time = moment();
        // Cues are multimodal.
        playSound(getAuditoryCueFilename(t.cue));
        var cueimage = paper.image(getVisualCueFilename(t.cue), STIMLEFT,
                                   STIMTOP, STIMWIDTH, STIMHEIGHT);
        cueimage.attr("opacity", tp.visual_cue_intensity);
        setTimeout(isi, tp.cue_duration_s * 1000);
    }

    function startTrialProper() {
        trace("startTrialProper()");
        if (t.pause_given_before_trial) {
            t.pause_end_time = moment();
        }
        t.trial_start_time = moment();
        cue();
    }

    function userPausePartTwo() {
        trace("userPausePartTwo()");
        paper.clear();
        var remaining = estimateRemaining(),
            msgTrials = tp.N_TRIALS_LEFT_MSG + " " + remaining.trials,
            msgTime = tp.TIME_LEFT_MSG + " " + Math.round(remaining.timeMin),
            B = createButton(paper, USERPAUSEBUTTON),
            A = createButton(paper, ABORT);
        createText(paper, msgTrials, PROMPT_X, PROMPT_Y,  PROMPT_ATTR);
        createText(paper, msgTime,   PROMPT_X, PROMPT_Y2, PROMPT_ATTR);
        setTouchStartEvent(B, startTrialProper);
        setTouchStartEvent(A, function () { askAbort(userPausePartTwo); });
    }

    function userPause() {
        trace("userPause()");
        t.pause_given_before_trial = true;
        t.pause_start_time = moment();
        userPausePartTwo();
    }

    //-------------------------------------------------------------------------
    // Start
    //-------------------------------------------------------------------------
    if (tp.pause_every_n_trials > 0 &&
            t.trial % tp.pause_every_n_trials === 0) {
        // we allow a pause at the start of trial 0
        userPause();
    } else {
        t.pause_given_before_trial = false;
        startTrialProper();
    }
}

nextTrial = function () {
    trace("nextTrial()");
    if (currentTrial >= 0) {
        saveTrial();
    }
    currentTrial += 1;
    if (currentTrial >= trials.length) {
        thanks();
        return;
    }
    trial(trials[currentTrial]);
};

registerWebviewTask(TASKNAME, EVENTNAME_IN, EVENTNAME_OUT,
                    startTask, incomingEvent);

makeRatingButtonsAndPoints(); // in a function to avoid "var i" in global scope
doCounterbalancing(); // in a function to avoid "var i" in global scope
createTrials();

//=====================================================================
// Debug initial processing of the script
//=====================================================================

trace("script parsed successfully");

