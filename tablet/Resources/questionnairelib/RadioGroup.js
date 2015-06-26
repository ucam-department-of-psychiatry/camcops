// RadioGroup.js

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

function RadioGroup(props) {
    var UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        MODULE_NAME = "RadioGroup",
        buttonTipropsArray = [],
        i,
        topspace,
        leftspace,
        container,
        textview,
        self = this;

    qcommon.requireProperty(props, "options", MODULE_NAME);
    qcommon.setDefaultProperty(props, "textColour",
                               UICONSTANTS.RADIO_TEXT_COLOUR);
    qcommon.setDefaultProperty(props, "space",
                               UICONSTANTS.RADIO_BUTTON_ICON_SIZE / 4);
    qcommon.setDefaultProperty(props, "horizontal", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.setDefaultProperty(props, "asTextButton", false);
    qcommon.requireFunctionProperty(props, "setFieldValue", MODULE_NAME);
    qcommon.setDefaultProperty(props, "tiprops", {});
    qcommon.setDefaultProperty(props.tiprops, "height", Titanium.UI.SIZE);
    qcommon.setDefaultProperty(props.tiprops, "width", Titanium.UI.FILL);
    qcommon.setDefaultProperty(props, "readOnly", false);
    // optional property: initialValue
    qcommon.setDefaultHorizontalPosLeft(props.tiprops, 0);
    qcommon.setDefaultVerticalPosTop(props.tiprops, 0);

    props.tiprops.layout = props.horizontal ? 'horizontal' : 'vertical';
    props.tiprops.touchEnabled = true; // worked as false on Android, but to be
    // honest it does make sense that it needs to be true!

    this.tiview = Titanium.UI.createView(props.tiprops);
    for (i = 0; i < props.options.length; ++i) {
        buttonTipropsArray.push(props.asTextButton ?
                {} :
                { center: { y: '50%' }  }
            );
    }
    this.mcqgroup = new qcommon.McqGroup({
        asTextButton: props.asTextButton,
        mandatory: props.mandatory,
        readOnly: props.readOnly,
        options: props.options,
        setFieldValue: props.setFieldValue, // no modification required
        tipropsArray: buttonTipropsArray,
    });
    if (props.asTextButton) {
        for (i = 0; i < props.options.length; ++i) {
            this.tiview.add(this.mcqgroup.buttons[i].tiview);
        }
    } else {
        for (i = 0; i < props.options.length; ++i) {
            topspace = props.horizontal ? 0 : (i > 0 ? props.space : 0);
            leftspace = props.horizontal ? (i > 0 ? props.space : 0) : 0;
            container = Titanium.UI.createView({
                width: Titanium.UI.SIZE,
                height: Titanium.UI.SIZE,
                top: topspace,
                left: leftspace,
                touchEnabled: true, // covers its constituent parts
                index_id: i, // extra data
            });
            container.add(this.mcqgroup.buttons[i].tiview);
            textview = Titanium.UI.createLabel({
                text: props.options[i].key,
                font: UICONSTANTS.getRadioFont(),
                textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
                color: props.textColour,
                left: UICONSTANTS.RADIO_BUTTON_ICON_SIZE + UICONSTANTS.SPACE,
                center: {y: '50%'},
                height: Titanium.UI.SIZE,
                width: Titanium.UI.SIZE,
                index_id: i, // extra data
                touchEnabled: true,
            });
            container.add(textview);
            this.tiview.add(container);
        }
    }

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
RadioGroup.prototype = {

    clicked: function (e) {
        if (e.source.index_id === undefined || e.source.index_id === null) {
            return;
        }
        this.mcqgroup.select(e.source.index_id);
    },

    double_clicked: function () {
        // It's sometimes worrying if you can't unselect a radio group.
        // "Did you kill your wife by:
        //      - poison?
        //      - faking a car crash?
        //      - gunshot?"
        // ... you may wish to unselect all options if you tap it
        // accidentally!

        // Titanium.API.trace("RadioGroup.double_clicked");
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

    isInputRequired: function () {
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
        this.mcqgroup.cleanup();
        var uifunc = require('lib/uifunc');
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
    },

};
module.exports = RadioGroup;
