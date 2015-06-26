// cardinal_expdetthreshold_task.jsx

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

/*jslint node: true, plusplus: true */
"use strict";
/*global unescape */
/*global inTitanium, trace, now, sendEvent,
    preprocess_moments_for_json_stringify,
    createText, createButton,
    setTouchStartEvent, clearTouchEvents,
    assert, copyProperties,
    registerWebviewTask,
*/
/*global Raphael */

//=============================================================================
// Comments
//=============================================================================

/*
- Sounds: originals (Rogers 1999 Psychopharm 146:482) were:
    correct = 1200 Hz, 164 ms, volume not given
    incorrect = 200 Hz, 550 ms, volume not given
  However, on the tablet, using the Audacity tone generator with the same
  parameters (in other respects) for the stimuli, makes the incorrect one
  nearly inaudible. So let's use different notes.
- Actual source in my chord.py. All are sine waves.
    correct = E5 + G5 + C6 (Cmaj), 164 ms
    incorrect = A4 + C5 + Eb5 + F#5 (Adim7), 550 ms

- Any further control required over over exact values used for shape/colour/
  number?
*/

//=============================================================================
// General functions
//=============================================================================

function dwor(bucket) {
    // Draw without replacement
    // http://stackoverflow.com/questions/12987719
    assert(bucket instanceof Array, "dwor() called with non-array");
    assert(bucket.length > 0, "dwor() called with empty bucket");
    var randomIndex = Math.floor(Math.random() * bucket.length);
    return bucket.splice(randomIndex, 1)[0];
}

function drawreplace(bucket) {
    // Draw with replacement
    assert(bucket instanceof Array, "drawreplace() called with non-array");
    assert(bucket.length > 0, "drawreplace() called with empty bucket");
    var randomIndex = Math.floor(Math.random() * bucket.length);
    return bucket[randomIndex];
}

function setsubtract(first, second) {
    // http://stackoverflow.com/questions/1187518/javascript-array-difference
    assert(first instanceof Array && second instanceof Array,
           "setsubtract() called with non-array(s)");
    return first.filter(function (i) {
        return second.indexOf(i) < 0;
    });
}

function range(start, end) {
    // Creates sequence start ... (end - 1) inclusive, for integer input.
    // For a single parameter n, performs range(0, n).
    assert(typeof start === 'number',
           "no or non-numerical first input to range()");
    if (end === undefined) {
        end = start;
        start = 0;
    } else {
        assert(typeof end === 'number',
               "non-numerical second input to range()");
    }
    var arr = [],
        i,
        tmp;
    if (start > end) {
        tmp = start;
        start = end;
        end = tmp;
    }
    for (i = start; i < end; ++i) {
        arr.push(i);
    }
    return arr;
}

function rep(x, each, times) {
    // Repeat; vaguely like the R rep() function.
    var arr = [],
        i,
        j,
        k;
    times = times !== undefined ? times : 1;
    if (x instanceof Array) {
        for (i = 0; i < times; ++i) {
            for (j = 0; j < x.length; ++j) {
                for (k = 0; k < each; ++k) {
                    arr.push(x[j]);
                }
            }
        }
    } else {
        for (i = 0; i < each * times; ++i) {
            arr.push(x);
        }
    }
    return arr;
}

function distribute(n, min, max) {
    // Fence/fence-post problem; return centre of fence segments.
    var extent = max - min,
        each = extent / n,
        centre_offset = each / 2,
        i,
        pos = [];
    for (i = 0; i < n; ++i) {
        pos.push(min + i * each + centre_offset);
    }
    return pos;
}

function griddimensions(n, aspect) {
    aspect = aspect !== undefined ? aspect : 1;
    // Solve the equations:
    //      x * y >= n
    //      aspect ~= x / y
    // ... for smallest x, y. Thus:
    //      x = aspect * y
    //      aspect * y * y >= n
    var y = Math.ceil(Math.sqrt(n / aspect)),
        x = Math.ceil(n / y);
    return {x: x, y: y};
}

//=============================================================================
// Variables
//=============================================================================

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
    //-------------------------------------------------------------------------
    // Events
    //-------------------------------------------------------------------------
    TASKNAME = "IDED3D",
    EVENTNAME_OUT = "IDED3D_EVENT_FROM_WEBVIEW",
    EVENTNAME_IN = "IDED3D_EVENT_TO_WEBVIEW",
    //-------------------------------------------------------------------------
    // Shapes
    //-------------------------------------------------------------------------
    SHAPE_DEFINITIONS = [
        /*
            List of paths.
            MULTI.PAT contained 96, but were only 12 things repeated 8 times.
            All stimuli redrawn.
            Good online editor:
                http://jsfiddle.net/DFhUF/1393/
            ... being jsfiddle set to the Raphael 2.1.0 framework "onLoad".
            Code:

var path = [
        // DETAILS HERE
        ["m10,-53 l20,100 l-60,0 z m50,60 l-120,20 l0,-50 z"], // 0: up-pointing triangle and right-pointing triangle
        ["m0,-50 l-57,57 l28,28 l28,-28 l28,28 l28,-28 z"], // 1: stealth bomber flying up
        ["m-15,-50 l-45,25 l90,0 z m15,35 l-45,25 l90,0 z m15,35 l-45,25 l90,0 z"], // 2: stacked triangle hats slightly offset horizontally
        ["m-60,-11 l94,55 l26,-28 l-38,-15 l38,-15 l-26,-28 l-94,55 z"], // 3: small-tailed fish with gaping mouth pointing right
        ["m-20,-50 l-40,50 l45,0 l0,50 l30,0 l0,-50 l45,0 l-45,-50 z"], // 4: top-truncated tree
        ["m-60,-36 l120,0 l0,72 l-40,0 l0,-36 l-40,0 l0,36, l-40,0 z"], // 5: side view of block table, or blocky inverted U
        ["m0,-40 l60,40 l-40,27 l0,13 l-40,0 l0,-13 l-40,-27 z"], // 6: diamond-like tree
        ["m-33,40 l-27,-40 l27,-40 l33,27 l33,-27 l27,40 l-27,40 l-33,-27 z"], // 7: bow tie
        ["m-60,-30 l60,-30 l60,30 l0,60 l-60,30 l-60,-30 z"], // 8: hexagon
        ["m-60,60 l120,0 l-60,-60 z m0,-120 l120,0 l-60,60 z"], // 9: hourglass of triangles
        ["m-60,-40 l0,68 l120,0 l-45,-30 l0,11 l-45,-38 l0,23 z"], // 10: mountain range
        ["m-60,0 l34,-43 l86,0 l-34,43 l34,43 l-86,0 z"], // 11: left-pointing arrow feathers
    ],
    index = 10,  // currently working on this one
    s = 120,  // target size; width and height
    c = 250,  // centre
    paper = Raphael(0, 0, c*2, c*2),
    crosshairs = ["M", 0, c, "L", c*2, c, "M", c, 0,  "L", c, c*2],
    chattr = {stroke: "#f00", opacity: 1, "stroke-width" : 1},
    gridattr = {stroke: "#888", opacity: 0.5, "stroke-width" : 1},
    textattr = {fill: "red", font: "20px Arial", "text-anchor": "middle"},
    pathattr = {stroke: "#808", opacity: 1, "stroke-width" : 1, fill: "#ccf"},
    i;
paper.path(path[index]).translate(c, c).attr(pathattr);
for (i = 0; i < 2*c; i += 10) {
    paper.path(["M", 0, i, "L", 2*c, i]).attr(gridattr);
    paper.path(["M", i, 0, "L", i, 2*c]).attr(gridattr);
}
paper.rect(c - s/2, c - s/2, s, s).attr(chattr);
paper.path(crosshairs).attr(chattr);
paper.text(c, c, "0").attr(textattr);

        */
        ["m10,-53 l20,100 l-60,0 z m50,60 l-120,20 l0,-50 z"], // 0: up-pointing triangle and right-pointing triangle
        ["m0,-50 l-57,57 l28,28 l28,-28 l28,28 l28,-28 z"], // 1: stealth bomber flying up
        ["m-15,-50 l-45,25 l90,0 z m15,35 l-45,25 l90,0 z m15,35 l-45,25 l90,0 z"], // 2: stacked triangle hats slightly offset horizontally
        ["m-60,-11 l94,55 l26,-28 l-38,-15 l38,-15 l-26,-28 l-94,55 z"], // 3: small-tailed fish with gaping mouth pointing right
        ["m-20,-50 l-40,50 l45,0 l0,50 l30,0 l0,-50 l45,0 l-45,-50 z"], // 4: top-truncated tree
        ["m-60,-36 l120,0 l0,72 l-40,0 l0,-36 l-40,0 l0,36, l-40,0 z"], // 5: side view of block table, or blocky inverted U
        ["m0,-40 l60,40 l-40,27 l0,13 l-40,0 l0,-13 l-40,-27 z"], // 6: diamond-like tree
        ["m-33,40 l-27,-40 l27,-40 l33,27 l33,-27 l27,40 l-27,40 l-33,-27 z"], // 7: bow tie
        ["m-60,-30 l60,-30 l60,30 l0,60 l-60,30 l-60,-30 z"], // 8: hexagon
        ["m-60,60 l120,0 l-60,-60 z m0,-120 l120,0 l-60,60 z"], // 9: hourglass of triangles
        ["m-60,-40 l0,68 l120,0 l-45,-30 l0,11 l-45,-38 l0,23 z"], // 10: mountain range
        ["m-60,0 l34,-43 l86,0 l-34,43 l34,43 l-86,0 z"], // 11: left-pointing arrow feathers
    ],
    STIMSIZE = 120,  // max width/height
    //-------------------------------------------------------------------------
    // Task design
    //-------------------------------------------------------------------------
    SHAPE = "shape",
    COLOUR = "colour",
    NUMBER = "number",
    POSSIBLE_SHAPES = range(SHAPE_DEFINITIONS.length),
    POSSIBLE_COLOURS = [  // HTML colours
        "#555", // CGA: dark grey
        "#55f", // CGA: light blue
        "#5f5", // CGA: light green
        "#5ff", // CGA: light cyan
        "#f55", // CGA: light red
        "#f5f", // CGA: light magenta
        "#ff5", // CGA: yellow
        "#fff", // white
    ],
    POSSIBLE_NUMBERS = range(tp.min_number, tp.max_number + 1),
    //-------------------------------------------------------------------------
    // Locations
    //-------------------------------------------------------------------------
    BOXWIDTH = tp.screenWidth * 0.45,  // use 90%
    BOXHEIGHT = tp.screenHeight * 0.3,  // use 90%
    VDIST = distribute(3, 0, tp.screenHeight),
    HDIST = [
        tp.screenWidth * 0.25,
        tp.screenWidth * 0.5,
        tp.screenWidth * 0.75
    ],
    LOCATIONS = [
        {
            // top
            xcentre: HDIST[1],
            ycentre: VDIST[0],
            width: BOXWIDTH,
            height: BOXHEIGHT,
            left: HDIST[1] - BOXWIDTH / 2,
            top: VDIST[0] - BOXHEIGHT / 2,
        },
        {
            // right
            xcentre: HDIST[2],
            ycentre: VDIST[1],
            width: BOXWIDTH,
            height: BOXHEIGHT,
            left: HDIST[2] - BOXWIDTH / 2,
            top: VDIST[1] - BOXHEIGHT / 2,
        },
        {
            // bottom
            xcentre: HDIST[1],
            ycentre: VDIST[2],
            width: BOXWIDTH,
            height: BOXHEIGHT,
            left: HDIST[1] - BOXWIDTH / 2,
            top: VDIST[2] - BOXHEIGHT / 2,
        },
        {
            // left
            xcentre: HDIST[0],
            ycentre: VDIST[1],
            width: BOXWIDTH,
            height: BOXHEIGHT,
            left: HDIST[0] - BOXWIDTH / 2,
            top: VDIST[1] - BOXHEIGHT / 2,
        },
    ],
    //-------------------------------------------------------------------------
    // Recording
    //-------------------------------------------------------------------------
    stages = [],
    trials = [],
    currentStage = 0,
    currentTrial = -1,
    //-------------------------------------------------------------------------
    // Implementation
    //-------------------------------------------------------------------------
    STROKE = Raphael.rgb(255, 255, 255),
    STROKEWIDTH = 3,
    STIMULUS_STROKEWIDTH = 1,
    BGCOLOUR_R = 0,
    BGCOLOUR_G = 0,
    BGCOLOUR_B = 0,
    BGCOLOUR = Raphael.rgb(BGCOLOUR_R, BGCOLOUR_G, BGCOLOUR_B),
    BOXATTR = {
        stroke: 'rgba(255,255,255,0.5)',
        'stroke-width': 3,
        fill: BGCOLOUR,  // or it won't be touchable
    },
    FONT = "20px Fontin-Sans, Arial",
    BIGFONT = "50px Fontin-Sans, Arial",
    PROMPT_X = tp.screenWidth * 0.5,
    PROMPT_Y = tp.screenHeight * 0.5,
    PROMPT_ATTR = {
        fill: Raphael.rgb(255, 255, 255),
        font: FONT,
        "text-anchor": "middle" // start, middle, end
    },
    DEBUG_ATTR = {
        fill: Raphael.rgb(255, 255, 255),
        font: FONT,
        "text-anchor": "middle"
    },
    CORRECT_ATTR = {
        fill: Raphael.rgb(0, 255, 0),  // green; Rogers et al. 1999
        font: BIGFONT,
        "text-anchor": "middle",
        "font-weight": "bold"
    },
    INCORRECT_ATTR = {
        fill: Raphael.rgb(255, 0, 0),  // red; Rogers et al. 1999
        font: BIGFONT,
        "text-anchor": "middle",
        "font-weight": "bold"
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
    OBSCURE_ATTR = {  // used to dim the display during feedback
        fill: Raphael.rgb(0, 0, 0),
        "fill-opacity": 0.4,
    },
    //-------------------------------------------------------------------------
    // Graphics
    //-------------------------------------------------------------------------
    paper = new Raphael(0, 0, tp.screenWidth, tp.screenHeight),
    //-------------------------------------------------------------------------
    // Functions defined before use to avoid circularity
    //-------------------------------------------------------------------------
    nextTrial;

//=============================================================================
// Trial design/calculation
//=============================================================================

function StageRecord(stageNum, stageName,
                     relevant_dimension, correct_exemplar, incorrect_exemplar,
                     correctStimulusShapes,
                     correctStimulusColours,
                     correctStimulusNumbers,
                     incorrectStimulusShapes,
                     incorrectStimulusColours,
                     incorrectStimulusNumbers,
                     incorrectStimulusCanOverlap) {
    // Note: object variables used internally (camelCase) have different names
    // from text-based versions sent to the database.

    // Database, config:
    this.ided3d_id = tp.ided3d_id;
    this.stage = stageNum;
    this.stage_name = stageName;
    this.relevant_dimension = relevant_dimension;
    this.correct_exemplar = correct_exemplar;
    this.incorrect_exemplar = incorrect_exemplar;
    this.correct_stimulus_shapes = correctStimulusShapes.join();
    this.correct_stimulus_colours = correctStimulusColours.join();
    this.correct_stimulus_numbers = correctStimulusNumbers.join();
    this.incorrect_stimulus_shapes = incorrectStimulusShapes.join();
    this.incorrect_stimulus_colours = incorrectStimulusColours.join();
    this.incorrect_stimulus_numbers = incorrectStimulusNumbers.join();
    // Database, results:
    this.first_trial_num = null;
    this.n_completed_trials = 0;
    this.n_correct = 0;
    this.n_incorrect = 0;
    this.stage_passed = false;
    this.stage_failed = false;
    // Internal only:
    this.correctStimulusShapes = correctStimulusShapes;
    this.correctStimulusColours = correctStimulusColours;
    this.correctStimulusNumbers = correctStimulusNumbers;
    this.incorrectStimulusShapes = incorrectStimulusShapes;
    this.incorrectStimulusColours = incorrectStimulusColours;
    this.incorrectStimulusNumbers = incorrectStimulusNumbers;
    this.incorrectStimulusCanOverlap = incorrectStimulusCanOverlap;
}

function makeStages(counterbalance_dimensions) {
    /*
    counterbalance_dimensions: integer 0-5
        value   firstRelevantDimension  secondRelevantDimension
        0       0                       1
        1       1                       2
        2       2                       0
        3       0                       2
        4       1                       0
        5       2                       1
        ... where 0=SHAPE, 1=COLOUR, 2=NUMBER (indices of DIMENSIONS)
    */

    function getShapes(exset, dimset) {
        if (dimset.dimname1 === SHAPE) {
            return exset.exlist1;
        }
        if (dimset.dimname2 === SHAPE) {
            return exset.exlist2;
        }
        if (dimset.dimname3 === SHAPE) {
            return exset.exlist3;
        }
        assert(false, "Bug in getShapes");
        return [];  // unreachable code
    }

    function getColours(exset, dimset) {
        if (dimset.dimname1 === COLOUR) {
            return exset.exlist1;
        }
        if (dimset.dimname2 === COLOUR) {
            return exset.exlist2;
        }
        if (dimset.dimname3 === COLOUR) {
            return exset.exlist3;
        }
        assert(false, "Bug in getColours");
        return [];  // unreachable code
    }

    function getNumbers(exset, dimset) {
        if (dimset.dimname1 === NUMBER) {
            return exset.exlist1;
        }
        if (dimset.dimname2 === NUMBER) {
            return exset.exlist2;
        }
        if (dimset.dimname3 === NUMBER) {
            return exset.exlist3;
        }
        assert(false, "Bug in getNumbers");
        return [];  // unreachable code
    }

    var DIMENSIONS = [SHAPE, COLOUR, NUMBER],
        POSSIBILITIES = [POSSIBLE_SHAPES, POSSIBLE_COLOURS, POSSIBLE_NUMBERS],
        // ... order must match DIMENSIONS
        nDimensions = DIMENSIONS.length,
        // Counterbalancing:
        cb1max = nDimensions,
        cb2max = nDimensions - 1,
        cb1 = counterbalance_dimensions % cb1max,
        cb2 = Math.floor(counterbalance_dimensions / cb1max) % cb2max,
        // Dimensions:
        firstRelevantDimIndex = cb1,
        secondRelevantDimIndex = (
            (firstRelevantDimIndex + 1 + cb2) % nDimensions
        ),
        thirdDimIndex = (
            (firstRelevantDimIndex + 1 + (cb2max - 1 - cb2)) % nDimensions
        ),
        firstDimName = DIMENSIONS[firstRelevantDimIndex],
        secondDimName = DIMENSIONS[secondRelevantDimIndex],
        thirdDimName = DIMENSIONS[thirdDimIndex],
        // Exemplars (poss for possibilities):
        possFirstDim = POSSIBILITIES[firstRelevantDimIndex].slice(0),
        possSecondDim = POSSIBILITIES[secondRelevantDimIndex].slice(0),
        possThirdDim = POSSIBILITIES[thirdDimIndex].slice(0),
        // ... relevant ones:
        sdCorrectExemplar = dwor(possFirstDim),
        sdIncorrectExemplar = dwor(possFirstDim),
        idCorrectExemplar = dwor(possFirstDim),
        idIncorrectExemplar = dwor(possFirstDim),
        edCorrectExemplar = dwor(possSecondDim),
        edIncorrectExemplar = dwor(possSecondDim),
        // ... irrelevant ones:
        sdIrrelevantExemplarSecondDim = dwor(possSecondDim),
        sdIrrelevantExemplarThirdDim = dwor(possThirdDim),
        cdIrrelevantExemplarsSecondDim = [
            // Only two distracting exemplars in each irrelevant dimension.
            dwor(possSecondDim),
            dwor(possSecondDim)
        ],
        cdIrrelevantExemplarsThirdDim = [
            dwor(possThirdDim),
            dwor(possThirdDim)
        ],
        idIrrelevantExemplarsSecondDim = [
            // Only two distracting exemplars in each irrelevant dimension.
            dwor(possSecondDim),
            dwor(possSecondDim)
        ],
        idIrrelevantExemplarsThirdDim = [
            dwor(possThirdDim),
            dwor(possThirdDim)
        ],
        edIrrelevantExemplarsFirstDim = [
            // Only two distracting exemplars in each irrelevant dimension.
            dwor(possFirstDim),
            dwor(possFirstDim)
        ],
        edIrrelevantExemplarsThirdDim = [
            dwor(possThirdDim),
            dwor(possThirdDim)
        ],
        // final stimulus collections
        dimset = {
            dimname1: firstDimName,
            dimname2: secondDimName,
            dimname3: thirdDimName,
        },
        sdCorrectSet = {
            exlist1: [sdCorrectExemplar],
            exlist2: [sdIrrelevantExemplarSecondDim],
            exlist3: [sdIrrelevantExemplarThirdDim],
        },
        sdIncorrectSet = {
            exlist1: [sdIncorrectExemplar],
            exlist2: [sdIrrelevantExemplarSecondDim],
            exlist3: [sdIrrelevantExemplarThirdDim],
        },
        sdrCorrectSet = {
            exlist1: [sdIncorrectExemplar],
            exlist2: [sdIrrelevantExemplarSecondDim],
            exlist3: [sdIrrelevantExemplarThirdDim],
        },
        sdrIncorrectSet = {
            exlist1: [sdCorrectExemplar],
            exlist2: [sdIrrelevantExemplarSecondDim],
            exlist3: [sdIrrelevantExemplarThirdDim],
        },
        cdCorrectSet = {
            exlist1: [sdIncorrectExemplar],
            exlist2: cdIrrelevantExemplarsSecondDim,
            exlist3: cdIrrelevantExemplarsThirdDim,
        },
        cdIncorrectSet = {
            exlist1: [sdCorrectExemplar],
            exlist2: cdIrrelevantExemplarsSecondDim,
            exlist3: cdIrrelevantExemplarsThirdDim,
        },
        cdrCorrectSet = {
            exlist1: [sdCorrectExemplar],
            exlist2: cdIrrelevantExemplarsSecondDim,
            exlist3: cdIrrelevantExemplarsThirdDim,
        },
        cdrIncorrectSet = {
            exlist1: [sdIncorrectExemplar],
            exlist2: cdIrrelevantExemplarsSecondDim,
            exlist3: cdIrrelevantExemplarsThirdDim,
        },
        idCorrectSet = {
            exlist1: [idCorrectExemplar],
            exlist2: idIrrelevantExemplarsSecondDim,
            exlist3: idIrrelevantExemplarsThirdDim,
        },
        idIncorrectSet = {
            exlist1: [idIncorrectExemplar],
            exlist2: idIrrelevantExemplarsSecondDim,
            exlist3: idIrrelevantExemplarsThirdDim,
        },
        idrCorrectSet = {
            exlist1: [idIncorrectExemplar],
            exlist2: idIrrelevantExemplarsSecondDim,
            exlist3: idIrrelevantExemplarsThirdDim,
        },
        idrIncorrectSet = {
            exlist1: [idCorrectExemplar],
            exlist2: idIrrelevantExemplarsSecondDim,
            exlist3: idIrrelevantExemplarsThirdDim,
        },
        edCorrectSet = {
            exlist1: edIrrelevantExemplarsFirstDim,
            exlist2: [edCorrectExemplar],
            exlist3: edIrrelevantExemplarsThirdDim,
        },
        edIncorrectSet = {
            exlist1: edIrrelevantExemplarsFirstDim,
            exlist2: [edIncorrectExemplar],
            exlist3: edIrrelevantExemplarsThirdDim,
        },
        edrCorrectSet = {
            exlist1: edIrrelevantExemplarsFirstDim,
            exlist2: [edIncorrectExemplar],
            exlist3: edIrrelevantExemplarsThirdDim,
        },
        edrIncorrectSet = {
            exlist1: edIrrelevantExemplarsFirstDim,
            exlist2: [edCorrectExemplar],
            exlist3: edIrrelevantExemplarsThirdDim,
        },
        stageNum = 1;

    return [
        new StageRecord(
            stageNum++,
            "SD", /* Only a single dimension varies. */
            firstDimName,
            sdCorrectExemplar,
            sdIncorrectExemplar,
            getShapes(sdCorrectSet, dimset),
            getColours(sdCorrectSet, dimset),
            getNumbers(sdCorrectSet, dimset),
            getShapes(sdIncorrectSet, dimset),
            getColours(sdIncorrectSet, dimset),
            getNumbers(sdIncorrectSet, dimset),
            true  // incorrectStimulusCanOverlap
        ),
        new StageRecord(
            stageNum++,
            "SDr", /* Reversal of SD */
            firstDimName,
            sdIncorrectExemplar,
            sdCorrectExemplar,
            getShapes(sdrCorrectSet, dimset),
            getColours(sdrCorrectSet, dimset),
            getNumbers(sdrCorrectSet, dimset),
            getShapes(sdrIncorrectSet, dimset),
            getColours(sdrIncorrectSet, dimset),
            getNumbers(sdrIncorrectSet, dimset),
            true  // incorrectStimulusCanOverlap
        ),
        new StageRecord(
            stageNum++,
            "CD",
            /*
            The phrase "compound discrimination" is ambiguous.
            The discrimination is not that a compound stimulus is correct
            (e.g. blue square), but that a particular unidimensional exemplar
            (e.g. blue) is correct, while the stimuli also vary along
            irrelevant dimensions (e.g. two/four, square/circle).
            */
            firstDimName,
            sdIncorrectExemplar,
            sdCorrectExemplar,
            getShapes(cdCorrectSet, dimset),
            getColours(cdCorrectSet, dimset),
            getNumbers(cdCorrectSet, dimset),
            getShapes(cdIncorrectSet, dimset),
            getColours(cdIncorrectSet, dimset),
            getNumbers(cdIncorrectSet, dimset),
            false  // incorrectStimulusCanOverlap
        ),
        new StageRecord(
            stageNum++,
            "CDr", /* Reversal of CD */
            firstDimName,
            sdCorrectExemplar,
            sdIncorrectExemplar,
            getShapes(cdrCorrectSet, dimset),
            getColours(cdrCorrectSet, dimset),
            getNumbers(cdrCorrectSet, dimset),
            getShapes(cdrIncorrectSet, dimset),
            getColours(cdrIncorrectSet, dimset),
            getNumbers(cdrIncorrectSet, dimset),
            false  // incorrectStimulusCanOverlap
        ),
        new StageRecord(
            stageNum++,
            "ID", /* Intradimensional shift */
            firstDimName,
            idCorrectExemplar,
            idIncorrectExemplar,
            getShapes(idCorrectSet, dimset),
            getColours(idCorrectSet, dimset),
            getNumbers(idCorrectSet, dimset),
            getShapes(idIncorrectSet, dimset),
            getColours(idIncorrectSet, dimset),
            getNumbers(idIncorrectSet, dimset),
            false  // incorrectStimulusCanOverlap
        ),
        new StageRecord(
            stageNum++,
            "IDr", /* ID reversal */
            firstDimName,
            idIncorrectExemplar,
            idCorrectExemplar,
            getShapes(idrCorrectSet, dimset),
            getColours(idrCorrectSet, dimset),
            getNumbers(idrCorrectSet, dimset),
            getShapes(idrIncorrectSet, dimset),
            getColours(idrIncorrectSet, dimset),
            getNumbers(idrIncorrectSet, dimset),
            false  // incorrectStimulusCanOverlap
        ),
        new StageRecord(
            stageNum++,
            "ED", /* Extradimensional shift */
            secondDimName,
            edCorrectExemplar,
            edIncorrectExemplar,
            getShapes(edCorrectSet, dimset),
            getColours(edCorrectSet, dimset),
            getNumbers(edCorrectSet, dimset),
            getShapes(edIncorrectSet, dimset),
            getColours(edIncorrectSet, dimset),
            getNumbers(edIncorrectSet, dimset),
            false  // incorrectStimulusCanOverlap
        ),
        new StageRecord(
            stageNum++,
            "EDr", /* ED reversal */
            secondDimName,
            edIncorrectExemplar,
            edCorrectExemplar,
            getShapes(edrCorrectSet, dimset),
            getColours(edrCorrectSet, dimset),
            getNumbers(edrCorrectSet, dimset),
            getShapes(edrIncorrectSet, dimset),
            getColours(edrIncorrectSet, dimset),
            getNumbers(edrIncorrectSet, dimset),
            false  // incorrectStimulusCanOverlap
        ),
    ];
}

//=============================================================================
// Trial creation/data structures
//=============================================================================

function TrialRecord(trialNumZeroBased, stageNumZeroBased) {
    assert(stageNumZeroBased >= 0 && stageNumZeroBased < stages.length,
           "TrialRecord() called with invalid stageNumZeroBased");
    var st = stages[stageNumZeroBased],
        availableLocations = range(LOCATIONS.length);
    this.ided3d_id = tp.ided3d_id;
    this.trial /* 1-based */ = trialNumZeroBased + 1;
    this.stageZeroBased = stageNumZeroBased;  // not stored in database
    this.stage /* 1-based */ = stageNumZeroBased + 1;
    // Locations
    this.correct_location = dwor(availableLocations);
    this.incorrect_location = dwor(availableLocations);
    // Stimuli
    this.correct_shape = drawreplace(st.correctStimulusShapes);
    this.correct_colour = drawreplace(st.correctStimulusColours);
    this.correct_number = drawreplace(st.correctStimulusNumbers);
    if (st.incorrectStimulusCanOverlap) {
        this.incorrect_shape = drawreplace(st.incorrectStimulusShapes);
        this.incorrect_colour = drawreplace(st.incorrectStimulusColours);
        this.incorrect_number = drawreplace(st.incorrectStimulusNumbers);
    } else {
        // Constraint for compound discriminations: the incorrect stimulus
        // should never match the correct one in any aspect. Remove the correct
        // exemplar from consideration before drawing, as follows.
        this.incorrect_shape = drawreplace(
            setsubtract(st.incorrectStimulusShapes, [this.correct_shape])
        );
        this.incorrect_colour = drawreplace(
            setsubtract(st.incorrectStimulusColours, [this.correct_colour])
        );
        this.incorrect_number = drawreplace(
            setsubtract(st.incorrectStimulusNumbers, [this.correct_number])
        );
    }
    // Trial
    this.trial_start_time = null;
    // Response
    this.responded = null;
    this.response_time = null;
    this.response_latency_ms = null;
    this.correct = null;
    this.incorrect = null;
}

//=============================================================================
// Saving, exiting
//=============================================================================

function saveShapes() {
    trace("saveShapes");
    sendEvent({
        eventType: "saveshapes",
        data: JSON.stringify(SHAPE_DEFINITIONS)
    });
}

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

function saveStage(s) {
    var st = stages[s];
    trace("saveStage: st = " + JSON.stringify(st));
    sendEvent({
        eventType: "savestage",
        data: JSON.stringify(preprocess_moments_for_json_stringify(st))
    });
}

function saveAllStages() {
    var s;
    for (s = 0; s < stages.length; s += 1) {
        saveStage(s);
    }
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
    saveAllStages();
    saveAllTrials();
    exit(false);
}

//=============================================================================
// Trials
//=============================================================================

function iti() {
    trace("iti()");
    paper.clear();
    setTimeout(function () { nextTrial(); }, tp.iti_ms);
}

function wait_after_beep() {
    trace("wait_after_beep()");
    setTimeout(function () { iti(); }, tp.pause_after_beep_ms);
}

function showAnswer(correct) {
    trace("showAnswer()");
    // correct: Boolean
    paper.rect(0, 0, tp.screenWidth, tp.screenHeight).attr(OBSCURE_ATTR);
    if (correct) {
        createText(paper, tp.CORRECT, PROMPT_X, PROMPT_Y, CORRECT_ATTR);
    } else {
        createText(paper, tp.INCORRECT, PROMPT_X, PROMPT_Y, INCORRECT_ATTR);
    }
    sendEvent({eventType: correct ? "correctsound" : "incorrectsound"});
    setTimeout(
        function () { wait_after_beep(); },
        correct ? tp.correct_sound_duration_ms : tp.incorrect_sound_duration_ms
    );
}

function recordResponse(correct) {
    if (trials[currentTrial].responded) {
        // prevent double-responding, since the stimuli are still displayed
        // during the "correct/incorrect" feedback (and we haven't removed
        // their touch-sensitivity)
        return;
    }
    trace("recordResponse(" + correct + ")");
    trials[currentTrial].responded = true;
    trials[currentTrial].response_time = now();
    trials[currentTrial].response_latency_ms = (
        trials[currentTrial].response_time -
        trials[currentTrial].trial_start_time
    );
    trials[currentTrial].correct = correct;
    trials[currentTrial].incorrect = !correct;
    stages[currentStage].n_correct += correct ? 1 : 0;
    stages[currentStage].n_incorrect += !correct ? 1 : 0;
    showAnswer(correct);
}

function stimCentres(n) {
    // Centre-of-stimulus positions within box.
    // Distribute stimuli about (0, 0) in an imaginary box that's 1 x 1,
    // i.e. from -0.5 to +0.5 in each direction.
    var x,
        y,
        left = -0.5,
        right = +0.5,
        top = -0.5,
        bottom = +0.5,
        topx,
        bottomx,
        topy,
        bottomy,
        tempy,
        ntop,
        nbottom;
    switch (n) {
    // horizontal row:
    case 1:
    case 2:
        x = distribute(n, left, right);
        y = rep(0, n);
        break;
    // two rows:
    case 4:
    case 6:  // Rogers 1999 gives this example
    case 8:
        x = rep(distribute(n / 2, left, right), 1, 2);
        y = rep(distribute(2, top, bottom), n / 2, 1);
        break;
    // one fewer on bottom than top:
    case 3:  // Rogers 1999 gives this example
    case 5:
    case 7:
    case 9:
        ntop = Math.floor(n / 2);
        nbottom = Math.ceil(n / 2);
        topx = distribute(ntop, left, right);
        bottomx = distribute(nbottom, left, right);
        tempy = distribute(2, top, bottom);
        topy = rep(tempy[0], ntop);
        bottomy = rep(tempy[1], nbottom);
        x = topx.concat(bottomx);
        y = topy.concat(bottomy);
        break;
    default:
        assert(false, "unknown n in stimCentre");
        return {};  // unreachable code
    }
    assert(x.length === n && y.length === n, "bug in stimCentre()");
    return {x: x, y: y};
}

function showIndividualStimulus(shape, colour, x, y, scale) {
    trace("showIndividualStimulus(" + shape + ", " + colour + ", " +
          x + ", " + y + ")");
    // displays Raphael stimulus centred at x, y
    assert(shape >= 0 && shape < SHAPE_DEFINITIONS.length,
           "Invalid shape passed to showIndividualStimulus()");
    var pathlist = SHAPE_DEFINITIONS[shape],
        attrs = {
            "stroke": colour,
            "fill": colour,
            "stroke-width": STIMULUS_STROKEWIDTH
        },
        t = (
            // scale:
            "s" + scale +
            // translate (correcting for current scaling):
            "t" + (x / scale) + "," + (y / scale)
        );
    return paper.path(pathlist).transform(t).attr(attrs);
}

function debugDisplayStimuli() {
    trace("debugDisplayStimuli()");
    var nstimuli = SHAPE_DEFINITIONS.length,
        aspect = tp.screenWidth / tp.screenHeight,
        gridinfo = griddimensions(nstimuli, aspect),
        nx = gridinfo.x,
        ny = gridinfo.y,
        x = distribute(nx, 0, tp.screenWidth),
        y = distribute(ny, 0, tp.screenHeight),
        scale = (
            0.8 * Math.min(tp.screenWidth / nx, tp.screenHeight / ny) / STIMSIZE
        ),
        i,
        j,
        n = 0,
        stim,
        fn = function () { exit(true); };
    for (j = 0; j < ny; ++j) {
        for (i = 0; i < nx; ++i) {
            stim = showIndividualStimulus(n, "grey", x[i], y[j], scale);
            setTouchStartEvent(stim, fn);
            createText(paper, n, x[i], y[j], DEBUG_ATTR);
            n += 1;
        }
    }
}

function showEmptyBox(location) {
    trace("showEmptyBox(" + location + ")");
    var loc = LOCATIONS[location],
        rect = paper.rect(loc.left, loc.top, loc.width, loc.height);
    rect.attr(BOXATTR);
}

function showCompositeStimulus(shape, colour, number, location, correct) {
    /*
    shape: shape# within SHAPES
    colour: HTML colour within COLOURS
    number: number of stimuli
    location: box number (0-3)
    correct: Boolean
    */
    trace("showCompositeStimulus(" + shape + ", " + colour + ", " + number +
          ", " + location + ", " + correct + ")");
    var loc = LOCATIONS[location],
        rect = paper.rect(loc.left, loc.top, loc.width, loc.height),
        centres = stimCentres(number),
        i,
        scale = (0.8 * 0.95 * BOXHEIGHT / 2) / STIMSIZE,
        // without the 0.8, you can fit 4 but not 5 wide.
        stim,
        fn = function () { recordResponse(correct); };
    rect.attr(BOXATTR);
    setTouchStartEvent(rect, fn);
    for (i = 0; i < number; ++i) {
        // Scale up
        centres.x[i] *= BOXWIDTH;
        centres.y[i] *= BOXHEIGHT;
        // Reposition (from coordinates relative to box centre at 0,0)
        centres.x[i] += loc.xcentre;
        centres.y[i] += loc.ycentre;
        stim = showIndividualStimulus(shape, colour, centres.x[i],
                                      centres.y[i], scale);
        setTouchStartEvent(stim, fn);
    }
}

function startTrial(tr) {
    trace("startTrial()");
    var l,
        A;
    for (l = 0; l < LOCATIONS.length; ++l) {
        if (l === tr.correct_location) {
            showCompositeStimulus(
                tr.correct_shape,
                tr.correct_colour,
                tr.correct_number,
                tr.correct_location,
                true
            );
        } else if (l === tr.incorrect_location) {
            showCompositeStimulus(
                tr.incorrect_shape,
                tr.incorrect_colour,
                tr.incorrect_number,
                tr.incorrect_location,
                false
            );
        } else {
            showEmptyBox(l);
        }
    }
    if (tp.offer_abort) {
        A = createButton(paper, ABORT);
        setTouchStartEvent(A, function () { abort(); });
    }
    tr.trial_start_time = now();
}

//=============================================================================
// Task
//=============================================================================

function stagePassed() {
    // X of the last Y correct?
    var n_correct = 0,
        first = trials.length - tp.progress_criterion_y,
        i;
    for (i = currentTrial;
            i >= 0 && i >= first && trials[i].stageZeroBased === currentStage;
            --i) {
        if (trials[i].correct) {
            n_correct += 1;
        }
    }
    return (n_correct >= tp.progress_criterion_x);
}

function getNumTrialsThisStage() {
    var n = 0,
        i;
    for (i = currentTrial; i >= 0; --i) {
        if (trials[i].stageZeroBased !== currentStage) {
            return n;
        }
        n += 1;
    }
    return n;
}

function stageFailed() {
    // Too many trials in this stage?
    if (getNumTrialsThisStage() >= tp.max_trials_per_stage) {
        return true;
    }
    return false;
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

nextTrial = function () {
    trace("nextTrial()");
    assert(currentStage >= 0 && currentStage < stages.length,
           "Bug in nextTrial() re stages");
    var tr,
        st = stages[currentStage];
    paper.clear();
    if (currentTrial >= 0) {
        saveTrial(currentTrial);
        st.n_completed_trials += 1;
        saveStage(currentStage);
    }
    if (stagePassed()) {
        trace("passed stage");
        st.stage_passed = true;
        saveStage(currentStage);
        currentStage += 1;
    } else if (stageFailed()) {
        trace("failed stage");
        st.stage_failed = true;
        saveStage(currentStage);
        thanks();
        return;
    }
    // Finished last stage?
    if (currentStage >= stages.length || currentStage >= tp.last_stage) {
        trace("completed task");
        thanks();
        return;
    }

    currentTrial += 1;
    tr = new TrialRecord(currentTrial, currentStage);
    trials.push(tr);
    assert(currentTrial === trials.length - 1,
           "Bug in nextTrial() re trials");
    st = stages[currentStage];  // another one, now
    if (st.first_trial_num === null) {
        st.first_trial_num = tr.trial;  // 1-based
        saveStage(currentStage);
    }
    startTrial(trials[currentTrial]);
};

//=============================================================================
// Communication from the "outside world": see taskhtmlcommon.js
//=============================================================================
// Must receive task parameters (see above), and provide incomingEvent(),
// startTask()

function incomingEvent(e) {
    trace("incomingEvent: " + JSON.stringify(e));
}

function startTask() {
    trace("starttask: params = " + JSON.stringify(tp));
    if (tp.debug_display_stimuli_only) {
        debugDisplayStimuli();
        return;
    }
    saveShapes();
    stages = makeStages(tp.counterbalance_dimensions);
    saveAllStages();
    paper.clear();
    createText(paper, tp.INSTRUCTIONS, PROMPT_X, PROMPT_Y, PROMPT_ATTR);
    var B = createButton(paper, START);
    setTouchStartEvent(B, function () {
        nextTrial();
    });
}

/* NOT WORKING, though it works in a plain browser (see keypress.html)

function keypress(e) {
    // http://javascript.info/tutorial/keyboard-events
    // http://stackoverflow.com/questions/905222
    e = e || event;
    var keyCode = e.keyCode;
    trace("keypress: " + e.keyCode);
    switch (e.keyCode) {
    case 27:  // Escape
        abort();
        break;
    default:
        break;
    }
    return false;  // prevent it bubbling up
}
*/

registerWebviewTask(TASKNAME, EVENTNAME_IN, EVENTNAME_OUT,
                    startTask, incomingEvent);
