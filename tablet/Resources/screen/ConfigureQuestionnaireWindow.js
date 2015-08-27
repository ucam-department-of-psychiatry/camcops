// ConfigureQuestionnaireWindow.js

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

/*jslint node: true, newcap: true, plusplus: true */
"use strict";
/*global Titanium, L */

var OFFER_SIZES = [50, 75, 100, 125, 150, 175, 200];

function makeSizeButton(percent) {
    var UICONSTANTS = require('common/UICONSTANTS'),
        qcommon = require('questionnairelib/qcommon');
    return Titanium.UI.createButton({
        left: 0,
        top: 0,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE,
        color: UICONSTANTS.QUESTIONNAIRE_BUTTON_TEXT_COLOR,
        // backgroundColor: UICONSTANTS.QUESTIONNAIRE_BUTTON_BG_COLOR,
        title: qcommon.processButtonTextForIos(percent + "%")
    });
}

function makeSizeListener(self, percent) {
    return function () {
        self.setPercent(percent);
    };
}

function createLabel(text, sizeVaries) {
    var UICONSTANTS = require('common/UICONSTANTS');
    return Titanium.UI.createLabel({
        text: text,
        left: UICONSTANTS.SPACE,
        font: UICONSTANTS.ROW_TITLE_FONT,
        color: (sizeVaries ?
                UICONSTANTS.READONLY_ANSWER_COLOUR :
                UICONSTANTS.QUESTION_COLOUR
        )
    });
}

function ConfigureQuestionnaireWindow() {

    var uifunc = require('lib/uifunc'),
        storedvars = require('table/storedvars'),
        UICONSTANTS = require('common/UICONSTANTS'),
        cancelbutton_left = uifunc.buttonPosition(0),
        heading_left = uifunc.buttonPosition(1),
        savebutton_right = uifunc.buttonPosition(0),
        heading_right = uifunc.buttonPosition(1),
        self = this,
        title = uifunc.createMenuTitleText({
            left: heading_left,
            right: heading_right,
            text: L('t_configure_questionnaire'),
            textAlign: Titanium.UI.TEXT_ALIGNMENT_CENTER,
            color: UICONSTANTS.QUESTIONNAIRE_TITLE_COLOUR
        }),
        toprow = Titanium.UI.createView({
            height: UICONSTANTS.ICONSIZE, // not SIZE; on very narrow displays,
            // it breaks a bit. Truncate instead!
            width: Titanium.UI.FILL
            // backgroundColor: COLOURS.YELLOW,
        }),
        contentview = Titanium.UI.createScrollView({
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL,
            layout: 'vertical',
            contentHeight: 'auto',
            scrollType: 'vertical',
            showVerticalScrollIndicator: true
        }),
        label_questionnaireTextSizePercent = createLabel(
            L('label_questionnaire_text_size_percent')
        ),
        buttonview = Titanium.UI.createView({
            top: 0,
            left: 0,
            height: Titanium.UI.SIZE,
            width: Titanium.UI.FILL,
            layout: 'horizontal'
        }),
        i,
        percent,
        button,
        listener,
        demotext = L('demo_text_for_text_size'),
        mainview = Titanium.UI.createView({
            height: Titanium.UI.FILL,
            width: Titanium.UI.FILL,
            layout: 'vertical',
            backgroundColor: UICONSTANTS.QUESTIONNAIRE_BG_COLOUR_CONFIG
        });

    this.tiview = uifunc.createMenuWindow();

    this.savebutton = uifunc.createOkButton({right: savebutton_right});
    this.saveListener = function () { self.save(); };
    this.savebutton.addEventListener('click', this.saveListener);

    this.cancelbutton = uifunc.createCancelButton({left: cancelbutton_left});
    this.cancelListener = function () { self.close(); };
    this.cancelbutton.addEventListener('click', this.cancelListener);
    this.tiview.addEventListener('android:back', this.cancelListener);

    toprow.add(title);
    toprow.add(this.savebutton);
    toprow.add(this.cancelbutton);

    contentview.add(label_questionnaireTextSizePercent);

    this.numberLabel_questionnaireTextSizePercent = Titanium.UI.createLabel({
        top: 0,
        center: {x: "50%"},
        touchEnabled: false,
        font: UICONSTANTS.getQuestionnaireFont(),
        color: UICONSTANTS.QUESTION_COLOUR
    });
    contentview.add(this.numberLabel_questionnaireTextSizePercent);

    this.slider_questionnaireTextSizePercent = Titanium.UI.createSlider({
        top: 0,
        left: 0,
        width: Titanium.UI.FILL,
        height: Titanium.UI.SIZE,
        min: 25,
        max: 300,
        minRange: 25,
        maxRange: 300,
        value: storedvars.questionnaireTextSizePercent.getValue()
    });
    contentview.add(this.slider_questionnaireTextSizePercent);

    this.sizeButtons = [];
    this.sizeButtonListeners = [];
    for (i = 0; i < OFFER_SIZES.length; ++i) {
        percent = OFFER_SIZES[i];
        button = makeSizeButton(percent);
        if (i > 0) {
            buttonview.add(uifunc.createHorizontalSpacer());
        }
        buttonview.add(button);
        listener = makeSizeListener(self, percent);
        button.addEventListener('click', listener);
        this.sizeButtons.push(button);
        this.sizeButtonListeners.push(listener);
    }
    contentview.add(buttonview);

    contentview.add(createLabel(L('label_normal_text')));
    this.demo_label_1 = createLabel(demotext, true);
    this.demo_label_2 = createLabel(demotext, true);
    this.demo_label_3 = createLabel(demotext, true);
    this.demo_label_4 = createLabel(demotext, true);
    contentview.add(this.demo_label_1);
    contentview.add(this.demo_label_2);
    contentview.add(this.demo_label_3);
    contentview.add(this.demo_label_4);

    contentview.add(createLabel(L('label_big_text')));
    this.demo_label_5 = createLabel(demotext, true);
    this.demo_label_6 = createLabel(demotext, true);
    this.demo_label_7 = createLabel(demotext, true);
    this.demo_label_8 = createLabel(demotext, true);
    contentview.add(this.demo_label_5);
    contentview.add(this.demo_label_6);
    contentview.add(this.demo_label_7);
    contentview.add(this.demo_label_8);

    this.setDemoFontSizes();
    this.sliderListener = function () { self.setDemoFontSizes(); };
    this.slider_questionnaireTextSizePercent.addEventListener(
        'touchend',
        this.sliderListener
    );
    this.slider_questionnaireTextSizePercent.addEventListener(
        'singletap',
        this.sliderListener
    );

    mainview.add(toprow);
    mainview.add(uifunc.createVerticalSpacer());
    mainview.add(uifunc.createQuestionnaireRule());
    mainview.add(uifunc.createVerticalSpacer());
    mainview.add(contentview);

    this.tiview.add(mainview);
}
ConfigureQuestionnaireWindow.prototype = {

    open: function () {
        this.tiview.open();
    },

    cleanup: function () {
        var i;
        this.savebutton.removeEventListener('click', this.saveListener);
        this.saveListener = null;
        this.savebutton = null;

        this.cancelbutton.removeEventListener('click', this.cancelListener);
        this.tiview.removeEventListener('android:back', this.cancelListener);
        this.cancelListener = null;
        this.cancelbutton = null;

        this.slider_questionnaireTextSizePercent.removeEventListener(
            'touchend',
            this.sliderListener
        );
        this.slider_questionnaireTextSizePercent.removeEventListener(
            'singletap',
            this.sliderListener
        );
        this.sliderListener = null;
        this.slider_questionnaireTextSizePercent = null;

        for (i = 0; i < this.sizeButtons.length; ++i) {
            this.sizeButtons[i].removeEventListener(
                'click',
                this.sizeButtonListeners[i]
            );
            this.sizeButtonListeners[i] = null;
            this.sizeButtons[i] = null;
        }

        this.numberLabel_questionnaireTextSizePercent = null;
        this.demo_label_1 = null;
        this.demo_label_2 = null;
        this.demo_label_3 = null;
        this.demo_label_4 = null;
        this.demo_label_5 = null;
        this.demo_label_6 = null;
        this.demo_label_7 = null;
        this.demo_label_8 = null;

        this.tiview = null;
    },

    close: function () {
        this.tiview.close();
        this.cleanup();
    },

    save: function () {
        var storedvars = require('table/storedvars'),
            textSizePercent = parseInt(
                this.slider_questionnaireTextSizePercent.value,
                10
            );
        storedvars.questionnaireTextSizePercent.setValue(textSizePercent);
        this.close(); // should call cleanup (will also destroy window elements)
    },

    setPercent: function (percent) {
        this.slider_questionnaireTextSizePercent.setValue(percent);
        this.setDemoFontSizes();
    },

    setDemoFontSizes: function () {
        var UICONSTANTS = require('common/UICONSTANTS'),
            percent = parseInt(this.slider_questionnaireTextSizePercent.value,
                               10);
        this.numberLabel_questionnaireTextSizePercent.setText(
            percent.toString()
        );
        this.demo_label_1.setFont(
            UICONSTANTS.getVariableFontSpecifyingPercent(
                UICONSTANTS.QUESTIONNAIRE_BASE_FONT_SIZE,
                false,
                false,
                percent
            )
        );
        this.demo_label_2.setFont(
            UICONSTANTS.getVariableFontSpecifyingPercent(
                UICONSTANTS.QUESTIONNAIRE_BASE_FONT_SIZE,
                false,
                true,
                percent
            )
        );
        this.demo_label_3.setFont(
            UICONSTANTS.getVariableFontSpecifyingPercent(
                UICONSTANTS.QUESTIONNAIRE_BASE_FONT_SIZE,
                true,
                false,
                percent
            )
        );
        this.demo_label_4.setFont(
            UICONSTANTS.getVariableFontSpecifyingPercent(
                UICONSTANTS.QUESTIONNAIRE_BASE_FONT_SIZE,
                true,
                true,
                percent
            )
        );
        this.demo_label_5.setFont(
            UICONSTANTS.getVariableFontSpecifyingPercent(
                UICONSTANTS.QUESTIONNAIRE_BIG_FONT_SIZE,
                false,
                false,
                percent
            )
        );
        this.demo_label_6.setFont(
            UICONSTANTS.getVariableFontSpecifyingPercent(
                UICONSTANTS.QUESTIONNAIRE_BIG_FONT_SIZE,
                false,
                true,
                percent
            )
        );
        this.demo_label_7.setFont(
            UICONSTANTS.getVariableFontSpecifyingPercent(
                UICONSTANTS.QUESTIONNAIRE_BIG_FONT_SIZE,
                true,
                false,
                percent
            )
        );
        this.demo_label_8.setFont(
            UICONSTANTS.getVariableFontSpecifyingPercent(
                UICONSTANTS.QUESTIONNAIRE_BIG_FONT_SIZE,
                true,
                true,
                percent
            )
        );
        // iOS bug: combination of bold + italic gives just bold (2013-05-24)
    }

};
module.exports = ConfigureQuestionnaireWindow;
