// WhiskerMenu.js

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

/*jslint node: true, newcap: true, unparam: true, plusplus: true */
"use strict";
/*global Titanium, L */

module.exports = function WhiskerMenu() {

    var MenuWindow = require('menulib/MenuWindow'),
        uifunc = require('lib/uifunc'),
        UICONSTANTS = require('common/UICONSTANTS'),
        data,
        self,
        wait;

    function connect() {
        var whisker = require('lib/whisker');
        wait.show();
        whisker.connect();
        wait.hide();
    }

    function disconnect() {
        var whisker = require('lib/whisker');
        wait.show();
        whisker.disconnect();
        wait.hide();
    }

    function configure() {
        var conf_whisker = require('screen/configure_whisker');
        conf_whisker.configure();
    }

    function test_latency() {
        var whisker = require('lib/whisker'),
            i,
            pings = 10,
            total = 0,
            latency,
            avg_latency;
        if (!whisker.isConnected()) {
            whisker.alert("Not connected!");
            return;
        }
        wait.show();
        for (i = 0; i < pings; i += 1) {
            latency = whisker.getNetworkLatencyMs();
            if (latency === null) {
                whisker.alert("Failed to test network latency");
                wait.hide();
                return;
            }
            total += latency;
        }
        avg_latency = total / pings;
        wait.hide();
        whisker.alert("Average round-trip latency over " + pings +
                      " pings was " + avg_latency + " ms");
    }

    data = [
        {
            notIfLocked: true,
            maintitle: L('whisker_connect'),
            func: connect
        },
        {
            notIfLocked: true,
            maintitle: L('whisker_diconnect'),
            func: disconnect
        },
        {
            notIfLocked: true,
            maintitle: L('whisker_test_latency'),
            func: test_latency
        },
        {
            notIfLocked: true,
            maintitle: L('whisker_configure'),
            func: configure
        }
    ];

    self = new MenuWindow({
        title: L('menutitle_whisker'),
        icon: UICONSTANTS.ICON_WHISKER,
        data: data
    });

    wait = uifunc.createWait({ window: self.tiview });

    return self;
};
