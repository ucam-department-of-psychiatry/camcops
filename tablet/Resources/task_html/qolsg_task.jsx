// qolsg_task.jsx

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
    pointAddXY, pointOnCircle, vectorAngleDegrees, vectorFromTo,
    alignTop, createText, createButton,
    setTouchStartEvent, clearTouchEvents,
    registerWebviewTask
*/
/*global Raphael */

//=============================================================================
// TrialRecord
//=============================================================================

function TrialRecord() {
    this.category_start_time = null;
    this.category_responded = null;
    this.category_response_time = null;
    this.category_chosen = null;
    this.gamble_fixed_option = null;
    this.gamble_lottery_option_p = null;
    this.gamble_lottery_option_q = null;
    this.gamble_lottery_on_left = null;
    this.gamble_starting_p = null;
    this.gamble_start_time = null;
    this.gamble_responded = null;
    this.gamble_response_time = null;
    this.p = null;
    this.h = null;
}

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
            screenHeight: 752,
        }
    ),
    TASKNAME = "QoLSG HTML/JS",
    EVENTNAME_OUT = "QOLSG_EVENT_FROM_WEBVIEW",
    EVENTNAME_IN = "QOLSG_EVENT_TO_WEBVIEW",
    // Calculate positioning
    EDGESPACE_FRAC = 0.2, // left, right
    CENTRESPACE_FRAC = 0.2,
    STIMDIAMETER_FRAC = 0.5 - EDGESPACE_FRAC - (0.5 * CENTRESPACE_FRAC),
    STIMDIAMETER = tp.screenWidth * STIMDIAMETER_FRAC,
    STIMRADIUS = STIMDIAMETER / 2,
    STIM_VCENTRE = tp.screenHeight * 0.55,
    HCENTRE = tp.screenWidth / 2,
    LEFTSTIMCENTRE  = tp.screenWidth * (0.5 - (0.5 * CENTRESPACE_FRAC +
                                               0.5 * STIMDIAMETER_FRAC)),
    RIGHTSTIMCENTRE = tp.screenWidth * (0.5 + (0.5 * CENTRESPACE_FRAC +
                                               0.5 * STIMDIAMETER_FRAC)),
    TEXT_RADIUS = STIMRADIUS * 1.65,
    STROKE = Raphael.rgb(255, 255, 255),
    STROKEWIDTH = 3,
    BGCOLOUR = Raphael.rgb(0, 0, 0),
    FONT = "20px Fontin-Sans, Arial",
    GAMBLEINSTRUCTION = {
        left: tp.screenWidth * 0.01,
        top: tp.screenHeight * 0.01,
        width: tp.screenWidth * 0.98,
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "text-anchor": "start",
        },
        //prefix_high: tp.TEXT_INSTRUCTION_PREFIX_HIGH,
        //prefix_medium: tp.TEXT_INSTRUCTION_PREFIX_MEDIUM,
        //prefix_low: tp.TEXT_INSTRUCTION_PREFIX_LOW,
        prefix_2: tp.TEXT_INSTRUCTION_PREFIX_2,
        medium: tp.TEXT_INSTRUCTION_MEDIUM,
        low: tp.TEXT_INSTRUCTION_LOW,
        high: tp.TEXT_INSTRUCTION_HIGH,
        suffix: tp.TEXT_INSTRUCTION_SUFFIX,
    },
    INITIALINSTRUCTION = {
        xcentre: tp.screenWidth * 0.5,
        ycentre: tp.screenHeight * 0.05,
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "text-anchor": "middle" // start, middle, end
        },
        text: tp.TEXT_INITIAL_INSTRUCTION
    },
    LABEL_ATTR = {
        font: FONT,
        "font-weight": "bold",
        "text-anchor": "middle" // start, middle, end
    },
    TESTSTATE = {
        label: tp.TEXT_CURRENT_STATE,
        fillcolour: Raphael.rgb(255, 255, 0),
        textcolour: Raphael.rgb(255, 255, 0),
    },
    DEAD = {
        label: tp.TEXT_DEAD,
        fillcolour: Raphael.rgb(0, 0, 0),
        textcolour: Raphael.rgb(255, 0, 0),
    },
    HEALTHY = {
        label: tp.TEXT_HEALTHY,
        fillcolour: Raphael.rgb(0, 0, 255),
        textcolour: Raphael.rgb(255, 255, 255),
    },
    TWIRLER = {
        radius: STIMRADIUS * 1.4,
        pointerparams: {
            fill: Raphael.rgb(255, 0, 0),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        angle: 20,
    },
    INDIFFERENCE = {
        label: tp.TEXT_INDIFFERENT,
        shapeattr: {
            fill: Raphael.rgb(0, 100, 0),
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
        top: tp.screenHeight * 0.90,
        bottom: tp.screenHeight * 0.99, // don't go below 0.90 on Android
        radius: 20,
    },
    BACK_TO_CATEGORY = {
        label: tp.TEXT_BACK,
        shapeattr: {
            fill: Raphael.rgb(150, 0, 0),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "text-anchor": "middle" // start, middle, end
        },
        left: tp.screenWidth * 0.05,
        right: tp.screenWidth * 0.15,
        top: tp.screenHeight * 0.94,
        bottom: tp.screenHeight * 0.99,
        radius: 20,
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
        top: tp.screenHeight * 0.4,
        bottom: tp.screenHeight * 0.6,
        radius: 20,
    },
    TASKTYPE_HIGH = {
        label: tp.TEXT_H_ABOVE_1,
        shapeattr: {
            fill: Raphael.rgb(0, 0, 200),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "font-weight": "bold",
            "text-anchor": "middle" // start, middle, end
        },
        left: tp.screenWidth * 0.2,
        right: tp.screenWidth * 0.8,
        top: tp.screenHeight * 0.15,
        bottom: tp.screenHeight * 0.25,
        radius: 20,
    },
    TASKTYPE_MEDIUM = {
        label: tp.TEXT_H_0_TO_1,
        shapeattr: {
            fill: Raphael.rgb(0, 0, 200),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "font-weight": "bold",
            "text-anchor": "middle" // start, middle, end
        },
        left: tp.screenWidth * 0.2,
        right: tp.screenWidth * 0.8,
        top: tp.screenHeight * 0.45,
        bottom: tp.screenHeight * 0.55,
        radius: 20,
    },
    TASKTYPE_LOW = {
        label: tp.TEXT_H_BELOW_0,
        shapeattr: {
            fill: Raphael.rgb(0, 0, 200),
            stroke: STROKE,
            "stroke-width": STROKEWIDTH
        },
        textattr: {
            fill: Raphael.rgb(255, 255, 255),
            font: FONT,
            "font-weight": "bold",
            "text-anchor": "middle" // start, middle, end
        },
        left: tp.screenWidth * 0.2,
        right: tp.screenWidth * 0.8,
        top: tp.screenHeight * 0.75,
        bottom: tp.screenHeight * 0.85,
        radius: 20,
    },
    //-------------------------------------------------------------------------
    // Graphics
    //-------------------------------------------------------------------------
    paper = new Raphael(0, 0, tp.screenWidth, tp.screenHeight),
    //-------------------------------------------------------------------------
    // Functions defined before use to avoid circularity
    //-------------------------------------------------------------------------
    askCategory,
    //-------------------------------------------------------------------------
    // Recording
    //-------------------------------------------------------------------------
    tr = new TrialRecord(); // effectively a global variable; no need to store old trials

//=============================================================================
// More graphics
//=============================================================================

function addP(text, p) {
    return text + "\n(" + (100 * p).toFixed(0) + " in 100)";
}

function pieChart(centre, r, textradius, values, options) {
    // See taskhtmlcommon.js for coordinate/angle conventions
    var angle = -90, // start at the top
        total = 0,
        chart = paper.set(), // start a set
        i;

    function sector(startAngle, endAngle, option, p) {
        var params = {
                fill: option.fillcolour,
                stroke: STROKE,
                "stroke-width": STROKEWIDTH
            },
            angleDifference = endAngle - startAngle,
            textAngle = (startAngle + endAngle) / 2,
            labelcoords = pointOnCircle(centre, textradius, textAngle),
            text = addP(option.label, p),
            label = createText(paper, text, labelcoords.x, labelcoords.y,
                               LABEL_ATTR),
            sect,
            point1,
            point2,
            largeArcFlag = (angleDifference > 180) ? 1 : 0,
            sweepFlag = 1; // clockwise; http://www.w3.org/TR/SVG/paths.html#PathData

        if (angleDifference >= 360) {
            sect = paper.circle(centre.x, centre.y, r).attr(params);
        } else {
            point1 = pointOnCircle(centre, r, startAngle);
            point2 = pointOnCircle(centre, r, endAngle);
            sect = paper.path(["M", centre.x, centre.y, // moveto
                               "L", point1.x, point1.y, // lineto
                               "A", r, r, 0, largeArcFlag, sweepFlag,
                               point2.x, point2.y, // elliptical arc
                               "z" // closepath
                ]).attr(params);
        }
        label.attr("fill", option.textcolour);
        chart.push(sect);
        chart.push(label);
    }

    function process(i) {
        var value = values[i],
            angleplus = 360 * value / total;
        sector(angle, angle + angleplus, options[i], value / total);
        angle += angleplus;
    }

    for (i = 0; i < values.length; i += 1) {
        total += values[i];
    }
    for (i = 0; i < values.length; i += 1) {
        process(i);
    }
    return chart;
}

function showTwirlerPointer(isLeft, starting_p, twirlerTouchedFunction) {
    var centre = {
            x : isLeft ? LEFTSTIMCENTRE : RIGHTSTIMCENTRE,
            y : STIM_VCENTRE
        },
        tip,
        resting_tip_angle,
        moving_tip_angle;

    function createAtZeroAngle() {
        var tip_point = pointOnCircle(centre, STIMRADIUS, 0),
            out1_angle = +TWIRLER.angle / 2,
            out2_angle = -TWIRLER.angle / 2,
            out1_point = pointOnCircle(centre, TWIRLER.radius, out1_angle),
            out2_point = pointOnCircle(centre, TWIRLER.radius, out2_angle),
            largeArcFlag = 0,
            sweepFlag = 0,
            tip_path_string = [
                "M", tip_point.x, tip_point.y,
                "L", out1_point.x, out1_point.y,
                "A", TWIRLER.radius, TWIRLER.radius, 0, largeArcFlag,
                sweepFlag, out2_point.x, out2_point.y,
                "z"
            ];
        tip = paper.path(tip_path_string).attr(TWIRLER.pointerparams);
    }

    function rotateTo(angle) {
        // Animating a path object:
        // http://stackoverflow.com/questions/6282171/raphael-js-how-to-move-animate-a-path-object
        // this.transform("r", angle, centre.x, centre.y);
        // this.attr({x: this.ox + dx, y: this.oy + dy}); -- not for paths
        // https://benknowscode.wordpress.com/tag/raphael/
        var transform_string = [ "r", angle, centre.x, centre.y ];
        tip.transform(transform_string);
    }

    function setRestingAngle(angle) {
        rotateTo(angle);
        resting_tip_angle = angle;
    }

    function getRestingTipPoint() {
        return pointOnCircle(centre, STIMRADIUS, resting_tip_angle);
    }

    function start() {
        // We already know the starting coordinates, esp. of the tip
        moving_tip_angle = resting_tip_angle;
        this.animate({r: 70, opacity: 0.5}, 500, ">");
    }

    function move(dx, dy) {
        var resting_tip_point = getRestingTipPoint(),
            finger = pointAddXY(resting_tip_point, dx, dy),
            vector = vectorFromTo(centre, finger);
        moving_tip_angle = vectorAngleDegrees(vector);
        rotateTo(moving_tip_angle);
    }

    function up() {
        this.animate({r: 50, opacity: 1}, 500, ">");
        setRestingAngle(moving_tip_angle);
        var p = (moving_tip_angle + 90) / 360;
        if (p < 0) {
            p += 1;
        }
        twirlerTouchedFunction(p);
    }

    // Define the tip at angle zero (then we always rotate it relative to that).
    createAtZeroAngle();
    setRestingAngle((360 * starting_p) - 90);
    tip.drag(move, start, up);
    return tip;
}

function showFixed(isLeft, option) {
    var values = [ 100 ],
        options = [ option ],
        centre = {
            x: isLeft ? LEFTSTIMCENTRE : RIGHTSTIMCENTRE,
            y: STIM_VCENTRE
        };
    return pieChart(centre, STIMRADIUS, TEXT_RADIUS, values, options);
}

function lottery(isLeft, p, option1, option2) {
    var values = [ 100 * p, 100 * (1 - p) ],
        options = [ option1, option2 ],
        centre = {
            x: isLeft ? LEFTSTIMCENTRE : RIGHTSTIMCENTRE,
            y: STIM_VCENTRE
        };
    return pieChart(centre, STIMRADIUS, TEXT_RADIUS, values, options);
}

function showGambleInstruction(lotteryOnLeft, choiceType) {
    // textbox is far too slow
    var instructionoption,
        suffix,
        top = 5,
        lineheight = 30,
        // e1,
        e2,
        e3,
        e4;

    trace("showGambleInstruction: arguments = " + JSON.stringify(arguments));
    // Finalize text
    switch (choiceType) {
    case "high":
        //var prefixoption = GAMBLEINSTRUCTION.prefix_high;
        instructionoption = GAMBLEINSTRUCTION.high;
        break;
    case "medium":
        //var prefixoption = GAMBLEINSTRUCTION.prefix_medium;
        instructionoption = GAMBLEINSTRUCTION.medium;
        break;
    case "low":
        //var prefixoption = GAMBLEINSTRUCTION.prefix_low;
        instructionoption = GAMBLEINSTRUCTION.low;
        break;
    }
    instructionoption = instructionoption.replace(
        /FIXEDSIDE/g,
        lotteryOnLeft ? tp.TEXT_RIGHT : tp.TEXT_LEFT
    );
    instructionoption = instructionoption.replace(
        /LOTTERYSIDE/g,
        lotteryOnLeft ? tp.TEXT_LEFT  : tp.TEXT_RIGHT
    );
    suffix = GAMBLEINSTRUCTION.suffix.replace(
        /FIXEDSIDE/g,
        lotteryOnLeft ? tp.TEXT_RIGHT : tp.TEXT_LEFT
    );
    suffix = suffix.replace(
        /LOTTERYSIDE/g,
        lotteryOnLeft ? tp.TEXT_LEFT  : tp.TEXT_RIGHT
    );
    // Display things
    /*
    e1 = createText(paper, prefixoption, GAMBLEINSTRUCTION.left,
                    GAMBLEINSTRUCTION.top + top,
                    GAMBLEINSTRUCTION.textattr),
    alignTop(e1);
    */
    e2 = createText(paper, GAMBLEINSTRUCTION.prefix_2,
                    GAMBLEINSTRUCTION.left,
                    GAMBLEINSTRUCTION.top + top,
                    GAMBLEINSTRUCTION.textattr);
    e2.attr("font-weight", "bold");
    alignTop(e2);
    e3 = createText(paper, instructionoption, GAMBLEINSTRUCTION.left,
                    GAMBLEINSTRUCTION.top + top + lineheight,
                    GAMBLEINSTRUCTION.textattr);
    alignTop(e3);
    e4 = createText(paper, suffix, GAMBLEINSTRUCTION.left,
                    GAMBLEINSTRUCTION.top + top + lineheight * 5,
                    GAMBLEINSTRUCTION.textattr);
    alignTop(e4);
    e4.attr("font-weight", "bold");
}

//=============================================================================
// Saving, exiting
//=============================================================================

function saveTrial() {
    trace("saveTrial: tr = " + JSON.stringify(tr));
    sendEvent({
        eventType: "savetrial",
        data: JSON.stringify(preprocess_moments_for_json_stringify(tr))
    });
}

function exit() {
    trace("exit");
    sendEvent({
        eventType: "exit"
    });
}

function thanks() {
    paper.clear();
    var T = createButton(paper, THANKS);
    setTouchStartEvent(T, function () {
        clearTouchEvents(T);
        exit();
    });
}

//=============================================================================
// Trial
//=============================================================================

function recordChoice(p) {
    trace("recordChoice: p = " + p);
    tr.gamble_responded = true;
    tr.gamble_response_time = now();
    tr.gamble_p = p;
    switch (tr.category_chosen) {
    case "high":
        tr.utility = 1 / p;
        break;
    case "medium":
        tr.utility = p;
        break;
    case "low":
        tr.utility = -p / (1 - p);
        break;
    }

    saveTrial();
    thanks();
}

function giveChoice(choiceType) {
    var h,
        /*
        testbackground = paper.rect(
            0,
            0,
            tp.screenWidth,
            tp.screenHeight).attr({fill:Raphael.rgb(100,0,0)}),
        */
        p,
        lotteryMaker,
        L,
        twirlerTouchedAtLeastOnce = false,
        C = null,
        B;

    function twirlerTouched(p) {
        trace("twirlerTouched: p = " + p);
        L.remove();
        L = lotteryMaker(p);
        if (!twirlerTouchedAtLeastOnce) {
            // Make the "indifference" button appear only after the twirler has been set.
            twirlerTouchedAtLeastOnce = true;
            C = createButton(paper, INDIFFERENCE);
        }
        if (C) {
            setTouchStartEvent(C, function () {
                clearTouchEvents(C);
                recordChoice(p);
            });
        }
    }

    trace("giveChoice: " + choiceType + ", now = " + JSON.stringify(now()));
    tr.category_responded = true;
    tr.category_response_time = now();
    tr.category_chosen = choiceType;
    tr.gamble_lottery_on_left = false; // randomBool();
    // task is more confusing with lots of left/right references. Fix the lottery on the right.
    paper.clear();

    switch (choiceType) {
    case "high":
        h = 1.5;
        // RNC: h > 1, since we should consider mania...
        // If indifferent, p * h + (1 - p) * 0 = 1 * 1  =>  h = 1/p  =>  p = 1/h
        p = 1 / h;
        tr.gamble_lottery_option_p = "current";
        tr.gamble_lottery_option_q = "dead";
        tr.gamble_fixed_option = "healthy";
        lotteryMaker = function (p) {
            return lottery(tr.gamble_lottery_on_left, p, TESTSTATE, DEAD);
        };
        showFixed(!tr.gamble_lottery_on_left, HEALTHY);
        // If the subject chooses A, their utility is HIGHER than h.
        // However, we'll ask them to aim for indifference directly -- simpler.
        break;

    case "medium":
        h = 0.5;
        // NORMAL STATE! 0 <= h <= 1
        // If indifferent, h = p
        // Obvious derivation: p * 1 + (1 - p) * 0 = 1 * h
        p = h;
        tr.gamble_lottery_option_p = "healthy";
        tr.gamble_lottery_option_q = "dead";
        tr.gamble_fixed_option = "current";
        lotteryMaker = function (p) {
            return lottery(tr.gamble_lottery_on_left, p, HEALTHY, DEAD);
        };
        showFixed(!tr.gamble_lottery_on_left, TESTSTATE);
        // If the subject chooses A, their utility is LOWER than h.
        // However, we'll ask them to aim for indifference directly -- simpler.
        break;

    case "low":
        h = -0.5;
        // h < 0: if indifferent here, current state is worse than death
        // If indifferent, Torrance gives h = -p / (1 - p) = p / (p - 1)  =>  p = h / (h - 1)
        // Derivation: p * 1 + (1 - p) * h = 1 * 0  =>  h = -p / (1-p)  => etc.
        p = h / (h - 1);
        tr.gamble_lottery_option_p = "healthy";
        tr.gamble_lottery_option_q = "current";
        tr.gamble_fixed_option = "dead";
        lotteryMaker = function (p) {
            return lottery(tr.gamble_lottery_on_left, p, HEALTHY, TESTSTATE);
        };
        showFixed(!tr.gamble_lottery_on_left, DEAD);
        // If the subject chooses A, their utility is HIGHER than h.
        // Example: h = -1, so p = 0.5: will be indifferent between {0.5 health, 0.5 current} versus {1 death}
        // Example: h = -0.1, so p = 0.0909: will be approx. indifferent between {0.9 health, 0.1 current} versus {1 death}
        // However, we'll ask them to aim for indifference directly -- simpler.
        break;

    default:
        trace("invalid choiceType to giveChoice()");
        break;
    }

    L = lotteryMaker(p);
    tr.gamble_starting_p = p;

    showTwirlerPointer(tr.gamble_lottery_on_left, p, twirlerTouched);
    showGambleInstruction(tr.gamble_lottery_on_left, choiceType);

    B = createButton(paper, BACK_TO_CATEGORY);
    setTouchStartEvent(B, function () { askCategory(); });

    tr.gamble_start_time = now();
    trace("giveChoice ENDING: now = " + JSON.stringify(now()));
}

askCategory = function () {
    paper.clear();
    createText(paper, INITIALINSTRUCTION.text, INITIALINSTRUCTION.xcentre,
               INITIALINSTRUCTION.ycentre, INITIALINSTRUCTION.textattr);
    var H = createButton(paper, TASKTYPE_HIGH),
        M = createButton(paper, TASKTYPE_MEDIUM),
        L = createButton(paper, TASKTYPE_LOW);
    setTouchStartEvent(H, function () { giveChoice("high"); });
    setTouchStartEvent(M, function () { giveChoice("medium"); });
    setTouchStartEvent(L, function () { giveChoice("low"); });
    tr.category_start_time = now();
};

//=============================================================================
// Task
//=============================================================================

function startTask() {
    trace("starttask: params = " + JSON.stringify(tp));
    askCategory();
}

registerWebviewTask(TASKNAME, EVENTNAME_IN, EVENTNAME_OUT,
                    startTask, incomingEvent);
