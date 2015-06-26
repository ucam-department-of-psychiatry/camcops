// RadioGroupHorizontalCaptionsAbove.js

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

function RadioGroupHorizontalCaptionsAbove(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        MODULE_NAME = "RadioGroupHorizontalCaptionsAbove",
        colWidthPct,
        colWidth,
        buttonTipropsArray = [],
        i,
        toprow = Titanium.UI.createView({
            width: Titanium.UI.FILL,
            height: Titanium.UI.SIZE,
        }),
        bottomrow,
        caption,
        self = this;

    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.setDefaultProperty(props, "space",
                               UICONSTANTS.RADIO_BUTTON_ICON_SIZE / 4);
    qcommon.setDefaultProperty(props, "horizontal", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.setDefaultProperty(props, "readOnly", false);
    // optional property: initialValue
    qcommon.setDefaultProperty(props, "textColour",
                               UICONSTANTS.RADIO_TEXT_COLOUR);
    qcommon.requireFunctionProperty(props, "setFieldValue", MODULE_NAME);
    qcommon.setDefaultProperty(props, "tiprops", {});
    qcommon.setDefaultProperty(props.tiprops, "height", Titanium.UI.SIZE);
    qcommon.setDefaultProperty(props.tiprops, "width", Titanium.UI.FILL);
    qcommon.setDefaultHorizontalPosLeft(props.tiprops, 0);
    qcommon.setDefaultVerticalPosTop(props.tiprops, 0);

    props.tiprops.layout = 'vertical';
    props.tiprops.touchEnabled = true; // worked as false on Android, but to be
    // honest it does make sense that it needs to be true!

    colWidthPct = (100 / props.options.length);
    colWidth = colWidthPct + '%'; // percentage width as a string
    function getColLeft(n) {
        return n * colWidthPct + '%';
    }
    function getColCentre(n) {
        return (n + 0.5) * colWidthPct + '%';
    }

    this.tiview = Titanium.UI.createView(props.tiprops);
    for (i = 0; i < props.options.length; ++i) {
        buttonTipropsArray.push({ center: { x: getColCentre(i), y: '50%' }  });
    }
    this.mcqgroup = new qcommon.McqGroup({
        mandatory: props.mandatory,
        readOnly: props.readOnly,
        options: props.options,
        setFieldValue: props.setFieldValue, // no modification required
        tipropsArray: buttonTipropsArray,
    });

    bottomrow = Titanium.UI.createView({
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        top: props.space,
        touchEnabled: true,
    });
    for (i = 0; i < props.options.length; ++i) {
        caption = Titanium.UI.createLabel({
            text: props.options[i].key,
            font: UICONSTANTS.getRadioFont(),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
            color: props.textColour,
            left: getColLeft(i),
            bottom: 0,
            height: Titanium.UI.SIZE,
            width: colWidth,
            touchEnabled: false,
        });
        toprow.add(caption);
        bottomrow.add(this.mcqgroup.buttons[i].tiview);
    }
    this.tiview.add(toprow);
    this.tiview.add(bottomrow);
    if (!props.readOnly) {
        this.clickListener = function (e) { self.clicked(e); };
        this.tiview.addEventListener('click', this.clickListener);
        this.dblclickListener = function (e) { self.double_clicked(e); };
        this.tiview.addEventListener('dblclick', this.dblclickListener);
    }

    // Set initial value, if desired
    if (props.initialValue !== undefined) {
        this.setValue(props.initialValue);
    }
}
RadioGroupHorizontalCaptionsAbove.prototype = {

    clicked: function (e) {
        if (e.source.index_id === undefined || e.source.index_id === null) {
            return;
        }
        this.mcqgroup.select(e.source.index_id);
    },

    double_clicked: function () {
        this.mcqgroup.select(null);
    },

    // Public interface
    getIndex: function () {
        return this.mcqgroup.getIndex();
    },

    getValue: function () {
        return this.mcqgroup.getValue();
    },

    setIndex: function (index) {
        this.mcqgroup.setIndex(index);
    },

    setValue: function (value) {
        this.mcqgroup.setValue(value);
    },

    setMandatory: function (mandatory) {
        this.mcqgroup.setMandatory(mandatory);
    },

    isInputRequired:  function () {
        return this.mcqgroup.isInputRequired();
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
module.exports = RadioGroupHorizontalCaptionsAbove;
