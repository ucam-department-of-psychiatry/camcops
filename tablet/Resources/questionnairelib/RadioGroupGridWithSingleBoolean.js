// RadioGroupGridWithSingleBoolean.js

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

function RadioGroupGridWSBTitleRow(options,
                                   booleanLabelText,
                                   radioColWidth,
                                   boolColWidth,
                                   topspace,
                                   subtitle) {
    var UICONSTANTS = require('common/UICONSTANTS'),
        lang = require('lib/lang'),
        radioview = Titanium.UI.createView({
            right: boolColWidth,
            width: lang.multiplyUnits(options.length, radioColWidth),
            height: Titanium.UI.SIZE,
            bottom: 0,
            backgroundColor: UICONSTANTS.GRID_TITLEROW_BACKGROUND,
            touchEnabled: false
        }),
        colWidthWithinRadioView = lang.divideUnits('100%', options.length),
        i,
        optionLabel,
        booleanLabel,
        subtitleview,
        subtitletext;

    this.tiview = Titanium.UI.createView({
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        top: topspace,
        touchEnabled: false
    });

    for (i = 0; i < options.length; ++i) {
        optionLabel = Titanium.UI.createLabel({
            text: options[i].key,
            font: UICONSTANTS.getRadioFont(),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
            color: UICONSTANTS.GRID_TITLEROW_COLOUR,
            left: lang.multiplyUnits(i, colWidthWithinRadioView),
            bottom: 0,
            height: Titanium.UI.SIZE,
            width: colWidthWithinRadioView,
            touchEnabled: false
        });
        radioview.add(optionLabel);
    }
    this.tiview.add(radioview);

    booleanLabel = Titanium.UI.createLabel({
        text: booleanLabelText,
        font: UICONSTANTS.getRadioFont(),
        textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
        color: UICONSTANTS.GRID_TITLEROW_COLOUR,
        backgroundColor: UICONSTANTS.GRID_TITLEROW_BACKGROUND,
        bottom: 0,
        height: Titanium.UI.SIZE,
        right: 0,
        width: boolColWidth,
        touchEnabled: false
    });
    this.tiview.add(booleanLabel);

    if (subtitle) {
        subtitleview = Titanium.UI.createView({
            left : 0,
            right : lang.addUnits(lang.multiplyUnits(options.length,
                                                     radioColWidth),
                                  boolColWidth),
            height : Titanium.UI.SIZE,
            touchEnabled: false
        });
        subtitletext = Titanium.UI.createLabel({
            text : subtitle,
            font : UICONSTANTS.getGridSubtitleFont(),
            textAlign : Titanium.UI.TEXT_ALIGNMENT_LEFT,
            color : UICONSTANTS.RADIO_TEXT_COLOUR,
            left : 0,
            right : UICONSTANTS.SPACE,
            center : { y : '50%' },
            height : Titanium.UI.SIZE,
            touchEnabled: false
        });
        subtitleview.add(subtitletext);
        this.tiview.add(subtitleview);
    }
}

function RadioGroupGridWSBRow(props) {
    var MODULE_NAME = "RadioGroupGridWSBRow",
        UICONSTANTS = require('common/UICONSTANTS'),
        lang = require('lib/lang'),
        qcommon = require('questionnairelib/qcommon'),
        buttonTipropsArray = [],
        i,
        questionview,
        questiontext,
        buttonview,
        self = this,
        booleanview;
    qcommon.requireProperty(props, "question_index", MODULE_NAME);
    qcommon.requireProperty(props, "question_text", MODULE_NAME);
    qcommon.requireProperty(props, "radioOptions", MODULE_NAME);
    qcommon.requireProperty(props, "topspace", MODULE_NAME);
    qcommon.requireProperty(props, "radioColWidth", MODULE_NAME);
    qcommon.requireProperty(props, "boolColWidth", MODULE_NAME);
    qcommon.requireProperty(props, "readOnly", MODULE_NAME);
    qcommon.requireProperty(props, "mcqField", MODULE_NAME);
    qcommon.requireProperty(props, "booleanField", MODULE_NAME);
    qcommon.requireProperty(props, "mcqMandatory", MODULE_NAME);
    qcommon.requireProperty(props, "booleanMandatory", MODULE_NAME);
    qcommon.requireProperty(props, "booleanBistate", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "setFieldValue", MODULE_NAME);

    this.tiview = Titanium.UI.createView({
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        top: props.topspace,
        touchEnabled: true
    });

    for (i = 0; i < props.radioOptions.length; ++i) {
        buttonTipropsArray.push({ center: { x: '50%', y: '50%' }  });
    }
    this.mcqgroup = new qcommon.McqGroup({
        mandatory: props.mcqMandatory,
        readOnly: props.readOnly,
        options: props.radioOptions,
        setFieldValue: function (newValue) {
            props.setFieldValue(props.mcqField, newValue);
        },
        tipropsArray: buttonTipropsArray,
        extraData: UICONSTANTS.ELEMENT_TYPE_RADIO // extra data
    });

    // Creation from the left
    questionview = Titanium.UI.createView({
        left : 0,
        right : lang.addUnits(lang.multiplyUnits(props.radioOptions.length,
                                                 props.radioColWidth),
                              props.boolColWidth),
        height : Titanium.UI.SIZE
    });
    questiontext = Titanium.UI.createLabel({
        text : props.question_text,
        font: UICONSTANTS.getRadioFont(),
        textAlign : Titanium.UI.TEXT_ALIGNMENT_RIGHT,
        color : UICONSTANTS.RADIO_TEXT_COLOUR,
        left : 0,
        right : UICONSTANTS.SPACE,
        center : { y : '50%' },
        height : Titanium.UI.SIZE,
        touchEnabled: false
    });
    questionview.add(questiontext);
    this.tiview.add(questionview);

    for (i = 0; i < props.radioOptions.length; ++i) {
        buttonview = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            right: lang.addUnits(
                lang.multiplyUnits(props.radioOptions.length - i - 1,
                                   props.radioColWidth),
                props.boolColWidth
            ),
            width: props.radioColWidth,
            extraData: UICONSTANTS.ELEMENT_TYPE_RADIO, // extra data
            index_id: i, // extra data
            touchEnabled: true
        });
        buttonview.add(this.mcqgroup.buttons[i].tiview);
        this.tiview.add(buttonview);
    }

    booleanview = Titanium.UI.createView({
        height: Titanium.UI.SIZE,
        right: 0,
        width: props.boolColWidth,
        extraData: UICONSTANTS.ELEMENT_TYPE_BOOLEAN, // extra data
        touchEnabled: true
    });
    this.booleanwidget = new qcommon.BooleanWidget({
        readOnly: props.readOnly,
        bistate: props.booleanBistate,
        mandatory: props.booleanMandatory,
        red: true,
        size: UICONSTANTS.RADIO_BUTTON_ICON_SIZE,
        setFieldValue: function (newValue) {
            props.setFieldValue(props.booleanField, newValue);
        },
        tiprops: {
            center: { x: '50%', y: '50%' }
        },
        extraData: UICONSTANTS.ELEMENT_TYPE_BOOLEAN // extra data
    });
    booleanview.add(this.booleanwidget.tiview);
    this.tiview.add(booleanview);

    // Dynamic code
    if (!props.readOnly) {
        this.clickListener = function (e) { self.clicked(e); };
        this.tiview.addEventListener('click', this.clickListener);
        this.dblclickListener = function (e) { self.double_clicked(e); };
        this.tiview.addEventListener('dblclick', this.dblclickListener);
    }
}
RadioGroupGridWSBRow.prototype = {

    clicked: function (e) {
        var UICONSTANTS = require('common/UICONSTANTS');
        if (e.source.extraData === UICONSTANTS.ELEMENT_TYPE_RADIO) {
            if (e.source.index_id === undefined || e.source.index_id === null) {
                return;
            }
            this.mcqgroup.select(e.source.index_id);
        } else if (e.source.extraData === UICONSTANTS.ELEMENT_TYPE_BOOLEAN) {
            this.booleanwidget.toggle();
        }
    },

    double_clicked: function (e) {
        var UICONSTANTS = require('common/UICONSTANTS');
        if (e.source.extraData === UICONSTANTS.ELEMENT_TYPE_RADIO) {
            this.mcqgroup.select(null);
        } else if (e.source.extraData === UICONSTANTS.ELEMENT_TYPE_BOOLEAN) {
            this.booleanwidget.toggle();
        }
    },

    cleanup: function () {
        if (this.clickListener) {
            this.tiview.removeEventListener('click', this.clickListener);
            this.clickListener = null;
        }
        if (this.dblclickListener) {
            this.tiview.removeEventListener('dblclick', this.dblclickListener);
            this.dblclickListener = null;
        }
        var uifunc = require('lib/uifunc');
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
        this.mcqgroup.cleanup();
        this.booleanwidget.cleanup();
    }

};

function RadioGroupGridWithSingleBoolean(props) {
    var MODULE_NAME = "RadioGroupGridWithSingleBoolean",
        UICONSTANTS = require('common/UICONSTANTS'),
        lang = require('lib/lang'),
        qcommon = require('questionnairelib/qcommon'),
        i,
        doSubtitle,
        subtitle,
        s,
        titlerow,
        rule,
        newrow;
    qcommon.requireProperty(props, "questions", MODULE_NAME);
    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.requireProperty(props, "mcqFields", MODULE_NAME);
    qcommon.requireProperty(props, "booleanFields", MODULE_NAME);
    qcommon.requireProperty(props, "booleanLabel", MODULE_NAME);
    qcommon.requireProperty(props, "mcqFieldsMandatory", MODULE_NAME);
    qcommon.requireProperty(props, "booleanFieldsMandatory", MODULE_NAME);
    qcommon.setDefaultProperty(props, "booleanBistate", true);
    qcommon.setDefaultProperty(props, "subtitles", []);
    qcommon.setDefaultProperty(props, "rowPadding",
                               UICONSTANTS.RADIO_BUTTON_ICON_SIZE / 8);
    qcommon.setDefaultProperty(props, "radioColWidth",
                               lang.divideUnits('50%',
                                                props.options.length + 1));
    qcommon.setDefaultProperty(props, "boolColWidth",
                               lang.divideUnits('50%',
                                                props.options.length + 1));
    qcommon.requireFunctionProperty(props, "setFieldValue", MODULE_NAME);
    qcommon.setDefaultProperty(props, "tiprops", {});
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultHorizontalPosLeft(props.tiprops, 0);
    qcommon.setDefaultVerticalPosTop(props.tiprops, 0);

    props.tiprops.width = Titanium.UI.FILL;
    props.tiprops.height = Titanium.UI.SIZE;
    props.tiprops.layout = 'vertical';

    this.tiview = Titanium.UI.createView(props.tiprops);
    this.mcqFields = props.mcqFields;
    this.booleanFields = props.booleanFields;

    this.rows = [];
    for (i = 0; i < props.questions.length; ++i) {
        doSubtitle = false;
        subtitle = "";
        for (s = 0; s < props.subtitles.length; ++s) {
            if (props.subtitles[s].beforeIndex === i) {
                doSubtitle = true;
                subtitle = props.subtitles[s].subtitle;
                break;
            }
        }
        if (i === 0 || doSubtitle) {
            titlerow = new RadioGroupGridWSBTitleRow(
                props.options,
                props.booleanLabel,
                props.radioColWidth,
                props.boolColWidth,
                (i === 0 ? 0 : props.rowPadding),
                subtitle
            );
            this.tiview.add(titlerow.tiview);
        }
        if (i > 0 && !doSubtitle) {
            rule = Titanium.UI.createView({
                top: props.rowPadding,
                height: UICONSTANTS.GRID_RULE_HEIGHT,
                width: Titanium.UI.FILL,
                backgroundColor: UICONSTANTS.GRID_RULE_COLOUR
            });
            this.tiview.add(rule);
        }
        newrow = new RadioGroupGridWSBRow({
            question_index: i,
            question_text: props.questions[i],
            radioOptions: props.options,
            topspace: props.rowPadding,
            radioColWidth: props.radioColWidth,
            boolColWidth: props.boolColWidth,
            readOnly: props.readOnly,
            mcqField: props.mcqFields[i],
            booleanField: props.booleanFields[i],
            mcqMandatory: props.mcqFieldsMandatory[i],
            booleanMandatory: props.booleanFieldsMandatory[i],
            booleanBistate: props.booleanBistate,
            setFieldValue: props.setFieldValue // relay the change
        });
        this.rows.push(newrow);
        this.tiview.add(newrow.tiview);
    }
}
RadioGroupGridWithSingleBoolean.prototype = {

    getRadioIndex: function (question_index) {
        return this.rows[question_index].mcqgroup.getIndex();
    },

    getNumSelectedRadio: function () {
        var n = 0,
            i;
        for (i = 0; i < this.rows.length; ++i) {
            if (this.getRadioIndex(i) !== null) {
                ++n;
            }
        }
        return n;
    },

    areAllSelectedRadio: function () {
        return this.getNumSelectedRadio() === this.rows.length;
    },

    setRadioIndex: function (question_index, answer_index) {
        this.rows[question_index].mcqgroup.setIndex(answer_index);
    },

    setAllRadioIndices: function (answer_indices) {
        var i;
        for (i = 0;
                i < this.rows.length && i < answer_indices.length;
                ++i) {
            this.rows[i].mcqgroup.setIndex(answer_indices[i]);
        }
    },

    getBoolean: function (question_index) {
        return this.rows[question_index].booleanwidget.getValue();
    },

    getNumSelectedBoolean: function () {
        var n = 0,
            i;
        for (i = 0; i < this.rows.length; ++i) {
            if (this.getBoolean(i)) {
                ++n;
            }
        }
        return n;
    },

    areAllSelectedBoolean: function () {
        return this.getNumSelectedBoolean() === this.rows.length;
    },

    setBoolean: function (question_index, boolean_value) {
        this.rows[question_index].booleanwidget.setValue(boolean_value);
    },

    setAllBoolean: function (boolean_array) {
        var i;
        for (i = 0;
                i < this.rows.length && i < boolean_array.length;
                ++i) {
            this.rows[i].booleanwidget.setValue(boolean_array[i]);
        }
    },

    setFieldToValue: function (field, value) {
        var i;
        for (i = 0; i < this.mcqFields.length; ++i) {
            if (this.mcqFields[i] === field) {
                this.rows[i].mcqgroup.setValue(value);
            }
            if (this.booleanFields[i] === field) {
                this.rows[i].booleanwidget.setValue(value);
            }
        }
    },

    setMcqMandatory: function (mandatory, index) {
        if (index < 0 || index >= this.rows.length) {
            return;
        }
        this.rows[index].mcqgroup.setMandatory(mandatory);
    },

    setBooleanMandatory: function (mandatory, index) {
        if (index < 0 || index >= this.rows.length) {
            return;
        }
        this.rows[index].booleanwidget.setMandatory(mandatory);
    },

    isInputRequired: function () {
        var i;
        for (i = 0; i < this.rows.length; ++i) {
            if (this.rows[i].mcqgroup.isInputRequired()) {
                return true;
            }
            if (this.rows[i].booleanwidget.isInputRequired()) {
                return true;
            }
        }
        return false;
    },

    cleanup: function () {
        var uifunc = require('lib/uifunc'),
            i;
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
        for (i = 0; i < this.rows.length; ++i) {
            this.rows[i].cleanup();
        }
    }

};
module.exports = RadioGroupGridWithSingleBoolean;
