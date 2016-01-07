// QuestionMCQGridDouble.js
// Stem, then one-from-many for several questions.

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

var MODULE_NAME = "QuestionMCQGridDouble",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionMCQGridDouble(props) {

    var lang = require('lib/lang'),
        RadioGroupGridDouble = require(
            'questionnairelib/RadioGroupGridDouble'
        ),
        colWidth_1,
        colWidth_2;

    qcommon.requireProperty(props, "questions", MODULE_NAME);
    qcommon.requireProperty(props, "options_1", MODULE_NAME);
    qcommon.requireProperty(props, "fields_1", MODULE_NAME);
    qcommon.requireSameLength(props, "fields_1", "questions", MODULE_NAME);
    qcommon.requireProperty(props, "options_2", MODULE_NAME);
    qcommon.requireProperty(props, "fields_2", MODULE_NAME);
    qcommon.requireSameLength(props, "fields_2", "questions", MODULE_NAME);
    qcommon.setDefaultProperty(props, "mandatory", true);
    // ... way of specifying all fields
    qcommon.setDefaultProperty(
        props,
        "fieldsMandatory_1",
        qcommon.arrayOfIdenticalElements(
            props.mandatory,
            props.questions.length
        )
    );
    qcommon.requireSameLength(props, "fieldsMandatory_1", "questions",
                              MODULE_NAME);
    qcommon.setDefaultProperty(
        props,
        "fieldsMandatory_2",
        qcommon.arrayOfIdenticalElements(
            props.mandatory,
            props.questions.length
        )
    );
    qcommon.requireSameLength(props, "fieldsMandatory_2", "questions",
                              MODULE_NAME);
    qcommon.setDefaultProperty(props, "options1_WidthTogether", "33%");
    qcommon.setDefaultProperty(props, "options2_WidthTogether", "33%");
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "stem_1", "");
    qcommon.setDefaultProperty(props, "stem_2", "");
    // other properties:
    //      subtitles -- array of objects with properties:
    //          beforeIndex, subtitle (can be "")
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    colWidth_1 = lang.divideUnits(props.options1_WidthTogether,
                                  props.options_1.length);
    colWidth_2 = lang.divideUnits(props.options2_WidthTogether,
                                  props.options_2.length);

    this.fields_1 = props.fields_1;
    this.fields_2 = props.fields_2;
    this.grid = new RadioGroupGridDouble({
        readOnly: props.readOnly,
        tiprops: {
            left: props.left,
            right: props.right,
            top: props.top,
            bottom: props.bottom,
            center: props.center
        },
        questions: props.questions,
        subtitles: props.subtitles,
        options_1: props.options_1,
        options_2: props.options_2,
        mandatoryFlags_1: props.fieldsMandatory_1,
        mandatoryFlags_2: props.fieldsMandatory_2,
        colWidth_1: colWidth_1,
        colWidth_2: colWidth_2,
        setFieldValue_1: function (questionIndex, value) {
            props.questionnaire.setFieldValue(props.fields_1[questionIndex],
                                              value);
        },
        setFieldValue_2: function (questionIndex, value) {
            props.questionnaire.setFieldValue(props.fields_2[questionIndex],
                                              value);
        },
        stem_1: props.stem_1,
        stem_2: props.stem_2
    });
    this.tiview = this.grid.tiview;
}
lang.inheritPrototype(QuestionMCQGridDouble, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionMCQGridDouble, {

    isInputRequired: function () {
        return this.grid.isInputRequired();
    },

    setFromField: function () {
        var values_1 = [],
            values_2 = [],
            i;
        for (i = 0; i < this.fields_1.length; ++i) {
            values_1.push(this.questionnaire.getFieldValue(this.fields_1[i]));
            values_2.push(this.questionnaire.getFieldValue(this.fields_2[i]));
        }
        this.grid.setAllValues(values_1, values_2);
    },

    setMandatory: function (mandatory, fieldname) {
        // if fieldname undefined, applies to all
        var i;
        for (i = 0; i < this.fields_1.length; ++i) {
            if (fieldname === undefined || this.fields_1[i] === fieldname) {
                this.grid.setMandatory_1(mandatory, i);
            }
            if (fieldname === undefined || this.fields_2[i] === fieldname) {
                this.grid.setMandatory_2(mandatory, i);
            }
        }
    },

    cleanup: function () {
        this.grid.cleanup();
        this.grid = null;
    }

});
module.exports = QuestionMCQGridDouble;
