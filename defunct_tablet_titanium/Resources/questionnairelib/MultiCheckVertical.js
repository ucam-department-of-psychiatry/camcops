// MultiCheckVertical.js

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

function MultiCheckVertical(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        MODULE_NAME = "MultiCheckVertical",
        i,
        newcheck,
        container,
        textlabel,
        self = this;
    qcommon.requireProperty(props, "optionFieldMap", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "setFieldValue", MODULE_NAME);
    qcommon.setDefaultProperty(props, "max", 1);
    qcommon.setDefaultProperty(props, "min", 1);
    qcommon.setDefaultProperty(props, "space",
                               UICONSTANTS.RADIO_BUTTON_ICON_SIZE / 4);
    qcommon.setDefaultProperty(props, "tiprops", {});
    qcommon.setDefaultProperty(props.tiprops, "height", Titanium.UI.SIZE);
    qcommon.setDefaultProperty(props.tiprops, "width", Titanium.UI.FILL);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.setDefaultProperty(props, "asTextButton", false);
    props.max = Math.max(1, props.max); // must be at least 1
    qcommon.setDefaultHorizontalPosLeft(props.tiprops, 0);
    qcommon.setDefaultVerticalPosTop(props.tiprops, 0);
    props.tiprops.layout = 'vertical';
    props.tiprops.touchEnabled = true;
    // qcommon.debugProps(props, MODULE_NAME);

    // Internals
    this.mandatory = props.mandatory;
    this.tiview = Titanium.UI.createView(props.tiprops);
    this.checks = [];
    this.optionFieldMap = props.optionFieldMap;
    this.min = props.min;
    this.max = props.max;

    function makeFnSetFieldValue(field) {
        // Beware the Javascript Callback Loop Bug
        return function (newValue) {
            props.setFieldValue(field, newValue);
        };
    }

    for (i = 0; i < props.optionFieldMap.length; ++i) {
        newcheck = new qcommon.BooleanWidget({
            asTextButton: props.asTextButton,
            readOnly: props.readOnly,
            bistate: true,
            red: true,
            size: UICONSTANTS.RADIO_BUTTON_ICON_SIZE,
            setFieldValue: makeFnSetFieldValue(props.optionFieldMap[i].value),
            // fnToggle: makeFnToggle(i),
            extraData: i,
            tiprops: props.asTextButton ? {} : {center: {y: '50%'}},
            text: props.asTextButton ? props.optionFieldMap[i].key : ""
        });
        if (props.asTextButton) {
            this.tiview.add(newcheck.tiview);
        }
        this.checks.push(newcheck);
    }
    if (!props.asTextButton) {
        for (i = 0; i < props.optionFieldMap.length; ++i) {
            container = Titanium.UI.createView({
                width: Titanium.UI.FILL,
                height: Titanium.UI.SIZE,
                top: (i > 0 ? props.space : 0),
                row_id: i // extra data
            });
            textlabel = Titanium.UI.createLabel({
                text: props.optionFieldMap[i].key,
                font: UICONSTANTS.getRadioFont(),
                textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
                color: UICONSTANTS.RADIO_TEXT_COLOUR,
                left: UICONSTANTS.RADIO_BUTTON_ICON_SIZE + UICONSTANTS.SPACE,
                center: {y: '50%'},
                // top: 0,
                height: Titanium.UI.SIZE,
                width: Titanium.UI.SIZE,
                row_id: i // extra data
            });
            container.add(this.checks[i].tiview);
            container.add(textlabel);
            this.tiview.add(container);
        }
    }

    if (!props.readOnly) {
        this.clickListener = function (e) { self.clicked(e); };
        this.tiview.addEventListener('click', this.clickListener);
    }
}
MultiCheckVertical.prototype = {

    toggle: function (index) {
        //Titanium.API.info("MultiCheckVertical toggle: index = " + index +
        //                  ", props = " + JSON.stringify(props));
        // var field = this.optionFieldMap[index].value;
        if (this.checks[index].getValue()) {
            this.checks[index].toggle();
        } else {
            if (this.getNumSelected() < this.max) {
                this.checks[index].toggle();
            }
        }
        this.applyMandatory();
    },

    clicked: function (e) {
        // This works because all objects that might trigger the event have a
        // "row_id" embedded in them.
        // It looks like the event comes from the Row view, not the inner
        // buttons... anyway, shove "row_id" everywhere.
        // Then we can have a single event listener: more efficient.
        // Explore e if there are problems.
        if (e.source.extraData !== undefined && e.source.extraData !== null) {
            this.toggle(e.source.extraData); // from a BooleanWidget
        } else if (e.source.row_id !== undefined && e.source.row_id !== null) {
            this.toggle(e.source.row_id); // from something else
        }
    },

    applyMandatory: function () {
        var needmandatory = (this.mandatory &&
                             (this.getNumSelected() < this.min)),
            i;
        for (i = 0; i < this.checks.length; ++i) {
            this.checks[i].setMandatory(needmandatory);
        }
    },

    // Public interface
    isSelected: function (index) {
        return this.checks[index].getValue();
    },

    getNumSelected: function () {
        var count = 0,
            i;
        for (i = 0; i < this.checks.length; ++i) {
            if (this.checks[i].getValue()) {
                ++count;
            }
        }
        return count;
    },

    getAllSelected: function () {
        var selected = [],
            i;
        for (i = 0; i < this.checks.length; ++i) {
            selected.push(this.checks[i].getValue());
        }
        return selected;
    },

    setSelected: function (index, value) {
        if (index === undefined || index === null || index < 0 ||
                index > this.checks.length) {
            return;
        }
        this.checks[index].setValue(value);
        this.applyMandatory();
    },

    setAllSelected: function (selected) {
        var i;
        for (i = 0; i < selected.length && i < this.checks.length; ++i) {
            this.checks[i].setValue(selected[i]);
        }
        this.applyMandatory();
    },

    setFieldToValue: function (field, value) {
        var lang = require('lib/lang'),
            index = lang.kvpGetIndexByValue(this.optionFieldMap, field);
        this.setSelected(index, value);
        this.applyMandatory();
    },

    setMandatory: function (mandatory) {
        this.mandatory = mandatory;
        this.applyMandatory();
    },

    isInputRequired: function () {
        return this.mandatory && this.getNumSelected() < this.min;
    },

    cleanup: function () {
        if (this.clickListener) {
            this.tiview.removeEventListener('click', this.clickListener);
            this.clickListener = null;
        }
        var uifunc = require('lib/uifunc');
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
    }

};
module.exports = MultiCheckVertical;
