// RadioGroupGridDouble.js

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

function createVerticalRule() {
    var UICONSTANTS = require('common/UICONSTANTS');
    return Titanium.UI.createView({
        left: 0,
        height: UICONSTANTS.RADIO_BUTTON_ICON_SIZE,
        // ... can't be Titanium.UI.FILL, or it gets giant
        width: UICONSTANTS.GRID_RULE_HEIGHT,
        backgroundColor: UICONSTANTS.GRID_RULE_COLOUR
    });
}

function createHorizontalRule() {
    var UICONSTANTS = require('common/UICONSTANTS');
    return Titanium.UI.createView({
        top: 0,
        height: UICONSTANTS.GRID_RULE_HEIGHT,
        width: Titanium.UI.FILL,
        backgroundColor: UICONSTANTS.GRID_RULE_COLOUR
    });
}

function RadioGroupGridDoubleTitleRow(options_1, options_2,
                                      colWidth_1, colWidth_2,
                                      topspace, subtitle,
                                      stem_1, stem_2) {
    var lang = require('lib/lang'),
        UICONSTANTS = require('common/UICONSTANTS'),
        i,
        optionLabel,
        stem_and_options_view_1 = Titanium.UI.createView({
            right: lang.multiplyUnits(options_2.length, colWidth_2),
            width: lang.multiplyUnits(options_1.length, colWidth_1),
            height: Titanium.UI.SIZE,
            layout: 'vertical',
            backgroundColor: UICONSTANTS.GRID_TITLEROW_BACKGROUND,
            touchEnabled: false
        }),
        stem_1_view = Titanium.UI.createLabel({
            text: stem_1,
            font: UICONSTANTS.getRadioFont(),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
            color: UICONSTANTS.GRID_TITLEROW_COLOUR,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            center : { x : '50%' },
            touchEnabled: false
        }),
        optionsview_1 = Titanium.UI.createView({
            width: Titanium.UI.FILL,
            height: Titanium.UI.SIZE,
            touchEnabled: false
        }),
        colWidthWithinView_1 = lang.divideUnits('100%', options_1.length),
        stem_and_options_view_2 = Titanium.UI.createView({
            right: 0,
            width: lang.multiplyUnits(options_2.length, colWidth_2),
            height: Titanium.UI.SIZE,
            layout: 'vertical',
            backgroundColor: UICONSTANTS.GRID_TITLEROW_BACKGROUND,
            touchEnabled: false
        }),
        stem_2_view = Titanium.UI.createLabel({
            text: stem_2,
            font: UICONSTANTS.getRadioFont(),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
            color: UICONSTANTS.GRID_TITLEROW_COLOUR,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            center : { x : '50%' },
            touchEnabled: false
        }),
        optionsview_2 = Titanium.UI.createView({
            width: Titanium.UI.FILL,
            height: Titanium.UI.SIZE,
            touchEnabled: false
        }),
        colWidthWithinView_2 = lang.divideUnits('100%', options_2.length),
        subtitleview,
        subtitletext;

    this.tiview = Titanium.UI.createView({
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        top: topspace,
        touchEnabled: false
    });
    stem_and_options_view_1.add(stem_1_view);
    for (i = 0; i < options_1.length; ++i) {
        optionLabel = Titanium.UI.createLabel({
            text: options_1[i].key,
            font: UICONSTANTS.getRadioFont(),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
            color: UICONSTANTS.GRID_TITLEROW_COLOUR,
            left: lang.multiplyUnits(i, colWidthWithinView_1),
            bottom: 0,
            height: Titanium.UI.SIZE,
            width: colWidthWithinView_1,
            touchEnabled: false
        });
        optionsview_1.add(optionLabel);
    }
    stem_and_options_view_1.add(optionsview_1);
    this.tiview.add(stem_and_options_view_1);

    stem_and_options_view_2.add(stem_2_view);
    for (i = 0; i < options_2.length; ++i) {
        optionLabel = Titanium.UI.createLabel({
            text: options_2[i].key,
            font: UICONSTANTS.getRadioFont(),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
            color: UICONSTANTS.GRID_TITLEROW_COLOUR,
            left: lang.multiplyUnits(i, colWidthWithinView_2),
            bottom: 0,
            height: Titanium.UI.SIZE,
            width: colWidthWithinView_2,
            touchEnabled: false
        });
        optionsview_2.add(optionLabel);
    }
    stem_and_options_view_2.add(optionsview_2);
    this.tiview.add(stem_and_options_view_2);

    if (subtitle) {
        subtitleview = Titanium.UI.createView({
            left: 0,
            right: lang.addUnits(lang.multiplyUnits(options_1.length,
                                                    colWidth_1),
                                 lang.multiplyUnits(options_2.length,
                                                    colWidth_2)),
            height: Titanium.UI.SIZE,
            touchEnabled: false
        });
        subtitletext = Titanium.UI.createLabel({
            text: subtitle,
            font: UICONSTANTS.getGridSubtitleFont(),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
            color: UICONSTANTS.RADIO_TEXT_COLOUR,
            left: 0,
            right: UICONSTANTS.SPACE,
            center: { y: '50%' },
            height: Titanium.UI.SIZE,
            touchEnabled: false
        });
        subtitleview.add(subtitletext);
        this.tiview.add(subtitleview);
    }
}

function RadioGroupGridDoubleRow(props) {
    var MODULE_NAME = "RadioGroupGridDoubleRow",
        lang = require('lib/lang'),
        UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        buttonTipropsArray1 = [],
        buttonTipropsArray2 = [],
        i,
        questionview,
        questiontext,
        buttonview,
        self = this;
    qcommon.requireProperty(props, "questionIndex", MODULE_NAME);
    qcommon.requireProperty(props, "questionText", MODULE_NAME);
    qcommon.requireProperty(props, "options_1", MODULE_NAME);
    qcommon.requireProperty(props, "options_2", MODULE_NAME);
    qcommon.requireProperty(props, "topspace", MODULE_NAME);
    qcommon.requireProperty(props, "colWidth_1", MODULE_NAME);
    qcommon.requireProperty(props, "colWidth_2", MODULE_NAME);
    qcommon.requireProperty(props, "readOnly", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "setFieldValue_1", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "setFieldValue_2", MODULE_NAME);
    qcommon.requireProperty(props, "mandatory_1", MODULE_NAME);
    qcommon.requireProperty(props, "mandatory_2", MODULE_NAME);

    this.tiview = Titanium.UI.createView({
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        top: props.topspace,
        touchEnabled: true
    });
    for (i = 0; i < props.options_1.length; ++i) {
        buttonTipropsArray1.push({ center: { x: '50%', y: '50%' }  });
    }
    this.mcqgroup1 = new qcommon.McqGroup({
        mandatory: props.mandatory_1,
        readOnly: props.readOnly,
        options: props.options_1,
        setFieldValue: props.setFieldValue_1, // no modification required
        tipropsArray: buttonTipropsArray1,
        extraData: 1 // extra data
    });
    for (i = 0; i < props.options_2.length; ++i) {
        buttonTipropsArray2.push({ center: { x: '50%', y: '50%' }  });
    }
    this.mcqgroup2 = new qcommon.McqGroup({
        mandatory: props.mandatory_2,
        readOnly: props.readOnly,
        options: props.options_2,
        setFieldValue: props.setFieldValue_2, // no modification required
        tipropsArray: buttonTipropsArray2,
        extraData: 2 // extra data
    });

    // Creation from the left
    questionview = Titanium.UI.createView({
        left : 0,
        right : lang.addUnits(lang.multiplyUnits(props.options_1.length,
                                                 props.colWidth_1),
                              lang.multiplyUnits(props.options_2.length,
                                                 props.colWidth_2)),
        height : Titanium.UI.SIZE
    });
    questiontext = Titanium.UI.createLabel({
        text : props.questionText,
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
    for (i = 0; i < props.options_1.length; ++i) {
        buttonview = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            right: lang.addUnits(
                lang.multiplyUnits(props.options_1.length - i - 1,
                                   props.colWidth_1),
                lang.multiplyUnits(props.options_2.length,
                                   props.colWidth_2)
            ),
            width: props.colWidth_1,
            index_id: i, // extra data
            extraData: 1, // extra data
            touchEnabled: true
        });
        buttonview.add(this.mcqgroup1.buttons[i].tiview);
        this.tiview.add(buttonview);
    }
    for (i = 0; i < props.options_2.length; ++i) {
        buttonview = Titanium.UI.createView({
            height: Titanium.UI.SIZE,
            right: lang.multiplyUnits(props.options_2.length - i - 1,
                                      props.colWidth_2),
            width: props.colWidth_2,
            index_id: i, // extra data
            extraData: 2, // extra data
            touchEnabled: true
        });
        if (i === 0) {
            buttonview.add(createVerticalRule());
        }
        buttonview.add(this.mcqgroup2.buttons[i].tiview);
        this.tiview.add(buttonview);
    }
    if (!props.readOnly) {
        this.clickListener = function (e) { self.clicked(e); };
        this.tiview.addEventListener('click', this.clickListener);
        this.dblclickListener = function (e) { self.double_clicked(e); };
        this.tiview.addEventListener('dblclick', this.dblclickListener);
        // ... handles all click events
    }
}
RadioGroupGridDoubleRow.prototype = {

    clicked: function (e) {
        if (e.source.index_id === undefined || e.source.index_id === null) {
            return;
        }
        if (e.source.extraData === 1) {
            this.mcqgroup1.select(e.source.index_id);
        } else {
            this.mcqgroup2.select(e.source.index_id);
        }
    },

    double_clicked: function (e) {
        if (e.source.extraData === undefined || e.source.extraData === null) {
            return;
        }
        if (e.source.extraData === 1) {
            this.mcqgroup1.select(null);
        } else {
            this.mcqgroup2.select(null);
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
        this.mcqgroup1.cleanup();
        this.mcqgroup2.cleanup();
    }

};

function RadioGroupGridDouble(props) {
    var MODULE_NAME = "RadioGroupGridDouble",
        lang = require('lib/lang'),
        UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        i,
        s,
        doSubtitle,
        subtitle,
        titlerow,
        newrow;
    qcommon.requireProperty(props, "questions", MODULE_NAME);
    qcommon.requireProperty(props, "options_1", MODULE_NAME);
    qcommon.requireProperty(props, "options_2", MODULE_NAME);
    qcommon.requireProperty(props, "stem_1", MODULE_NAME);
    qcommon.requireProperty(props, "stem_2", MODULE_NAME);
    qcommon.requireProperty(props, "mandatoryFlags_1", MODULE_NAME);
    qcommon.requireProperty(props, "mandatoryFlags_2", MODULE_NAME);
    qcommon.setDefaultProperty(props, "subtitles", []);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "rowPadding",
                               UICONSTANTS.RADIO_BUTTON_ICON_SIZE / 8);
    qcommon.setDefaultProperty(props, "colWidth_1",
                               lang.divideUnits('33%',
                                                props.options_1.length));
    qcommon.setDefaultProperty(props, "colWidth_2",
                               lang.divideUnits('33%',
                                                props.options_2.length));
    qcommon.requireFunctionProperty(props, "setFieldValue_1", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "setFieldValue_2", MODULE_NAME);
    qcommon.setDefaultProperty(props, "tiprops", {});
    qcommon.setDefaultHorizontalPosLeft(props.tiprops, 0);
    qcommon.setDefaultVerticalPosTop(props.tiprops, 0);

    props.tiprops.width = Titanium.UI.FILL;
    props.tiprops.height = Titanium.UI.SIZE;
    props.tiprops.layout = 'vertical';

    this.tiview = Titanium.UI.createView(props.tiprops);

    function makeFnSetFieldValue_1(questionIndex) {
        // Beware the Javascript Callback Loop Bug
        return function (newValue) {
            props.setFieldValue_1(questionIndex, newValue);
        };
    }
    function makeFnSetFieldValue_2(questionIndex) {
        // Beware the Javascript Callback Loop Bug
        return function (newValue) {
            props.setFieldValue_2(questionIndex, newValue);
        };
    }

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
            titlerow = new RadioGroupGridDoubleTitleRow(
                props.options_1,
                props.options_2,
                props.colWidth_1,
                props.colWidth_2,
                (i === 0 ? 0 : props.rowPadding),
                subtitle,
                props.stem_1,
                props.stem_2
            );
            this.tiview.add(titlerow.tiview);
        }
        if (i > 0 && !doSubtitle) {
            this.tiview.add(createHorizontalRule());
        }
        newrow = new RadioGroupGridDoubleRow({
            questionIndex: i,
            questionText: props.questions[i],
            options_1: props.options_1,
            options_2: props.options_2,
            topspace: props.rowPadding,
            colWidth_1: props.colWidth_1,
            colWidth_2: props.colWidth_2,
            readOnly: props.readOnly,
            setFieldValue_1: makeFnSetFieldValue_1(i),
            setFieldValue_2: makeFnSetFieldValue_2(i),
            mandatory_1: props.mandatoryFlags_1[i],
            mandatory_2: props.mandatoryFlags_2[i]
        });
        this.rows.push(newrow);
        this.tiview.add(newrow.tiview);
    }
}
RadioGroupGridDouble.prototype = {

    getIndex_1: function (questionIndex) {
        return this.rows[questionIndex].mcqgroup1.getIndex();
    },

    getIndex_2: function (questionIndex) {
        return this.rows[questionIndex].mcqgroup2.getIndex();
    },

    getValue_1: function (questionIndex) {
        return this.rows[questionIndex].mcqgroup1.getValue();
    },

    getValue_2: function (questionIndex) {
        return this.rows[questionIndex].mcqgroup1.getValue();
    },

    getNumSelected_1: function () {
        var n = 0,
            i;
        for (i = 0; i < this.rows.length; ++i) {
            if (this.getIndex_1(i) !== null) {
                ++n;
            }
        }
        return n;
    },

    getNumSelected_2: function () {
        var n = 0,
            i;
        for (i = 0; i < this.rows.length; ++i) {
            if (this.getIndex_2(i) !== null) {
                ++n;
            }
        }
        return n;
    },

    areAllSelected_1: function () {
        return this.getNumSelected_1() === this.rows.length;
    },

    areAllSelected_2: function () {
        return this.getNumSelected_2() === this.rows.length;
    },

    setIndex_1: function (questionIndex, answerIndex) {
        this.rows[questionIndex].mcqgroup1.setIndex(answerIndex);
    },

    setIndex_2: function (questionIndex, answerIndex) {
        this.rows[questionIndex].mcqgroup2.setIndex(answerIndex);
    },

    setValue_1: function (questionIndex, value) {
        this.rows[questionIndex].mcqgroup1.setValue(value);
    },

    setValue_2: function (questionIndex, value) {
        this.rows[questionIndex].mcqgroup2.setValue(value);
    },

    setAllIndices: function (answerIndices_1, answerIndices_2) {
        var i;
        for (i = 0;
                i < this.rows.length &&
                    i < answerIndices_1.length &&
                    i < answerIndices_2.length;
                ++i) {
            this.rows[i].mcqgroup1.setIndex(answerIndices_1[i]);
            this.rows[i].mcqgroup2.setIndex(answerIndices_2[i]);
        }
    },

    setAllValues: function (values_1, values_2) {
        var i;
        for (i = 0;
                i < this.rows.length &&
                    i < values_1.length &&
                    i < values_2.length;
                ++i) {
            this.rows[i].mcqgroup1.setValue(values_1[i]);
            this.rows[i].mcqgroup2.setValue(values_2[i]);
        }
    },

    setMandatory_1: function (mandatory, index) {
        if (index < 0 || index >= this.rows.length) {
            return;
        }
        this.rows[index].mcqgroup1.setMandatory(mandatory);
    },

    setMandatory_2: function (mandatory, index) {
        if (index < 0 || index >= this.rows.length) {
            return;
        }
        this.rows[index].mcqgroup2.setMandatory(mandatory);
    },

    isInputRequired: function () {
        var i;
        for (i = 0; i < this.rows.length; ++i) {
            if (this.rows[i].mcqgroup1.isInputRequired()) {
                return true;
            }
            if (this.rows[i].mcqgroup2.isInputRequired()) {
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
module.exports = RadioGroupGridDouble;
