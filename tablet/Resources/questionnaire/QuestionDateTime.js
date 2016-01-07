// QuestionDateTime.js

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

/*jslint node: true, newcap: true */
"use strict";
/*global Titanium, L */

/*
    Date versus moment principles:
    ===========================================================================
    The Titanium date/time pickers use Date().
    Date() objects are not timezone-aware.
    We assume the user is operating in the current timezone.
    Moment has e.g. 15:00+0100 for 3pm BST (= 2pm GMT)
    So when we convert from moment() to Date(), we should STRIP the
    timezone information.
    And when we convert from Date() to moment(), we should ADD the current
    timezone information.
    However, it seems that the pickers are also timezone-aware... so they'll
    show 2pm UTC as 3pm when in BST.

    Parsing text as dates with moment:
    ===========================================================================
    PREAMBLE:
        sudo npm install moment
        node
    THEN:
        var moment = require('moment');

        // Accepts all ISO-8601 formats:

        moment("2000-12-30");
        moment("2000-12-30 18:52");
        moment("2000-12-30 18:52+0100");

        // Otherwise falls back to Date(string), which uses Date.parse(string):
        // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/parse
        // http://tools.ietf.org/html/rfc2822#page-14

        moment("March 21, 2012 2:53 pm");
        moment("3 Jan 1980");

    Layout with all elements present:
    ===========================================================================

        BUTTON_NOW      STATIC_TEXT
        BUTTON_CLEAR    WIDGET_DATE WIDGET_TIME
        INDICATOR       TEXT_ENTRY

        WIDGET_DATE + WIDGET_TIME in widgetcontainer (H)
        STATIC_TEXT + widgetcontainer + TEXT_ENTRY in datacontainer (V)
        BUTTON_NOW + BUTTON_CLEAR + INDICATOR in buttoncontainer (V)
        buttoncontainer + datacontainer in this.tiview (H)
*/

var MODULE_NAME = "QuestionDateTime",
    qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang'),
    moment = require('lib/moment');

function QuestionDateTime(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon'),
        platform = require('lib/platform'),
        uifunc = require('lib/uifunc'),
        self = this,
        widgetcontainer,
        datacontainer,
        buttoncontainer;
    qcommon.requireProperty(props, "field", MODULE_NAME);
    qcommon.setDefaultProperty(props, "showTime", false);
    qcommon.setDefaultProperty(props, "minuteInterval", 1);
    qcommon.setDefaultProperty(props, "readOnly", false);
    qcommon.setDefaultProperty(props, "mandatory", true);
    qcommon.setDefaultProperty(props, "offerNowButton", true);
    qcommon.setDefaultProperty(props, "offerNullButton", false);
    qcommon.setDefaultProperty(props, "textInput", true);
    qcommon.setDefaultProperty(props, "useWidgets", true);
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    this.props = props;
    this.showDateAsText = true; // (props.readOnly || props.textInput);
    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE,
        layout: 'horizontal'
    });

    buttoncontainer = Titanium.UI.createView({
        left: 0,
        top: 0,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE,
        layout: 'vertical'
    });
    this.tiview.add(buttoncontainer);

    this.indicator = new qcommon.ValidityIndicator({
        size: UICONSTANTS.QUESTIONNAIRE_WARNING_IMAGE_SIZE
    });
    buttoncontainer.add(this.indicator.tiview);

    datacontainer = Titanium.UI.createView({
        left: 0,
        top: 0,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE,
        layout: 'vertical'
    });
    this.tiview.add(datacontainer);

    this.separateTime = platform.android && props.showTime && props.useWidgets;
    this.composite_datetime = moment();
    // ... used to track time with separate date/time pickers.

    // So these things are reliably null if unused:
    this.date_as_text = null;
    this.editbox = null;

    if (this.showDateAsText) {
        // Read only mode... or additional text display
        // The pickers can't be made not to rotate, which is confusing in a
        // read-only context, even if we don't read their value.
        // So we won't display any.

        this.date_as_text = Titanium.UI.createLabel({
            left: 0,
            top: 0,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            font: UICONSTANTS.getQuestionnaireFont(false, true, false), // bold
            color: UICONSTANTS.READONLY_ANSWER_COLOUR,
            text: this.momentToPrettyText(this.getRawFieldValue())
        });
        datacontainer.add(this.date_as_text);
    }
    if (!props.readOnly) {
        widgetcontainer = Titanium.UI.createView({
            left: 0,
            top: 0,
            width: Titanium.UI.SIZE,
            height: Titanium.UI.SIZE,
            // backgroundColor: UICONSTANTS.ANDROID_WIDGET_BACKGROUND_COLOUR,
            // for Android (date/time things are transparent, with white text)
            layout: 'horizontal'
        });
        datacontainer.add(widgetcontainer);
        if (this.separateTime) {
            // No date+time picker in Android; make it out of a date picker
            // with a time picker to the right
            this.datepicker = Titanium.UI.createPicker({
                top: 0,
                left: 0,
                width : Titanium.UI.SIZE,
                height : Titanium.UI.SIZE,
                type: Titanium.UI.PICKER_TYPE_DATE
                // selectionIndicator: true,
            });
            this.timepicker = Titanium.UI.createPicker({
                left: 0,
                center: { y: '50%' }, // it's smaller than the date picker so
                // centre it vertically
                width : Titanium.UI.SIZE,
                height : Titanium.UI.SIZE,
                type: Titanium.UI.PICKER_TYPE_TIME,
                // selectionIndicator: true,
                format24: true,
                minuteInterval: props.minuteInterval
            });
            widgetcontainer.add(this.datepicker);
            widgetcontainer.add(this.timepicker);
            this.dateListener = function (e) { self.dateValueChangedFromWidget(e); };
            this.datepicker.addEventListener('change', this.dateListener);
            this.timeListener = function (e, value) {
                self.timeValueChangedFromWidget(e, value);
            };
            this.timepicker.addEventListener('change', this.timeListener);
        } else if (props.useWidgets) {
            this.datetimepicker = Titanium.UI.createPicker({
                left: 0,
                top: 0,
                width : Titanium.UI.SIZE,
                height : Titanium.UI.SIZE,
                type: (
                    props.showTime ?
                            Titanium.UI.PICKER_TYPE_DATE_AND_TIME :
                            Titanium.UI.PICKER_TYPE_DATE
                ),
                // selectionIndicator: true,
                format24: true, // Android only
                minuteInterval: props.minuteInterval
            });
            widgetcontainer.add(this.datetimepicker);
            this.datetimeListener = function (e, value) {
                self.datetimeValueChangedFromWidget(e, value);
            };
            this.datetimepicker.addEventListener('change',
                                                 this.datetimeListener);
        }
        if (props.textInput) {
            this.editbox = Titanium.UI.createTextField({
                left: 0,
                top: 0,
                height: Titanium.UI.SIZE,
                width: Titanium.UI.SIZE,

                autocapitalization: Titanium.UI.TEXT_AUTOCAPITALIZATION_NONE,
                autocorrect: false,
                backgroundColor: (props.mandatory ?
                        UICONSTANTS.ANSWER_BACKGROUND_COLOUR_REQUIRED :
                        (props.readOnly ?
                                UICONSTANTS.ANSWER_BACKGROUND_COLOUR_READONLY :
                                UICONSTANTS.ANSWER_BACKGROUND_COLOUR
                        )
                ),
                color: UICONSTANTS.ANSWER_COLOUR,
                editable: !props.readOnly,
                ellipsize: true, // Android only
                font: UICONSTANTS.getQuestionnaireFont(false, true, false), // bold
                hintText: props.showTime ? L('hint_datetime') : L('hint_date'),
                keyboardType: Titanium.UI.KEYBOARD_DEFAULT,
                maxLength: UICONSTANTS.DATETIME_TEXTENTRY_MAXLENGTH,
                passwordMask: false,
                suppressReturn: true, // not multiline
                value: null, // Will be overwritten later
                verticalAlign: Titanium.UI.TEXT_VERTICAL_ALIGNMENT_TOP
            });
            this.editChangedListener = function (e) {
                self.editChanged(e);
            };
            this.editbox.addEventListener('change', this.editChangedListener);
            this.editFocusLostListener = function (e) {
                self.editFocusLost(e);
            };
            this.editbox.addEventListener('blur', this.editFocusLostListener);
            datacontainer.add(this.editbox);
        }
        if (props.offerNowButton) {
            this.offerNowButton = uifunc.createGenericButton(
                UICONSTANTS.ICON_TIME_NOW,
                // { left: 0, top: UICONSTANTS.ICONSIZE }, // extra space
                { left: 0, top: 0 }, // no extra space
                UICONSTANTS.ICON_TIME_NOW_T
            );
            buttoncontainer.add(this.offerNowButton);
            this.offerNowListener = function () { self.setToNow(); };
            this.offerNowButton.addEventListener('click',
                                                 this.offerNowListener);
        }
        if (props.offerNullButton) {
            this.offerNullButton = uifunc.createDeleteButton({
                left: 0,
                // top: UICONSTANTS.ICONSIZE // extra space
                top: 0 // no extra space
            });
            buttoncontainer.add(this.offerNullButton);
            this.offerNullListener = function () { self.setToNull(); };
            this.offerNullButton.addEventListener('click',
                                                  this.offerNullListener);
        }
    }
}
lang.inheritPrototype(QuestionDateTime, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionDateTime, {

    // SET FROM FIELD
    setFromField: function () {
        var momentvalue = this.getRawFieldValue();
        this.setWidgetValue(momentvalue);
        this.setStaticTextValue(momentvalue);
        this.setEditBoxValue(momentvalue);
        this.applyMandatory();
    },

    // VALIDATION AND RETURNING VALUE TO FIELD
    dateValueChangedFromWidget: function (e) {
        // Titanium.API.trace("dateValueChangedFromWidget: e: "
        //                    + JSON.stringify(e));
        var datevalue = e.value;
        this.composite_datetime.date(datevalue.getDate());
        this.composite_datetime.month(datevalue.getMonth());
        this.composite_datetime.year(datevalue.getFullYear());
        // Titanium.API.trace("dateValueChangedFromWidget: composite_datetime = " +
        //                    JSON.stringify(this.composite_datetime));
        this.sendValueToField(this.composite_datetime);
        this.setStaticTextValue(this.composite_datetime);
        this.setEditBoxValue(this.composite_datetime);
        this.applyMandatory();
    },

    timeValueChangedFromWidget: function (e) {
        // Titanium.API.trace("timeValueChangedFromWidget: e: "
        //                    + JSON.stringify(e));
        var timevalue = e.value;
        this.composite_datetime.hours(timevalue.getHours());
        this.composite_datetime.minutes(timevalue.getMinutes());
        this.composite_datetime.seconds(timevalue.getSeconds()); // irrelevant, probably
        // Titanium.API.trace("timeValueChangedFromWidget: composite_datetime = "
        //                    + JSON.stringify(this.composite_datetime));
        this.sendValueToField(this.composite_datetime);
        this.setStaticTextValue(this.composite_datetime);
        this.setEditBoxValue(this.composite_datetime);
        this.applyMandatory();
    },

    datetimeValueChangedFromWidget: function (e) {
        // e.source is of type TiUIPicker
        var datevalue = e.source.value,
            momentvalue = moment(datevalue);
        // Titanium.API.trace("datetimeValueChangedFromWidget: momentvalue = "
        //                    + JSON.stringify(momentvalue));
        this.sendValueToField(momentvalue);
        this.setStaticTextValue(momentvalue);
        this.setEditBoxValue(momentvalue);
        this.applyMandatory();
    },

    editChanged: function (e) {
        // If you're thinking "why update the field after every keystroke?",
        // it's so that things like the availability of the "Next" button
        // work properly. The "corrected" value is only written
        // back to the visible edit box when focus is lost (see below).
        var momentvalue = this.textToMoment(e.source.value);
        // Titanium.API.trace("editChanged: momentvalue = " +
        //                    JSON.stringify(momentvalue));
        this.sendValueToField(momentvalue);
        this.setStaticTextValue(momentvalue);
        this.composite_datetime = momentvalue;
        this.applyMandatory();
        return momentvalue; // used by editFocusLost
    },

    editFocusLost: function (e) {
        var momentvalue = this.editChanged(e);
        // ... and write it back:
        // e.source.value = this.momentToText(momentvalue);
        this.setEditBoxValue(momentvalue);
        this.setWidgetValue(momentvalue);
    },

    setWidgetValue: function (momentvalue) {
        if (!this.props.useWidgets || this.props.readOnly) {
            return;
        }
        var datevalue = this.momentToDate(momentvalue);
        // Titanium.API.trace("setWidgetValue: datevalue = " +
        //                    JSON.stringify(datevalue));
        if (this.separateTime) {
            this.timepicker.setValue(datevalue);
            this.datepicker.setValue(datevalue);
        } else {
            this.datetimepicker.setValue(datevalue);
        }
    },

    setStaticTextValue: function (momentvalue) {
        if (!this.date_as_text) {
            return;
        }
        this.date_as_text.setText(this.momentToPrettyText(momentvalue));
    },

    setEditBoxValue: function (momentvalue) {
        if (!this.editbox) {
            return;
        }
        this.editbox.setValue(this.momentToText(momentvalue));
    },

    setToNow: function () {
        var momentvalue = moment();
        this.setWidgetValue(momentvalue);
        this.setStaticTextValue(momentvalue);
        this.sendValueToField(momentvalue);
        this.setEditBoxValue(momentvalue);
        this.applyMandatory();
    },

    nullDisplayMoment: function () {
        // What does a NULL date/time look like on the widgets?
        // ... The current date/time? No, confusing with neonates.
        // ... 1 Jan 1900?
        return moment("19000101", "YYYYMMDD");
    },

    setToNull: function () {
        var platform = require('lib/platform');
        if (!platform.android) {
            /* AVOID THIS ON ANDROID - MAKES THE NULL INDICATOR FLASH ON, THEN
             * OFF, AS THE WIDGET RESPONDS TO SOMETHING AND RESETS THE VALUE
             * TO THE CURRENT DATE/TIME. */
            this.setWidgetValue(this.nullDisplayMoment());
        }
        this.setStaticTextValue(null);
        this.sendValueToField(null);
        this.setEditBoxValue(null);
        this.applyMandatory();
    },

    textToMoment: function (text) {
        if (!text) {
            return null;
        }
        var momentvalue = moment(text);
        if (!momentvalue || !momentvalue.isValid()) {
            return null;
        }
        return momentvalue;
    },

    momentToText: function (momentvalue) {
        if (momentvalue === null) {
            return "";
        }
        var UICONSTANTS = require('common/UICONSTANTS');
        if (this.props.showTime) {
            return momentvalue.format(
                UICONSTANTS.QUESTIONNAIRE_DATETIME_FORMAT
            );
        }
        return momentvalue.format(UICONSTANTS.QUESTIONNAIRE_DATE_FORMAT);
    },

    momentToPrettyText: function (momentvalue) {
        var text = this.momentToText(momentvalue);
        return text || "?";
    },

    momentToDate: function (momentvalue) {
        // convert from moment to Date.
        var conversion = require('lib/conversion');
        return conversion.momentToDateStrippingTimezone(
            momentvalue === null ?
                    this.nullDisplayMoment() :
                    momentvalue
        );
    },

    sendValueToField: function (momentvalue) {
        this.questionnaire.setFieldValue(this.field, momentvalue);
    },

    getRawFieldValue: function () {
        // returns a moment
        return this.questionnaire.getFieldValue(this.field);
    },

    isInputRequired: function () {
        return this.mandatory && this.getRawFieldValue() === null;
    },

    applyMandatory: function () {
        var input_required = this.isInputRequired(), // null and mandatory
            UICONSTANTS;
        // Validity indicator
        if (input_required) {
            this.indicator.setRequired();
        } else if (this.getRawFieldValue() === null) {
            this.indicator.setNullButOptional();
        } else {
            this.indicator.clear();
        }
        // Text box background colour
        if (this.editbox) {
            UICONSTANTS = require('common/UICONSTANTS');
            this.editbox.setBackgroundColor(input_required ?
                    UICONSTANTS.ANSWER_BACKGROUND_COLOUR_REQUIRED :
                    (this.props.readOnly ?
                            UICONSTANTS.ANSWER_BACKGROUND_COLOUR_READONLY :
                            UICONSTANTS.ANSWER_BACKGROUND_COLOUR
                    )
                );
        }
    },

    setMandatory: function (mandatory) {
        this.mandatory = mandatory;
        this.applyMandatory();
    },

    cleanup: function () {
        if (this.dateListener) {
            this.datepicker.removeEventListener("click", this.dateListener);
            this.dateListener = null;
        }
        if (this.timeListener) {
            this.timepicker.removeEventListener("click", this.timeListener);
            this.timeListener = null;
        }
        if (this.datetimeListener) {
            this.datetimepicker.removeEventListener("click",
                                                    this.datetimeListener);
            this.datetimeListener = null;
        }
        if (this.offerNowListener) {
            this.offerNowButton.removeEventListener("click",
                                                    this.offerNowListener);
            this.offerNowListener = null;
        }
        if (this.offerNullListener) {
            this.offerNullButton.removeEventListener("click",
                                                     this.offerNullListener);
            this.offerNullListener = null;
        }
        this.datepicker = null;
        this.timepicker = null;
        this.datetimepicker = null;
        this.offerNowButton = null;
        this.offerNullButton = null;
        this.indicator.cleanup();
        this.indicator = null;
        this.date_as_text = null;
        if (this.editChangedListener) {
            this.editbox.removeEventListener('change',
                                             this.editChangedListener);
            this.editChangedListener = null;
        }
        if (this.editFocusLostListener) {
            this.editbox.removeEventListener('blur',
                                             this.editFocusLostListener);
            this.editFocusLostListener = null;
        }
        this.editbox = null;
    }

});
module.exports = QuestionDateTime;
