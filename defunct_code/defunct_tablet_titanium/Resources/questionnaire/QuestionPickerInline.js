// QuestionPickerInline.js

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

var MODULE_NAME = "QuestionMCQ",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionPickerInline(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        viewprops,
        column,
        i,
        rowprops,
        pickerprops,
        platform,
        self = this;
    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.setDefaultProperty(props, "randomize", false);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    if (props.randomize) {
        lang.shuffle(props.options);
    }
    this.props = props;

    this.selectedIndex = null;

    viewprops = {
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE
    };
    this.tiview = Titanium.UI.createView(viewprops);

    this.indicator = new qcommon.ValidityIndicator({
        size: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE
    });
    this.tiview.add(this.indicator.tiview);

    // Android problems:
    // 1. useSpinner: spinner looks nice but doesn't respond to touches.
    //      -- Possibly this:
    //      http://developer.appcelerator.com/question/119756/android-spinner-in-the-table-view-row-doesnt-work
    //      -- so try setting height of parent view -- no, no effect, still
    //         unresponsive
    // 2. Without useSpinner, it's white-on-white (in resting state) and fine
    //    (with its own popup colours) when popped up.
    //      -- createPicker() no color property, no backgroundColor property
    //      -- createPickerRow() color property ignored
    // ... so: additional intermediate view

    if (props.readOnly) {
        this.value_as_text = Titanium.UI.createLabel({
            top: 0,
            left: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            font: UICONSTANTS.getQuestionnaireFont(false, true, false), // bold
            color: UICONSTANTS.READONLY_ANSWER_COLOUR,
            text: ""  // will be set later
        });
        this.tiview.add(this.value_as_text);
    } else {
        column = Titanium.UI.createPickerColumn(); // we use this method
        // so we can pass all the data at picker creation
        for (i = 0; i < this.props.options.length; ++i) {
            rowprops = { title: this.props.options[i].key };
            column.addRow(Titanium.UI.createPickerRow(rowprops));
        }
        pickerprops = {
            top: 0,
            left: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            type: Titanium.UI.PICKER_TYPE_PLAIN,
            selectionIndicator: true,
            // DOESN'T WORK (UNRESPONSIVE TO TOUCHES): // useSpinner: true,
            // ... for an inline picker on Android, to match the iOS interface
            columns: [column]
        };

        platform = require('lib/platform');
        if (platform.android) {
            pickerprops.left = 0;
            this.picker = Titanium.UI.createPicker(pickerprops);
            this.intermediateview = Titanium.UI.createView({
                top: 0,
                left: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE,
                width: Titanium.UI.SIZE,
                height: Titanium.UI.SIZE,
                backgroundColor: UICONSTANTS.ANDROID_WIDGET_BACKGROUND_COLOUR
            });
            this.intermediateview.add(this.picker);
            this.tiview.add(this.intermediateview);
        } else {
            this.picker = Titanium.UI.createPicker(pickerprops);
            this.tiview.add(this.picker);
        }

        this.changeListener = function (e) { self.pickerValueChanged(e); };
        this.picker.addEventListener('change', this.changeListener);
    }
}
lang.inheritPrototype(QuestionPickerInline, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionPickerInline, {

    getValueAsText: function () {
        if (this.selectedIndex === null) {
            return "";
        }
        return this.props.options[this.selectedIndex].key;
    },

    isInputRequired: function () {
        return this.props.mandatory && this.selectedIndex === null;
    },

    pickerValueChanged: function (e) {
        this.selectedIndex = e.rowIndex;
        if (this.selectedIndex < 0 ||
                this.selectedIndex >= this.props.options.length) {
            this.selectedIndex = null;
        } else {
            var value = this.props.options[this.selectedIndex].value;
            this.questionnaire.setFieldValue(this.field, value);
        }
        this.applyMandatory();
    },

    setFromField: function () {
        var value = this.questionnaire.getFieldValue(this.field);
        this.selectedIndex = lang.kvpGetIndexByValue(this.props.options,
                                                     value);
        if (this.props.readOnly) {
            this.value_as_text.setText(this.getValueAsText());
        } else {
            this.picker.setSelectedRow(0, this.selectedIndex, false);
            // ... column, row, animated
        }
        this.applyMandatory();
    },

    setMandatory: function () { // any parameters ignored
        this.applyMandatory();
    },

    applyMandatory: function () {
        if (this.isInputRequired()) {
            this.indicator.setRequired();
        } else if (this.selectedIndex === null) {
            this.indicator.setNullButOptional();
        } else {
            this.indicator.clear();
        }
    },

    cleanup: function () {
        if (this.props.readOnly) {
            this.value_as_text = null;
        } else {
            if (this.changeListener) {
                this.picker.removeEventListener("change", this.changeListener);
                this.changeListener = null;
            }
            this.indicator.cleanup();
            this.indicator = null;
            this.picker = null;
            this.intermediateview = null;
        }
    }

});
module.exports = QuestionPickerInline;
