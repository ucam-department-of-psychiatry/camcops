// QuestionSlider.js

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

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var MODULE_NAME = "QuestionSlider",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function convertToStep(value, step) {
    value /= step;
    value = Math.round(value);
    value *= step;
    return value;
}

function QuestionSlider(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        self = this,
        maincontainer,
        textcontainer,
        i,
        labelprops,
        label;
    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.setDefaultProperty(props, "showCurrentValueNumerically", false);
    qcommon.setDefaultProperty(props, "big", false);
    qcommon.setDefaultProperty(props, "bold", false);
    qcommon.setDefaultProperty(props, "italic", false);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    // optional property: min
    // optional property: max
    // optional property: step
    // optional property: labels
    // ... array of objects like { text: XXX, left: XXX OR center: XXX OR
    //     right: XXX }
    // optional property: numberFormatDecimalPlaces
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.numberFormatDecimalPlaces = props.numberFormatDecimalPlaces;
    this.showCurrentValueNumerically = props.showCurrentValueNumerically;
    this.step = props.step;
    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE
    });
    this.indicator = new qcommon.ValidityIndicator({
        size: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE
    });
    this.tiview.add(this.indicator.tiview);
    maincontainer = Titanium.UI.createView({
        left: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE,
        top: 0,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        layout: 'vertical'
    });
    this.tiview.add(maincontainer);

    // Current value
    if (props.showCurrentValueNumerically) {
        this.numberLabel = Titanium.UI.createLabel({
            top: 0,
            center: {x: "50%"},
            font: UICONSTANTS.getQuestionnaireFont(props.big, props.bold,
                                                   props.italic),
            color: UICONSTANTS.QUESTION_COLOUR,
            touchEnabled: false
        });
        maincontainer.add(this.numberLabel);
    }

    // Slider
    this.slider = Titanium.UI.createSlider({
        top: 0,
        left: 0,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        enabled: !props.readOnly,
        min: props.min,
        max: props.max,
        minRange: props.min,
        maxRange: props.max
    });
    maincontainer.add(this.slider);

    // Text, if required
    if (props.labels) {
        textcontainer = Titanium.UI.createView({
            top: 0,
            left: 0,
            width: Titanium.UI.FILL,
            height: Titanium.UI.SIZE
        });
        maincontainer.add(textcontainer);
        for (i = 0; i < props.labels.length; ++i) {
            labelprops = {
                top: 0,
                font: (props.big ?
                        (props.bold ?
                                UICONSTANTS.getQuestionnaireFontBigBold() :
                                UICONSTANTS.getQuestionnaireFontBig()) :
                        (props.bold ?
                                UICONSTANTS.getQuestionnaireFontBold() :
                                UICONSTANTS.getQuestionnaireFont())
                ),
                color: UICONSTANTS.QUESTION_COLOUR,
                touchEnabled: false,
                text: props.labels[i].text
            };
            if (props.labels[i].left !== undefined) {
                labelprops.left = props.labels[i].left;
                labelprops.textAlign = Titanium.UI.TEXT_ALIGNMENT_LEFT;
            } else if (props.labels[i].center !== undefined) {
                labelprops.center = {x: props.labels[i].center};
                labelprops.textAlign = Titanium.UI.TEXT_ALIGNMENT_CENTER;
            } else if (props.labels[i].right !== undefined) {
                labelprops.right = props.labels[i].right;
                labelprops.textAlign = Titanium.UI.TEXT_ALIGNMENT_RIGHT;
            }
            label = Titanium.UI.createLabel(labelprops);
            textcontainer.add(label);
        }
    }

    /* Bug setting slider value?
        http://developer.appcelerator.com/question/143516/slider-value-set-problem
        http://developer.appcelerator.com/question/141082/value-of-slider-in-android-is-ignored
        http://jira.appcelerator.org/browse/TIMOB-10880
        Workaround:
    */
    this.setValueOnlyAfterVisible = true;

    // To field
    if (!props.readOnly) {
        // touchend works better than change for writing to the database
        // (not least because creating the slider, and writing to its value,
        // generate [multiple!] change events.
        this.touchendListener = function (e) { self.respondToChange(e); };
        this.slider.addEventListener('touchend', this.touchendListener);
        this.singletapListener = function (e) { self.respondToChange(e); };
        this.slider.addEventListener('singletap', this.singletapListener);
    }

}
lang.inheritPrototype(QuestionSlider, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionSlider, {

    isInputRequired: function () {
        return (this.mandatory &&
                (this.questionnaire.getFieldValue(this.field) === null));
    },

    setMandatory: function (mandatory) {
        this.mandatory = mandatory;
        this.applyMandatory();
    },

    applyMandatory: function () {
        if (this.isInputRequired()) {
            this.indicator.setRequired();
        } else if (this.questionnaire.getFieldValue(this.field) === null) {
            this.indicator.setNullButOptional();
        } else {
            this.indicator.clear();
        }
    },

    setLabelValue: function (value) {
        var processedval = "?";
        if (value !== null && !isNaN(value)) {
            if (this.numberFormatDecimalPlaces !== undefined) {
                processedval = value.toFixed(this.numberFormatDecimalPlaces);
            } else {
                processedval = value;
            }
        }
        if (this.showCurrentValueNumerically) {
            this.numberLabel.setText(processedval);
        }
    },

    setSliderValue: function (value) {
        if (isNaN(value)) {
            value = null;
        }
        if (value !== null) {
            // Setting it to null makes it move to the far right; looks worse
            this.slider.setValue(value);
        }
        this.setLabelValue(value);
    },

    respondToChange: function () {
        var value = parseFloat(this.slider.value);
        if (isNaN(value)) {
            value = null;
        }
        if (value !== null && this.step !== undefined) {
            value = convertToStep(value, this.step);
            this.slider.setValue(value);
        }
        this.setLabelValue(value);
        this.questionnaire.setFieldValue(this.field, value);
        this.applyMandatory();
    },

    // From field
    setFromField: function () {
        if (this.field === undefined) {
            return;
        }
        var value = this.questionnaire.getFieldValue(this.field);
        this.setSliderValue(value);
        this.applyMandatory();
    },

    cleanup: function () {
        if (this.touchendListener) {
            this.slider.removeEventListener('touchend', this.touchendListener);
            this.touchendListener = null;
        }
        if (this.singletapListener) {
            this.slider.removeEventListener('singletap',
                                            this.singletapListener);
            this.singletapListener = null;
        }
        this.slider = null;
        this.numberLabel = null;
        this.indicator.cleanup();
    }

});
module.exports = QuestionSlider;
