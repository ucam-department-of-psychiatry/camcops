// RadioGroupGrid.js

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


function RadioGroupGridTitleRow(options, colWidth, topspace, subtitle) {
    var lang = require('lib/lang'),
        UICONSTANTS = require('common/UICONSTANTS'),
        optionsview = Titanium.UI.createView({
            right: 0,
            width: lang.multiplyUnits(options.length, colWidth),
            height: Titanium.UI.SIZE,
            backgroundColor: UICONSTANTS.GRID_TITLEROW_BACKGROUND,
            touchEnabled: false,
        }),
        colWidthWithinView = lang.divideUnits('100%', options.length),
        i,
        optionLabel,
        subtitleview,
        subtitletext;

    this.tiview = Titanium.UI.createView({
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        top: topspace,
        touchEnabled: false,
    });

    for (i = 0; i < options.length; ++i) {
        optionLabel = Titanium.UI.createLabel({
            text: options[i].key,
            font: UICONSTANTS.getRadioFont(),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
            color: UICONSTANTS.GRID_TITLEROW_COLOUR,
            left: lang.multiplyUnits(i, colWidthWithinView),
            bottom: 0,
            height: Titanium.UI.SIZE,
            width: colWidthWithinView,
            touchEnabled: false,
        });
        optionsview.add(optionLabel);
    }
    this.tiview.add(optionsview);

    if (subtitle) {
        subtitleview = Titanium.UI.createView({
            left : 0,
            right : lang.multiplyUnits(options.length, colWidth),
            height : Titanium.UI.SIZE,
            touchEnabled: false,
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
            touchEnabled: false,
        });
        subtitleview.add(subtitletext);
        this.tiview.add(subtitleview);
    }
}

function RadioGroupGridRow(props) {
    var MODULE_NAME = "RadioGroupGridRow",
        lang = require('lib/lang'),
        UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        questionview,
        questiontext,
        i,
        buttonTipropsArray = [],
        buttonview,
        self = this;
    qcommon.requireProperty(props, "questionIndex", MODULE_NAME);
    qcommon.requireProperty(props, "questionText", MODULE_NAME);
    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.requireProperty(props, "topspace", MODULE_NAME);
    qcommon.requireProperty(props, "colWidth", MODULE_NAME);
    qcommon.requireProperty(props, "readOnly", MODULE_NAME);
    qcommon.requireProperty(props, "mandatory", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "setFieldValue", MODULE_NAME);

    this.tiview = Titanium.UI.createView({
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        top: props.topspace,
        touchEnabled: true,
    });

    // Creation from the left
    questionview = Titanium.UI.createView({
        left: 0,
        right: lang.multiplyUnits(props.options.length, props.colWidth),
        height: Titanium.UI.SIZE,
    });
    questiontext = Titanium.UI.createLabel({
        text: props.questionText,
        font: UICONSTANTS.getRadioFont(),
        textAlign: Titanium.UI.TEXT_ALIGNMENT_RIGHT,
        color: UICONSTANTS.RADIO_TEXT_COLOUR,
        left: 0,
        right: UICONSTANTS.SPACE,
        center: { y : '50%' },
        height: Titanium.UI.SIZE,
        touchEnabled: false,
    });
    questionview.add(questiontext);
    this.tiview.add(questionview);
    for (i = 0; i < props.options.length; ++i) {
        buttonTipropsArray.push({ center: { x: '50%', y: '50%' }  });
    }
    this.mcqgroup = new qcommon.McqGroup({
        mandatory: props.mandatory,
        readOnly: props.readOnly,
        options: props.options,
        setFieldValue: function (newValue) {
            props.setFieldValue(props.questionIndex, newValue);
        },
        tipropsArray: buttonTipropsArray,
    });
    for (i = 0; i < props.options.length; ++i) {
        buttonview = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            right: lang.multiplyUnits(props.options.length - i - 1,
                                      props.colWidth),
            width: props.colWidth,
            index_id: i, // extra data
            touchEnabled: true,
        });
        buttonview.add(this.mcqgroup.buttons[i].tiview);
        this.tiview.add(buttonview);
    }
    if (!props.readOnly) {
        // Handle touches to the views
        this.clickListener = function (e) { self.clicked(e); };
        this.tiview.addEventListener('click', this.clickListener);
        this.dblclickListener = function (e) { self.double_clicked(e); };
        this.tiview.addEventListener('dblclick', this.dblclickListener);
    }
}
RadioGroupGridRow.prototype = {

    clicked: function (e) {
        if (e.source.index_id === undefined || e.source.index_id === null) {
            return;
        }
        this.mcqgroup.select(e.source.index_id);
    },

    double_clicked: function () {
        this.mcqgroup.select(null);
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
    },

};

function RadioGroupGrid(props) {
    var MODULE_NAME = "RadioGroupGrid",
        lang = require('lib/lang'),
        UICONSTANTS = require('common/UICONSTANTS'),
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
    qcommon.requireProperty(props, "subtitles", MODULE_NAME);
    qcommon.requireProperty(props, "readOnly", MODULE_NAME);
    qcommon.requireProperty(props, "mandatoryFlags", MODULE_NAME);
    qcommon.setDefaultProperty(props, "rowPadding",
                               UICONSTANTS.RADIO_BUTTON_ICON_SIZE / 8);
    qcommon.setDefaultProperty(props, "colWidth",
                               lang.divideUnits('50%',
                                                props.options.length));
    qcommon.requireFunctionProperty(props, "setFieldValue", MODULE_NAME);
    qcommon.setDefaultProperty(props, "tiprops", {});
    qcommon.setDefaultHorizontalPosLeft(props.tiprops, 0);
    qcommon.setDefaultVerticalPosTop(props.tiprops, 0);

    props.tiprops.width = Titanium.UI.FILL;
    props.tiprops.height = Titanium.UI.SIZE;
    props.tiprops.layout = 'vertical';

    this.tiview = Titanium.UI.createView(props.tiprops);

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
            titlerow = new RadioGroupGridTitleRow(
                props.options,
                props.colWidth,
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
                backgroundColor: UICONSTANTS.GRID_RULE_COLOUR,
            });
            this.tiview.add(rule);
        }
        newrow = new RadioGroupGridRow({
            questionIndex: i,
            questionText: props.questions[i],
            options: props.options,
            topspace: props.rowPadding,
            colWidth: props.colWidth,
            readOnly: props.readOnly,
            mandatory: props.mandatoryFlags[i],
            setFieldValue: props.setFieldValue, // relay the change
        });
        this.rows.push(newrow);
        this.tiview.add(newrow.tiview);
    }

}
RadioGroupGrid.prototype = {

    getIndex: function (questionIndex) {
        return this.rows[questionIndex].mcqgroup.getIndex();
    },

    getValue: function (questionIndex) {
        return this.rows[questionIndex].mcqgroup.getValue();
    },

    getNumSelected: function () {
        var n = 0,
            i;
        for (i = 0; i < this.rows.length; ++i) {
            if (this.getIndex(i) !== null) {
                ++n;
            }
        }
        return n;
    },

    areAllSelected: function () {
        return this.getNumSelected() === this.rows.length;
    },

    isInputRequired: function () {
        var i;
        for (i = 0; i < this.rows.length; ++i) {
            if (this.rows[i].mcqgroup.isInputRequired()) {
                return true;
            }
        }
        return false;
    },

    setIndex: function (questionIndex, answerIndex) {
        this.rows[questionIndex].mcqgroup.setIndex(answerIndex);
    },

    setValue: function (questionIndex, value) {
        this.rows[questionIndex].mcqgroup.setValue(value);
    },

    setAllIndices: function (answerIndices) {
        var i;
        for (i = 0;
                i < this.rows.length && i < answerIndices.length;
                ++i) {
            this.rows[i].mcqgroup.setIndex(answerIndices[i]);
        }
    },

    setAllValues: function (values) {
        var i;
        for (i = 0; i < this.rows.length && i < values.length; ++i) {
            this.rows[i].mcqgroup.setValue(values[i]);
        }
    },

    setMandatory: function (mandatory, index) {
        if (index < 0 || index >= this.rows.length) {
            return;
        }
        this.rows[index].mcqgroup.setMandatory(mandatory);
    },

    cleanup: function () {
        var uifunc = require('lib/uifunc'),
            i;
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
        for (i = 0; i < this.rows.length; ++i) {
            this.rows[i].cleanup();
        }
    },

};
module.exports = RadioGroupGrid;
