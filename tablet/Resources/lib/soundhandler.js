// soundhandler.js

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

var soundArray = [];

function getDurationOfSoundMs(sound) {
    var duration = sound.duration,
        platform = require('lib/platform');
    if (platform.android) {
        Titanium.API.trace("getDurationOfSoundMs: duration = " + duration +
                           " ms");
        return duration; // is in ms
    }
    if (platform.ios) {
        Titanium.API.trace("getDurationOfSoundMs: duration = " + duration +
                           " s");
        return Math.ceil(duration * 1000); // duration is in seconds
    }
    // unknown platform!
    Titanium.API.trace("getDurationOfSoundMs: duration = " + duration);
    return duration;
}
exports.getDurationOfSoundMs = getDurationOfSoundMs;

function loadSound(params) {
    if (params.volume === undefined) {
        params.volume = 1.0;
    }
    // other parameters:
    //      filename
    //      ... filename should begin with "/" or it searches
    //          Resources/lib/FILENAME (= relative to this .js file...)
    //      fnSoundComplete

    Titanium.API.trace("loadSound: filename = " + params.filename +
                       ", volume = " + params.volume);
    var sound,
        platform = require('lib/platform'),
        duration,
        KeyValuePair = require('lib/KeyValuePair');
    if (platform.android) {
        // ANDROID: sound duration is zero following
        // Titanium.Media.createSound();
        // ... http://developer.appcelerator.com/question/134063/sound-getduration-without-playing-the-audio-file-first
        // ... ... using the create-then-set-URL method doesn't help
        // ... so let's play silently!
        sound = Titanium.Media.createSound({
            url: params.filename,
            allowBackground: true,
            volume: 0.0,
        });
        sound.play();
        sound.stop(); // resets position to zero
        sound.setVolume(params.volume);
    } else {
        sound = Titanium.Media.createSound({
            url: params.filename,
            allowBackground: true,
            volume: params.volume,
        });
    }
    if (typeof params.fnSoundComplete === "function") {
        Titanium.API.trace("soundhandler.loadSound: adding fnSoundComplete " +
                           "for " + params.filename);
        sound.addEventListener("complete", params.fnSoundComplete);
        // *** PROBLEM (soundhandler.loadSound): it seems this "complete" event
        // intermittently fails to fire (iOS simulator). Consequently,
        // workaround...
        // Consequently, we'll operate predominantly by using the duration,
        // and keeping sound-playing in the Titanium code, using callbacks
        // based on duration in webviews.
    }
    sound.addEventListener("error", function (e) {
        Titanium.API.error("SOUND ERROR for " + params.filename + ": " +
                           JSON.stringify(e));
    });
    duration = getDurationOfSoundMs(sound);
    soundArray.push(new KeyValuePair(params.filename, sound));
    return duration;
}
exports.loadSound = loadSound;

function getSound(filename) {
    var lang = require('lib/lang'),
        sound = lang.kvpGetValue(soundArray, filename);
    if (!sound) {
        Titanium.API.error("Invalid sound! filename = " + filename);
    }
    return sound;
}

function setVolume(filename, volume) {
    Titanium.API.trace("setVolume: filename = " + filename + ", volume = " +
                       volume);
    var sound = getSound(filename);
    if (!sound) {
        return;
    }
    sound.setVolume(volume);
}
exports.setVolume = setVolume;

function playSound(filename, resetToStartFirst) {
    if (resetToStartFirst === undefined) {
        resetToStartFirst = true;
    }
    Titanium.API.trace("playSound: filename = " + filename);
    var sound = getSound(filename);
    if (!sound) {  // trace error will have been reported by getSound
        return;
    }
    if (resetToStartFirst) {
        Titanium.API.trace("playSound: reset to start");
        sound.reset();
    }
    sound.play();
}
exports.playSound = playSound;

function pauseSound(filename) {
    Titanium.API.trace("pauseSound: filename = " + filename);
    var sound = getSound(filename);
    if (!sound) {
        return;
    }
    sound.pause();
}
exports.pauseSound = pauseSound;

function stopSound(filename) {
    Titanium.API.trace("stopSound: filename = " + filename);
    var sound = getSound(filename);
    if (!sound) {
        return;
    }
    sound.stop();
}
exports.stopSound = stopSound;

function resetSound(filename) {
    Titanium.API.trace("resetSound: filename = " + filename);
    var sound = getSound(filename);
    if (!sound) {
        return;
    }
    sound.reset();
}
exports.resetSound = resetSound;

function getDurationMs(filename) {
    Titanium.API.trace("stopSound: filename = " + filename);
    var sound = getSound(filename);
    if (!sound) {
        return null;
    }
    return getDurationOfSoundMs(sound);
}
exports.getDurationMs = getDurationMs;

function unloadSound(filename) {
    var sound = getSound(filename),
        lang = require('lib/lang');
    if (!sound) {
        return;
    }
    sound.release(); // proably unnecessary
    lang.kvpRemoveByKey(soundArray, filename);
}
exports.unloadSound = unloadSound;

function unloadAllSounds() {
    var i;
    for (i = 0; i < soundArray.length; i += 1) {
        soundArray[i].value.release();
    }
    soundArray = []; // reset to empty
}
exports.unloadAllSounds = unloadAllSounds;
