// QuestionAudioPlayer.js

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

/*jslint node: true */
"use strict";
/*global Titanium */

var qcommon = require('questionnairelib/qcommon'),
    lang = require('lib/lang');

function QuestionAudioPlayer(props) {

    var UICONSTANTS = require('common/UICONSTANTS'),
        self = this;
    qcommon.requireProperty(props, "filename", "QuestionAudio");
    qcommon.setDefaultProperty(props, "volume", 1.0);
    qcommon.QuestionElementBase.call(this, props); // call base constructor


    this.sound = Titanium.Media.createSound({
        url: props.filename,
        // filename should begin with "/" or it searches Resources/lib/FILENAME
        // (= relative to this .js file...)
        allowBackground: true,
        volume: props.volume
    });
    this.finishedListener = function () { self.soundFinished(); };
    this.sound.addEventListener("complete", this.finishedListener);

    this.tiview = Titanium.UI.createButton({
        backgroundImage: UICONSTANTS.ICON_SPEAKER,
        backgroundSelectedImage: UICONSTANTS.ICON_SPEAKER_T,
        height: UICONSTANTS.ICONSIZE,
        width: UICONSTANTS.ICONSIZE,
        left: props.left,
        right: props.right,
        top: props.top,
        bottom: props.bottom,
        center: props.center,
        touchEnabled: true
    });
    this.touchedListener = function () { self.touched(); };
    this.tiview.addEventListener("click", this.touchedListener);

    this.playing = false;
}
lang.inheritPrototype(QuestionAudioPlayer, qcommon.QuestionElementBase);
lang.extendPrototype(QuestionAudioPlayer, {

    touched: function () {
        if (this.playing) {
            this.playing = false;
            this.sound.stop(); // also resets the position
            this.setPictureSpeaker();
        } else {
            this.playing = true;
            this.sound.reset(); // just in case...
            this.sound.play();
            this.setPictureSpeakerPlaying();
        }
    },

    soundFinished: function () {
        this.playing = false;
        this.setPictureSpeaker();
    },

    setPictureSpeaker: function () {
        var UICONSTANTS = require('common/UICONSTANTS');
        this.tiview.setBackgroundImage(UICONSTANTS.ICON_SPEAKER);
        this.tiview.setBackgroundSelectedImage(UICONSTANTS.ICON_SPEAKER_T);
    },

    setPictureSpeakerPlaying: function () {
        var UICONSTANTS = require('common/UICONSTANTS');
        this.tiview.setBackgroundImage(UICONSTANTS.ICON_SPEAKER_PLAYING);
        this.tiview.setBackgroundSelectedImage(
            UICONSTANTS.ICON_SPEAKER_PLAYING_T
        );
    },

    onClose: function () {
        if (this.playing) {
            this.playing = false;
            this.sound.stop();
        }
    },

    cleanup: function () {
        this.sound.removeEventListener("click", this.finishedListener);
        this.finishedListener = null;
        this.tiview.removeEventListener("click", this.touchedListener);
        this.touchedListener = null;
        this.sound = null;
    }

});
module.exports = QuestionAudioPlayer;
