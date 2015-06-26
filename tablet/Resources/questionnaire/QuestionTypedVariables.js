// QuestionTypedVariables.js

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

/*

    PROBLEM: keyboard entry (e.g. with Bluetooth keyboard) on iPad is slow,
    proportional to number of elements/text boxes.
    HOWEVER, no effect of disabling all event listeners, suggesting that
    it's down to the Titanium rendering system or something.

    - But removing the textHolder/textView pair made it very slow to scroll.
    - Not very substantially affected by disabling autocorrect (but disabling
      it does make it less annoying).
    - Android: perfectly fast enough.
    - No discernable lag at all in iOS simulator.
    - Turns out it's due to the "height: Titanium.UI.SIZE" element for
      multiline fields, i.e. presumably constant recalculation over multiple
      views whenever a key is pressed.
      So: storedvars.multilineTextFixedHeight -- now fine.

*/

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var MODULE_NAME = "QuestionTypedVariables",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang'),
    MAX_SAFE_BIGINT = Math.pow(2, 53) - 1,
    // ... Number.MAX_SAFE_BIGINT isn't supported yet within Titanium
    MAX_SAFE_INT = Math.pow(2, 31) - 1; // ... probably
    // ... what Titanium can cope with from SQLite integer fields;
    //     https://jira.appcelerator.org/browse/TIMOB-3050

//=============================================================================
// BUG FIX FOR TextArea in Titanium 3.2.0GA
//=============================================================================
/*
function getTextAreaCreator() {
    var platform = require('lib/platform');
    if (platform.android) {
        return require('org.camcops.androidtibugfix').createTextArea; // module
    }
    else {
        return Titanium.UI.createTextArea;
    }
}
*/
//=============================================================================


function getStringVersionOfNumber(v) {
    if (isNaN(v) || v === null) { // ... isNaN(null) is false
        return "";
    }
    return v.toString();
    // works for int and float
    // ... will survive conversion to/from exponential notation
}

function makeChangedFunction(object, varnum, fnChanged) {
    // Beware the Javascript Callback Loop Bug
    // (a) http://stackoverflow.com/questions/3023874/
    // (b) timings...
    return function (e) {
        var UICONSTANTS = require('common/UICONSTANTS');
        if (object.timeouts[varnum] !== null) {
            clearTimeout(object.timeouts[varnum]);
        }
        object.timeouts[varnum] = setTimeout(
            function () {
                object.timeouts[varnum] = null;
                fnChanged.call(object, e);
            },
            UICONSTANTS.KEYBOARD_VALIDATION_DELAY_MS
        );
    };
}

function makeFocusLostFunction(object, fnFocusLost) {
    return function (e) {
        fnFocusLost.call(object, e);
    };
}

function QuestionTypedVariables(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        i,
        platform = require('lib/platform'),
        storedvars = require('table/storedvars'),
        multilineTextFixedHeight = storedvars.multilineTextFixedHeight.getValue(),
        questionnaireTextSizePercent = storedvars.questionnaireTextSizePercent.getValue(),
        changedFunction,
        focusLostFunction,
        creatorFunction,
        suppressReturn,
        editHeight,
        textHolder,
        textView,
        editView,
        rowview,
        fnChanged,
        fnFocus;
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "useColumns", true);
    qcommon.setDefaultProperty(props, "colWidthPrompt", "50%");
    qcommon.setDefaultProperty(props, "mandatory", true);
    // ... applies to fields without individual specification
    qcommon.setDefaultProperty(props, "boldPrompt", false);
    qcommon.requireProperty(props, "variables", MODULE_NAME);
    // ... array of objects with properties:
    for (i = 0; i < props.variables.length; ++i) {
        qcommon.requireProperty(props.variables[i], "field", MODULE_NAME);
        qcommon.requireProperty(props.variables[i], "type", MODULE_NAME);
        qcommon.setDefaultProperty(props.variables[i], "hint",
                                   props.variables[i].prompt);
        qcommon.setDefaultProperty(props.variables[i], "mandatory",
                                   props.mandatory);
        qcommon.setDefaultProperty(props.variables[i], "autocapitalization",
                                   Titanium.UI.TEXT_AUTOCAPITALIZATION_NONE);
        qcommon.setDefaultProperty(props.variables[i], "trim", false);
        // ... for text
        qcommon.setDefaultProperty(props.variables[i], "passwordMask", false);
        qcommon.setDefaultProperty(props.variables[i], "maxLength", -1);
        // ... primarily for strings; -1 means unlimited
        qcommon.setDefaultProperty(
            props.variables[i],
            "nDisplayLines",
            storedvars.multilineDefaultNLines.getValue()
        );
        // ... for multiline text: when multilineTextFixedHeight is TRUE, how many lines to display?
        // optional property: prompt
        // optional property: min (for numbers)
        // optional property: max (for numbers)
        // optional property: keyboardType
    }
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.rows = [];
    this.variables = props.variables;
    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width : Titanium.UI.FILL,
        height : Titanium.UI.SIZE,
        layout : 'vertical',
    });
    this.timeouts = [];
    this.changeListeners = [];
    this.focusListeners = [];
    this.dead = false;

    for (i = 0; i < props.variables.length; ++i) {
        suppressReturn = true; // only set to false (= allow newlines in text) for the multiline field
        editHeight = Titanium.UI.SIZE;
        this.timeouts.push(null);
        switch (props.variables[i].type) {
        case UICONSTANTS.TYPEDVAR_INTEGER:
            if (props.variables[i].keyboardType === undefined) {
                props.variables[i].keyboardType = (platform.android ?
                        Titanium.UI.KEYBOARD_DEFAULT :
                        Titanium.UI.KEYBOARD_NUMBERS_PUNCTUATION
                );
                // numeric keyboard not working on Android (doesn't allow
                // "." entry)
            }
            changedFunction = this.valueChangedInt;
            focusLostFunction = this.focusLostInt;
            creatorFunction = Titanium.UI.createTextField;
            break;
        case UICONSTANTS.TYPEDVAR_BIGINT:
            if (props.variables[i].keyboardType === undefined) {
                props.variables[i].keyboardType = (platform.android ?
                        Titanium.UI.KEYBOARD_DEFAULT :
                        Titanium.UI.KEYBOARD_NUMBERS_PUNCTUATION
                );
                // numeric keyboard not working on Android (doesn't allow
                // "." entry)
            }
            changedFunction = this.valueChangedBigInt; // NB different here
            focusLostFunction = this.focusLostBigInt; // NB different here
            creatorFunction = Titanium.UI.createTextField;
            break;
        case UICONSTANTS.TYPEDVAR_REAL:
            if (props.variables[i].keyboardType === undefined) {
                props.variables[i].keyboardType = (platform.android ?
                        Titanium.UI.KEYBOARD_DEFAULT :
                        Titanium.UI.KEYBOARD_NUMBERS_PUNCTUATION
                );
                // numeric keyboard not working on Android (doesn't allow
                // "." entry)
            }
            changedFunction = this.valueChangedFloat;
            focusLostFunction = this.focusLostFloat;
            creatorFunction = Titanium.UI.createTextField;
            break;
        case UICONSTANTS.TYPEDVAR_TEXT:
            if (props.variables[i].keyboardType === undefined) {
                props.variables[i].keyboardType = Titanium.UI.KEYBOARD_DEFAULT;
            }
            changedFunction = this.valueChangedString;
            focusLostFunction = this.focusLostString;
            creatorFunction = Titanium.UI.createTextField;
            break;
        case UICONSTANTS.TYPEDVAR_TEXT_MULTILINE:
            if (props.variables[i].keyboardType === undefined) {
                props.variables[i].keyboardType = Titanium.UI.KEYBOARD_DEFAULT;
            }
            changedFunction = this.valueChangedString;
            focusLostFunction = this.focusLostString;
            creatorFunction = Titanium.UI.createTextArea;
            // ... getTextAreaCreator();
            suppressReturn = false;
            if (multilineTextFixedHeight && !props.readOnly) {
                editHeight = Math.round(
                    props.variables[i].nDisplayLines *
                        UICONSTANTS.QUESTIONNAIRE_BASE_FONT_SIZE *
                        1.4 * // line height > font height
                        questionnaireTextSizePercent /
                        100
                ).toString() + 'sp';
            }
            break;
        default:
            throw new Error("Invalid type to QuestionTypedVariables");
        }
        if (props.variables[i].prompt) {
            textHolder = Titanium.UI.createView({
                top: 0,
                height: Titanium.UI.SIZE,
                left: 0,
                right: (props.useColumns ?
                        lang.subtractUnits("100%", props.colWidthPrompt) :
                        0
                ), // Titanium calculates this from right to left, it seems (2014-01-17)
                touchEnabled: false,
                // backgroundColor: UICONSTANTS.GARISH_DEBUG_COLOUR_1,
            });
            textView = Titanium.UI.createLabel({
                top: 0,
                height: Titanium.UI.SIZE,
                left: 0,
                right: props.useColumns ? UICONSTANTS.SPACE : 0,
                font: UICONSTANTS.getQuestionnaireFont(false, props.boldPrompt,
                                                       false),
                text: props.variables[i].prompt,
                textAlign: (props.useColumns ?
                        Titanium.UI.TEXT_ALIGNMENT_RIGHT :
                        Titanium.UI.TEXT_ALIGNMENT_LEFT
                ),
                color: UICONSTANTS.QUESTION_COLOUR,
                // backgroundColor: UICONSTANTS.GARISH_DEBUG_COLOUR_2,
                touchEnabled: false,
            });
            textHolder.add(textView);
        }
        editView = creatorFunction({
            left: props.useColumns ? props.colWidthPrompt : 0,
            right: 0,
            top: 0,
            height: editHeight,

            autocapitalization: Titanium.UI.TEXT_AUTOCAPITALIZATION_NONE,
            autocorrect: false,
            // ... turn off spellchecking; will this improve speed?
            backgroundColor: (props.variables[i].mandatory ?
                    UICONSTANTS.ANSWER_BACKGROUND_COLOUR_REQUIRED :
                    (props.readOnly ?
                            UICONSTANTS.ANSWER_BACKGROUND_COLOUR_READONLY :
                            UICONSTANTS.ANSWER_BACKGROUND_COLOUR
                    )
            ),
            color: UICONSTANTS.ANSWER_COLOUR,
            editable: !props.readOnly,
            ellipsize: true, // Android only
            font: UICONSTANTS.getQuestionnaireFont(false, true, false), // bold
            hintText: props.variables[i].hint,
            // ... not a feature of iOS Titanium.UI.textArea
            keyboardType: props.variables[i].keyboardType,
            maxLength: props.variables[i].maxLength,
            passwordMask: props.variables[i].passwordMask,
            suppressReturn: suppressReturn,
            value: null, // Will be overwritten later
            verticalAlign: Titanium.UI.TEXT_VERTICAL_ALIGNMENT_TOP,

            variableId: i,
        });
        if (!props.readOnly) {
            fnChanged = makeChangedFunction(this, i, changedFunction);
            this.changeListeners.push(fnChanged);
            editView.addEventListener('change', fnChanged);
            fnFocus = makeFocusLostFunction(this, focusLostFunction);
            this.focusListeners.push(fnFocus);
            editView.addEventListener('blur', fnFocus);
            // http://developer.appcelerator.com/question/119550/textfield-change-event-is-crazy-wrong
        }
        this.rows.push(editView);
        if (props.useColumns) {
            rowview = Titanium.UI.createView({
                width : Titanium.UI.FILL,
                height : Titanium.UI.SIZE,
                top: (i > 0 ? UICONSTANTS.SPACE : 0),
            });
            if (props.variables[i].prompt) {
                rowview.add(textHolder);
            }
            rowview.add(editView);
            this.tiview.add(rowview);
        } else {
            if (props.variables[i].prompt) {
                this.tiview.add(textHolder);
            }
            this.tiview.add(editView);
        }
    }
}
lang.inheritPrototype(QuestionTypedVariables, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionTypedVariables, {

    // VALIDATION AND RETURNING VALUE TO FIELD
    valueChanged: function (e, value) {
        // properties: source, type
        var index = e.source.variableId,
            field = this.variables[index].field;
        this.questionnaire.setFieldValue(field, value);
        // If you're thinking "why update the field after every keystroke?",
        // it's so that things like the availability of the "Next" button
        // work properly. The "corrected" value is only written
        // back to the visible edit box when focus is lost (see below).
        if (this.dead) {
            return;
        }
        this.setMandatoryAppearance(index);
    },

    getValidatedInt: function (e, bigint) {
        // var v = parseInt(e.source.value.replace(/[^\d]/g, ""));
        // ... limit to digits
        if (bigint === undefined) {
            bigint = false;
        }
        var v = parseInt(parseFloat(e.source.value), 10),
            // ... parseFloat copes with e.g. "5e+3", which parseInt rejects
            // ... then some floats can be integers, e.g 5e+3 becomes 5000,
            //     while others can't, e.g. 5e+25 (string) becomes 5e+25
            //     (float) becomes 5 (int)
            // ... but probably the best we can do.
            index = e.source.variableId,
            maxint = bigint ? MAX_SAFE_BIGINT : MAX_SAFE_INT;
        if (isNaN(v) || v === null) {
            return null;
        }
        if (this.variables[index].max !== undefined) {
            v = Math.min(v, this.variables[index].max);
        } else {
            v = Math.min(v, maxint);
        }
        if (this.variables[index].min !== undefined) {
            v = Math.max(v, this.variables[index].min);
        } else {
            v = Math.max(v, -maxint);
        }
        return v;
    },

    getValidatedFloat: function (e) {
        var v = parseFloat(e.source.value),
            index = e.source.variableId;
        if (isNaN(v) || v === null) {
            return null;
        }
        if (this.variables[index].max !== undefined) {
            v = Math.min(v, this.variables[index].max);
        }
        if (this.variables[index].min !== undefined) {
            v = Math.max(v, this.variables[index].min);
        }
        return v;
    },

    getValidatedString: function (e) {
        var v = e.source.value, // consider also e.value
            index = e.source.variableId;
        if (v && this.variables[index].trim) {
            v = v.trim();
        }
        if (v && this.variables[index].maxLength > 0 &&
                v.length > this.variables[index].maxLength) {
            v = v.substring(0, this.variables[index].maxLength);
        }
        if (v && this.variables[index].autocapitalization ===
                Titanium.UI.TEXT_AUTOCAPITALIZATION_ALL) {
            v = v.toUpperCase();
        }
        if (v === "") {
            v = null;
            // More helpful to have NULLs than empty strings!
        }
        return v;
    },

    valueChangedInt: function (e) {
        var v = this.getValidatedInt(e, false);
        this.valueChanged(e, v);
    },

    valueChangedBigInt: function (e) {
        var v = this.getValidatedInt(e, true);
        this.valueChanged(e, v);
    },

    valueChangedFloat: function (e) {
        var v = this.getValidatedFloat(e);
        this.valueChanged(e, v);
    },

    valueChangedString: function (e) {
        var v = this.getValidatedString(e);
        this.valueChanged(e, v);
    },

    focusLostInt: function (e) {
        var v = this.getValidatedInt(e, false);
        e.source.value = getStringVersionOfNumber(v);
    },

    focusLostBigInt: function (e) {
        var v = this.getValidatedInt(e, true);
        e.source.value = getStringVersionOfNumber(v);
    },

    focusLostFloat: function (e) {
        var v = this.getValidatedFloat(e);
        e.source.value = getStringVersionOfNumber(v);
    },

    focusLostString: function (e) {
        var v = this.getValidatedString(e);
        e.source.value = v;
    },

    setMandatoryAppearance: function (variableId) {
        var UICONSTANTS = require('common/UICONSTANTS'),
            mandatory = this.variables[variableId].mandatory,
            blank = this.isBlank(variableId);
        this.rows[variableId].setBackgroundColor(
            mandatory && blank ?
                    UICONSTANTS.ANSWER_BACKGROUND_COLOUR_REQUIRED :
                    (this.readOnly ?
                            UICONSTANTS.ANSWER_BACKGROUND_COLOUR_READONLY :
                            UICONSTANTS.ANSWER_BACKGROUND_COLOUR
                    )
        );
    },

    setMandatory: function (mandatory, fieldname) {
        // if fieldname undefined, applies to all
        var i;
        for (i = 0; i < this.variables.length; ++i) {
            if (fieldname === undefined ||
                    this.variables[i].field === fieldname) {
                this.variables[i].mandatory = mandatory;
                this.setMandatoryAppearance(i, this.rows[i].value !== null);
            }
        }
    },

    isInputRequired: function () {
        var requiresInput = false,
            i;
        for (i = 0; i < this.rows.length; ++i) {
            requiresInput = requiresInput || (this.isBlank(i) &&
                                              this.variables[i].mandatory);
        }
        return requiresInput;
    },

    isBlank: function (variableId) {
        if (variableId < 0 || variableId > this.variables.length) {
            return false;
        }
        return (this.rows[variableId].value === null ||
                this.rows[variableId].value === "");
    },

    setFromField: function () {
        var UICONSTANTS = require('common/UICONSTANTS'),
            i,
            v;
        for (i = 0; i < this.variables.length; ++i) {
            v = this.questionnaire.getFieldValue(this.variables[i].field);
            switch (this.variables[i].type) {
            case UICONSTANTS.TYPEDVAR_INTEGER:
            case UICONSTANTS.TYPEDVAR_BIGINT:
            case UICONSTANTS.TYPEDVAR_REAL:
                this.rows[i].setValue(getStringVersionOfNumber(v));
                break;
            case UICONSTANTS.TYPEDVAR_TEXT:
            case UICONSTANTS.TYPEDVAR_TEXT_MULTILINE:
                this.rows[i].setValue(v);
                break;
            default:
                throw new Error("Invalid type to QuestionTypedVariables");
            }
            this.setMandatoryAppearance(i);
        }
    },

    cleanup: function () {
        var i;
        this.dead = true; // in case there's an extant timer calling a
        // "changed" function, which will call valueChanged
        for (i = 0; i < this.rows.length; ++i) {
            if (!this.readOnly) {
                this.rows[i].removeEventListener('change',
                                                 this.changeListeners[i]);
                this.changeListeners[i] = null;
                this.rows[i].removeEventListener('blur',
                                                 this.focusListeners[i]);
                this.focusListeners[i] = null;
            }
            this.rows[i] = null;
        }
    },

});
module.exports = QuestionTypedVariables;
