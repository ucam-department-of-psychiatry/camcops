// ImageGroupVertical.js

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

function ImageGroupRow(props) {
    var MODULE_NAME = "ImageGroupRow",
        UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        imageprops,
        text;
    qcommon.requireProperty(props, "index", MODULE_NAME);
    qcommon.requireProperty(props, "text", MODULE_NAME);
    qcommon.requireProperty(props, "activeImage", MODULE_NAME);
    qcommon.requireProperty(props, "inactiveImage", MODULE_NAME);
    // optional property: imageHeight
    // optional property: imageWidth

    this.activeImage = props.activeImage;
    this.inactiveImage = props.inactiveImage;
    this.tiview = Titanium.UI.createView({
        left: 0,
        top: 0,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        index: props.index, // extra data
        touchEnabled: true // covers its constituent parts
    });

    // iOS image scaling problem here. Probably this:
    //      https://jira.appcelerator.org/browse/TIMOB-3749
    // ... fixed in Titanium 3.0.0

    imageprops = {
        image: props.inactiveImage,
        left: 0,
        top: 0,
        index: props.index, // extra data
        touchEnabled: false
    };
    if (props.imageHeight) {
        imageprops.height = props.imageHeight;
    }
    if (props.imageWidth) {
        imageprops.width = props.imageWidth;
    }

    this.imgInactive = Titanium.UI.createImageView(imageprops);
    this.tiview.add(this.imgInactive);

    imageprops.image = props.activeImage;
    imageprops.visible = false;
    this.imgActive = Titanium.UI.createImageView(imageprops);
    this.tiview.add(this.imgActive);

    text = Titanium.UI.createLabel({
        text: props.text,
        font: UICONSTANTS.getRadioFont(),
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        color: UICONSTANTS.RADIO_TEXT_COLOUR,
        left: props.imageWidth,
        center: {y: '50%'},
        // top: 0,
        height: Titanium.UI.SIZE,
        width: Titanium.UI.SIZE,
        index: props.index, // extra data
        touchEnabled: false
    });
    this.tiview.add(text);
}
ImageGroupRow.prototype = {

    select: function () {
        this.imgActive.show();
        this.imgInactive.hide();
    },

    deselect: function () {
        this.imgInactive.show();
        this.imgActive.hide();
    },

    cleanup: function () {
        var uifunc = require('lib/uifunc');
        uifunc.removeAllViewChildren(this.tiview);
        this.tiview = null;
        this.imgInactive = null;
        this.imgActive = null;
    }

};

function ImageGroupVertical(props) {
    var MODULE_NAME = "ImageGroupVertical",
        UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        i,
        row,
        self = this;
    qcommon.requireProperty(props, "text", MODULE_NAME);
    qcommon.requireProperty(props, "values", MODULE_NAME);
    qcommon.requireProperty(props, "activeImages", MODULE_NAME);
    qcommon.requireProperty(props, "inactiveImages", MODULE_NAME);
    qcommon.requireProperty(props, "readOnly", MODULE_NAME);
    qcommon.requireProperty(props, "mandatory", MODULE_NAME);
    qcommon.requireFunctionProperty(props, "setFieldValue", MODULE_NAME);
    qcommon.setDefaultProperty(props, "tiprops", {});
    // optional property: imageHeight
    // optional property: imageWidth
    qcommon.requireSameLength(props, "activeImages", "text", MODULE_NAME);
    qcommon.requireSameLength(props, "activeImages", "inactiveImages",
                              MODULE_NAME);
    qcommon.setDefaultHorizontalPosLeft(props.tiprops, 0);
    qcommon.setDefaultVerticalPosTop(props.tiprops, 0);

    props.tiprops.width = Titanium.UI.SIZE;
    props.tiprops.height = Titanium.UI.SIZE;
    props.tiprops.touchEnabled = true;

    this.tiview = Titanium.UI.createView(props.tiprops);
    this.setFieldValue = props.setFieldValue;
    this.mandatory = props.mandatory;
    this.values = props.values;

    this.indicator = new qcommon.ValidityIndicator({
        size: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE
    });
    this.tiview.add(this.indicator.tiview);
    this.maincontainer = Titanium.UI.createView({
        left: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE,
        top: 0,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE,
        layout: 'vertical'
    });
    this.tiview.add(this.maincontainer);

    this.rows = [];
    this.selected_id = null;

    for (i = 0; i < props.inactiveImages.length; ++i) {
        row = new ImageGroupRow({
            activeImage: props.activeImages[i],
            inactiveImage: props.inactiveImages[i],
            text: props.text[i],
            imageHeight: props.imageHeight,
            imageWidth: props.imageWidth,
            index: i // extra data
        });
        this.rows.push(row);
        this.maincontainer.add(row.tiview);
    }

    if (!props.readOnly) {
        this.clickListener = function (e) { self.clicked(e); };
        this.maincontainer.addEventListener('click', this.clickListener);
    }
}
ImageGroupVertical.prototype = {

    select: function (index, quietly) {
        if (this.selected_id !== null) {
            this.rows[this.selected_id].deselect();
        }
        if (index === null || index < 0 || index >= this.rows.length) {
            this.selected_id = null;
        } else {
            this.selected_id = index;
            this.rows[this.selected_id].select();
        }
        this.applyMandatory();
        if (!quietly) {
            this.setFieldValue(this.getValue()); // send the data back
        }
    },

    clicked: function (e) {
        // Titanium.API.info("ImageGroupVertical clicked: e.source = " +
        //                   e.source);
        if (e.source.index === undefined || e.source.index === null) {
            return;
        }
        this.select(e.source.index);
    },

    applyMandatory: function () {
        if (this.mandatory && this.selected_id === null) {
            this.indicator.setRequired();
        } else if (this.selected_id === null) {
            this.indicator.setNullButOptional();
        } else {
            this.indicator.clear();
        }
    },

    // Public interface
    getIndex: function () {
        return this.selected_id;
    },

    getValue: function () {
        if (this.selected_id === null) {
            return null;
        }
        return this.values[this.selected_id];
    },

    setIndex: function (index) {
        this.select(index, true);
    },

    setValue: function (value) {
        var lang = require('lib/lang'),
            index = lang.arrayGetIndexByValue(this.values, value);
        this.select(index, true);
        this.applyMandatory();
    },

    setMandatory: function (mandatory) {
        this.mandatory = mandatory;
        this.applyMandatory();
    },

    isInputRequired: function () {
        return this.mandatory && this.selected_id === null;
    },

    cleanup: function () {
        var i;
        this.tiview.removeAllChildren();
        this.tiview = null;
        if (this.clickListener) {
            this.maincontainer.removeEventListener('click',
                                                   this.clickListener);
            this.clickListener = null;
        }
        this.maincontainer.removeAllChildren();
        this.maincontainer = null;
        for (i = 0; i < this.rows.length; ++i) {
            this.rows[i].cleanup();
        }
    }

};
module.exports = ImageGroupVertical;
