// QuestionCountdown.js

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

/*jslint node: true, newcap: true, plusplus: true */
"use strict";
/*global Titanium, L */

var qcommon = require('questionnairelib/qcommon');
var lang = require('lib/lang');

function QuestionCountdown(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        self = this;

    qcommon.setDefaultProperty(props, "seconds", 0);
    // other properties:
    //      text
    qcommon.QuestionElementBase.call(this, props); // call base constructor

    if (props.seconds < 0) {
        throw new Error("Negative start value passed to QuestionCountdown");
    }

    this.running = false;
    this.duration_seconds = props.seconds;
    this.seconds = props.seconds;
    this.timer = null;
    this.bingPlayer = Titanium.Media.createSound({
        url: UICONSTANTS.SOUND_COUNTDOWN_FINISHED,
        allowBackground: true,
        volume: 1.0
    });

    this.tiview = Titanium.UI.createView({
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        width: Titanium.UI.SIZE,
        height: Titanium.UI.SIZE,
        layout: 'horizontal',
        touchEnabled: true
    });

    this.countdown = Titanium.UI.createLabel({
        left: UICONSTANTS.SPACE,
        center: {y: '50%'},
        textAlign: Titanium.UI.TEXT_ALIGNMENT_LEFT,
        font: UICONSTANTS.getQuestionnaireFont(),
        color: UICONSTANTS.QUESTION_COLOUR,
        text: props.text,
        touchEnabled: false
    });

    this.startButton = Titanium.UI.createButton({
        title: qcommon.processButtonTextForIos(L("start")),
        color: (
            props.readOnly ?
                    UICONSTANTS.QUESTIONNAIRE_READONLY_BUTTON_TEXT_COLOR :
                    UICONSTANTS.QUESTIONNAIRE_BUTTON_TEXT_COLOR
        )
    });

    this.stopButton = Titanium.UI.createButton({
        left: UICONSTANTS.SPACE,
        title: qcommon.processButtonTextForIos(L("stop")),
        color: (
            props.readOnly ?
                    UICONSTANTS.QUESTIONNAIRE_READONLY_BUTTON_TEXT_COLOR :
                    UICONSTANTS.QUESTIONNAIRE_BUTTON_TEXT_COLOR
        )
    });

    this.resetButton = Titanium.UI.createButton({
        left: UICONSTANTS.SPACE,
        title: qcommon.processButtonTextForIos(L("reset")),
        color: (
            props.readOnly ?
                    UICONSTANTS.QUESTIONNAIRE_READONLY_BUTTON_TEXT_COLOR :
                    UICONSTANTS.QUESTIONNAIRE_BUTTON_TEXT_COLOR
        )
    });

    if (!props.readOnly) {
        this.startListener = function () { self.start(); };
        this.startButton.addEventListener('click', this.startListener);
        this.stopListener = function () { self.stop(); };
        this.stopButton.addEventListener('click', this.stopListener);
        this.resetListener = function () { self.reset(); };
        this.resetButton.addEventListener('click', this.resetListener);
    }

    this.tiview.add(this.startButton);
    this.tiview.add(this.countdown);
    this.tiview.add(this.stopButton);
    this.tiview.add(this.resetButton);

    this.update_display();
}
lang.inheritPrototype(QuestionCountdown, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionCountdown, {
    tick: function () {
        --this.seconds;
        this.update_display();
        if (this.seconds <= 0) {
            this.stop();
            this.bingPlayer.play();
        }
    },

    start: function () {
        if (this.running || this.seconds <= 0) {
            return;
        }
        this.running = true;
        var self = this;
        this.timer = setInterval(function () { self.tick(); }, 1000);
        // ... second parameter is period in ms
    },

    stop: function () {
        if (!this.running) {
            return;
        }
        this.running = false;
        clearInterval(this.timer);
    },

    reset: function () {
        var was_running = this.running;
        this.stop();
        this.seconds = this.duration_seconds;
        if (was_running) {
            this.start();
        }
        this.update_display();
    },

    update_display: function () {
        var minutes = Math.floor(this.seconds / 60),
            sec_only = this.seconds % 60,
            sectext = (sec_only < 10) ? "0" + sec_only : sec_only;
        this.countdown.setText(minutes + ":" + sectext +
                               (this.seconds === 0 ? " -- FINISHED" : ""));
    },

    // Views don't have close events -- only windows. So we'll use the
    // Questionnaire framework to clean up:
    onClose: function () {
        this.stop(); // clean up any timers outstanding
    },

    cleanup: function () {
        if (this.startListener) {
            this.startButton.removeEventListener("click", this.startListener);
            this.startListener = null;
        }
        if (this.stopListener) {
            this.stopButton.removeEventListener("click", this.stopListener);
            this.stopListener = null;
        }
        if (this.resetListener) {
            this.resetButton.removeEventListener("click", this.resetListener);
            this.resetListener = null;
        }
        this.startButton = null;
        this.stopButton = null;
        this.resetButton = null;
        this.bingPlayer = null;
        this.countdown = null;
    }

});
module.exports = QuestionCountdown;
