// QuestionMCQGrid.js
// Stem, then one-from-many for several questions.

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

/*jslint node: true, plusplus: true */
"use strict";
/*global Titanium */

var MODULE_NAME = "QuestionMCQGrid",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionMCQGrid(props) {

    var lang = require('lib/lang'),
        RadioGroupGrid = require('questionnairelib/RadioGroupGrid'),
        colWidth;

    qcommon.requireProperty(props, "fields", MODULE_NAME);
    qcommon.requireProperty(props, "questions", MODULE_NAME);
    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.requireSameLength(props, "fields", "questions", MODULE_NAME);
    qcommon.setDefaultProperty(props, "optionsWidthTogether", "50%");
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    // ... way of specifying all fields
    qcommon.setDefaultProperty(
        props,
        "fieldsMandatory",
        qcommon.arrayOfIdenticalElements(props.mandatory, props.fields.length)
    );
    // ... way of specifying individual fields
    qcommon.requireSameLength(props, "fields", "fieldsMandatory", MODULE_NAME);
    qcommon.setDefaultProperty(props, "subtitles", []);
    // ... or: array of objects with properties:
    //          beforeIndex, subtitle (can be "")
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    colWidth = lang.divideUnits(props.optionsWidthTogether,
                                props.options.length);

    this.fields = props.fields;
    this.grid = new RadioGroupGrid({
        readOnly: props.readOnly,
        mandatoryFlags: props.fieldsMandatory,
        tiprops: {
            left: props.left,
            right: props.right,
            top: props.top,
            bottom: props.bottom,
            center: props.center,
        },
        questions: props.questions,
        subtitles: props.subtitles,
        options: props.options,
        colWidth: colWidth,
        setFieldValue: function (questionIndex, value) {
            Titanium.API.trace(
                "QuestionMCQGrid setFieldValue: questionIndex=" +
                    questionIndex + ", value=" + value
            );
            props.questionnaire.setFieldValue(props.fields[questionIndex],
                                              value);
        }
    });
    this.tiview = this.grid.tiview;
}
lang.inheritPrototype(QuestionMCQGrid, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionMCQGrid, {

    isInputRequired: function () {
        return this.grid.isInputRequired();
    },

    setFromField: function () {
        var values = [],
            i;
        for (i = 0; i < this.fields.length; ++i) {
            values.push(this.questionnaire.getFieldValue(this.fields[i]));
        }
        this.grid.setAllValues(values);
    },

    setMandatory: function (mandatory, fieldname) {
        // if fieldname undefined, applies to all
        var i;
        for (i = 0; i < this.fields.length; ++i) {
            if (fieldname === undefined || this.fields[i] === fieldname) {
                this.grid.setMandatory(mandatory, i);
            }
        }
    },

    cleanup: function () {
        this.grid.cleanup();
        this.grid = null;
    },

});
module.exports = QuestionMCQGrid;
