// QuestionMCQGridWithSingleBoolean.js
// Stem, then one-from-many for several questions, plus a boolean for each.
// See "DIFFERENT" for comparison to usual QuestionMCQGrid

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

var MODULE_NAME = "QuestionMCQGridWithSingleBoolean",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionMCQGridWithSingleBoolean(props) {

    var RadioGroupGridWithSingleBoolean = require(
            'questionnairelib/RadioGroupGridWithSingleBoolean'
        );

    qcommon.requireProperty(props, "questions", MODULE_NAME);
    qcommon.requireProperty(props, "mcqFields", MODULE_NAME);
    qcommon.requireProperty(props, "booleanFields", MODULE_NAME);
    qcommon.requireSameLength(props, "questions", "mcqFields", MODULE_NAME);
    qcommon.requireSameLength(props, "questions", "booleanFields",
                              MODULE_NAME);
    qcommon.requireProperty(props, "booleanLabel", MODULE_NAME);
    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.setDefaultProperty(props, "radioColWidth",
                               lang.divideUnits("50%",
                                                props.options.length + 1));
    qcommon.setDefaultProperty(props, "boolColWidth",
                               lang.divideUnits("50%",
                                                props.options.length + 1));
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    // ... way of specifying all fields
    qcommon.setDefaultProperty(
        props,
        "mcqFieldsMandatory",
        qcommon.arrayOfIdenticalElements(
            props.mandatory,
            props.questions.length
        )
    );
    qcommon.setDefaultProperty(
        props,
        "booleanFieldsMandatory",
        qcommon.arrayOfIdenticalElements(
            props.mandatory,
            props.questions.length
        )
    );
    qcommon.setDefaultProperty(props, "booleanBistate", true);
    // other properties:
    //      subtitles -- array of objects with properties:
    //          beforeIndex, subtitle (can be "")
    if (props.booleanBistate) {
        props.booleanFieldsMandatory = qcommon.arrayOfIdenticalElements(
            false,
            props.questions.length
        );
    }
    // ... can't sensibly be mandatory and bistate!
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.mcqFields = props.mcqFields;
    this.booleanFields = props.booleanFields;
    this.booleanBistate = props.booleanBistate;
    this.grid = new RadioGroupGridWithSingleBoolean({
        readOnly: props.readOnly,
        tiprops: {
            left: props.left,
            right: props.right,
            top: props.top,
            bottom: props.bottom,
            center: props.center,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL
        },
        questions: props.questions,
        subtitles: props.subtitles,
        options: props.options,
        booleanLabel: props.booleanLabel,
        radioColWidth: props.radioColWidth,
        boolColWidth: props.boolColWidth,
        mcqFields: props.mcqFields,
        booleanFields: props.booleanFields,
        mcqFieldsMandatory: props.mcqFieldsMandatory,
        booleanFieldsMandatory: props.booleanFieldsMandatory,
        booleanBistate: props.booleanBistate,
        setFieldValue: function (field, value) {
            // you can't do setFieldValue: props.questionnaire.setFieldValue !
            // That will fail to set the "this" object correctly, as
            // setFieldValue is part of the prototype of props.questionnaire.
            props.questionnaire.setFieldValue(field, value);
        }
    });
    this.tiview = this.grid.tiview;
}
lang.inheritPrototype(QuestionMCQGridWithSingleBoolean,
                      qcommon.QuestionElementBase);
lang.extendPrototype(QuestionMCQGridWithSingleBoolean, {

    isInputRequired: function () {
        return this.grid.isInputRequired();
    },

    setFromField: function () {
        var field,
            i;
        for (i = 0; i < this.mcqFields.length; ++i) {
            field = this.mcqFields[i];
            this.grid.setFieldToValue(field,
                                      this.questionnaire.getFieldValue(field));
            field = this.booleanFields[i];
            this.grid.setFieldToValue(field,
                                      this.questionnaire.getFieldValue(field));
        }
    },

    setMandatory: function (mandatory, fieldname) {
        // if fieldname undefined, applies to all
        // unless booleanBistate, when mandatory should not be true
        var i;
        for (i = 0; i < this.mcqFields.length; ++i) {
            if (fieldname === undefined || this.mcqFields[i] === fieldname) {
                this.grid.setMcqMandatory(mandatory, i);
            }
            if (
                (fieldname === undefined ||
                    this.booleanFields[i] === fieldname) &&
                    !(this.booleanBistate && mandatory)
            ) {
                this.grid.setBooleanMandatory(mandatory, i);
            }
        }
    },

    cleanup: function () {
        this.grid.cleanup();
        this.grid = null;
    }

});
module.exports = QuestionMCQGridWithSingleBoolean;
