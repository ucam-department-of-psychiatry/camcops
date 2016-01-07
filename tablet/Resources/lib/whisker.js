// whisker.js

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

// *** How to disable Nagle algorithm (i.e. use TCP_NODELAY)?

/*jslint node: true */
"use strict";
/*global Titanium */

var CMD_PING_ACKNOWLEDGED = "PingAcknowledged",
    CMD_REPORTNAME = "ReportName",
    CMD_RESETCLOCK = "ResetClock",
    CMD_TEST_NETWORK_LATENCY = "TestNetworkLatency",
    CMD_TIMESTAMPS_ON = "TimeStamps on",
    code = null,
    CODE_REGEX = /^Code: (\S+)$/,
    connected = false,
    disconnect, // predeclare function
    EVENT_REGEX = /^Event: ([\s\S]+) \[(\d+)\]$/, // with timestamps
    imm_connected = false,
    immport = null,
    IMMPORT_REGEX = /^ImmPort: ([0-9]+)$/,
    imm_socket = null,
    main_connected = false,
    main_socket = null,
    MAX_CHUNK_SIZE = 1024,
    // MINIMUM_WHISKER_VERSION = 4.6,
    NEWLINE = "\n",
    PING_REGEX = /^Ping \[(\d+)\]$/, // with timestamps
    queue = "",
    resetClock, // predeclare function
    SUCCESS = "Success",
    SUCCESS_WITH_TIMESTAMPS_REGEX = /^Success \[\d+\]$/;

// ============================================================================
// Common
// ============================================================================

function alert(msg) {
    var uifunc = require('lib/uifunc');
    uifunc.alert(msg, "CamCOPS <> Whisker");
}
exports.alert = alert;

// ============================================================================
// Immediate socket internals
// ============================================================================

function send_imm(msg) {
    Titanium.API.debug("whisker: send_imm: " + msg);
    // Blocking:
    imm_socket.write(Titanium.createBuffer({
        value: msg + NEWLINE,
        type: Titanium.Codec.CHARSET_ASCII
    }));
}

function get_imm_reply() {
    var buffer = Titanium.createBuffer({length: MAX_CHUNK_SIZE}),
        numbytes = imm_socket.read(buffer), // blocking
        reply;
    if (numbytes < MAX_CHUNK_SIZE) {
        buffer.setLength(numbytes);
        // http://docs.appcelerator.com/titanium/3.0/#!/guide/Buffer_and_Codec
        // http://docs.appcelerator.com/titanium/3.0/#!/api/Titanium.Buffer
    }
    reply = buffer.toString().split(NEWLINE)[0];
    Titanium.API.debug("whisker: get_imm_reply: " + reply);
    return reply;
}

function send_imm_get_reply(msg) {
    if (!imm_connected) {
        return null;
    }
    send_imm(msg);
    return get_imm_reply();
}

function sendGetSuccess(command) {
    var reply = send_imm_get_reply(command),
        success = (SUCCESS_WITH_TIMESTAMPS_REGEX.test(reply) ||
                   reply === SUCCESS);
    Titanium.API.debug("whisker: sendGetSuccess: returning " +
                       success);
    return success;
}
exports.sendGetSuccess = sendGetSuccess;

function reportName(name) {
    return sendGetSuccess(CMD_REPORTNAME + " " + name);
}
exports.reportName = reportName;

function defaultClientName() {
    var VERSION = require('common/VERSION');
    return "CamCOPS " + VERSION.CAMCOPS_VERSION;
}

function on_imm_connected() {
    var EVENTS = require('common/EVENTS'),
        msg;
    imm_connected = true;
    connected = true;
    Titanium.API.info('whisker: immediate socket connected');
    if (!sendGetSuccess("Link " + code)) {
        msg = "whisker: Failed to link immediate socket";
        Titanium.API.error(msg);
        alert(msg);
        disconnect();
        return;
    }
    sendGetSuccess(CMD_TIMESTAMPS_ON);
    resetClock();
    reportName(defaultClientName());
    Titanium.App.fireEvent(EVENTS.WHISKER_STATUS_CHANGED, {});
}

function connect_imm(port) {
    var storedvars = require('table/storedvars'),
        host = storedvars.whiskerHost.getValue(),
        timeoutMs = storedvars.whiskerTimeoutMs.getValue(),
        msg;
    if (imm_connected) {
        return;
    }
    imm_socket = Titanium.Network.Socket.createTCP({
        host: host,
        port: port,
        timeout: timeoutMs,
        connected: on_imm_connected,
        error: function (e) {
            msg = ('whisker: immediate socket connection error (' +
                   e.errorCode + '): ' + e.error);
            Titanium.API.warn(msg);
            alert(msg);
        }
    });
    Titanium.API.info("whisker: connecting immediate socket to " +
                      host + ":" + port);
    imm_socket.connect();
}

function disconnect_imm() {
    if (!imm_connected) {
        return;
    }
    try {
        imm_socket.close();
    } catch (ex) {
        Titanium.API.error(ex);
        alert(ex);
    }
    imm_connected = false;
    imm_socket = null;
}

// ============================================================================
// Main socket internals
// ============================================================================

function main_write_callback(e) {
    // e contains: bytesProcessed, code, error, source, success
    if (e.success) {
        return;
    }
    var msg = 'whisker: main socket write error (' + e.code + '): ' + e.error;
    Titanium.API.error(msg);
    alert(msg);
}

function send_main(msg) {
    if (!main_connected) {
        return;
    }
    Titanium.API.debug("whisker: send_main: " + msg);

    // METHOD 1: nonblocking (asynchronous)
    /*
    Titanium.Stream.write(
        main_socket, // stream
        Titanium.createBuffer({
            value: msg + NEWLINE,
            type: Titanium.Codec.CHARSET_ASCII,
        }), // buffer
        // can omit offset and length parameters
        main_write_callback // resultsCallback
    );
    */

    // Probably best not to use a stream? We want to be sure that
    // the data has been sent prior to any other commands, inc.
    // subsequent commands sent on the immediate socket, so we
    // should probably use a blocking call.

    // METHOD 2: blocking (synchronous)
    main_socket.write(Titanium.createBuffer({
        value: msg + NEWLINE,
        type: Titanium.Codec.CHARSET_ASCII
    }));
}

function process_incoming_event(event, whisker_timestamp_ms, now) {
    var EVENTS = require('common/EVENTS');
    Titanium.API.info("whisker EVENT: " + event +
                      " (timestamp: " + whisker_timestamp_ms + " ms)");
    Titanium.App.fireEvent(EVENTS.WHISKER_EVENT, {
        event: event,
        whisker_timestamp_ms: whisker_timestamp_ms,
        moment_timestamp: now
    });
}

function process_incoming_line(msg) {
    var match,
        processed = false,
        moment;
    Titanium.API.info('whisker: main received: ' + msg);
    if (!imm_connected) {
        // Only bother checking these before we have an immediate port.
        match = IMMPORT_REGEX.exec(msg);
        if (match) {
            immport = parseInt(match[1], 10);
            processed = true;
        }
        match = CODE_REGEX.exec(msg);
        if (match) {
            code = match[1];
            processed = true;
        }
        if (immport && code) {
            connect_imm(immport);
        }
        if (processed) {
            return;
        }
    }
    if (PING_REGEX.test(msg)) {
        send_main(CMD_PING_ACKNOWLEDGED);
        return;
    }
    match = EVENT_REGEX.exec(msg);
    if (match) {
        moment = require('lib/moment');
        process_incoming_event(match[1], match[2], moment());
    }
}

function process_incoming_message(msg) {
    if (!msg) {
        return;
    }
    msg = queue + msg;
    var lines = msg.split(NEWLINE),
        nlines = lines.length,
        i,
        lastline;
    for (i = 0; i < nlines - 1; i += 1) { // skip the very last one
        process_incoming_line(lines[i]);
    }
    lastline = lines[nlines - 1];
    queue = lastline; // might be blank (if there was a "\n" terminator) or not
}

function receive_main(e) {
    var msg,
        received;
    if (e.bytesProcessed === -1) {
        // Error / EOF on socket. Do any cleanup here.
        disconnect();
        msg = 'whisker: receive_main(), end of stream (socket closed)';
        Titanium.API.warn(msg);
        alert(msg);
        return;
    }
    try {
        if (e.buffer) {
            received = e.buffer.toString();
            process_incoming_message(received);
        } else {
            msg = 'whisker: receive_main called with no buffer!';
            Titanium.API.error(msg);
            alert(msg);
        }
    } catch (ex) {
        Titanium.API.error(ex);
        alert(ex);
    }
}

function on_main_connected(e) {
    main_connected = true;
    Titanium.API.info('whisker: main socket connected');
    Titanium.Stream.pump(e.socket, // input stream
                         receive_main, // handler
                         MAX_CHUNK_SIZE, // maxChunkSize,
                         true); // isAsync
}

function connect_main() {
    var storedvars = require('table/storedvars'),
        host = storedvars.whiskerHost.getValue(),
        port = storedvars.whiskerPort.getValue(),
        timeoutMs = storedvars.whiskerTimeoutMs.getValue(),
        msg;
    if (main_connected) {
        return;
    }
    main_socket = Titanium.Network.Socket.createTCP({
        host: host,
        port: port,
        timeout: timeoutMs,
        connected: on_main_connected,
        error: function (e) {
            msg = ('whisker: main socket connection error (' +
                   e.errorCode + '): ' + e.error);
            Titanium.API.info(msg);
            alert(msg);
        }
    });
    Titanium.API.info("whisker: connecting main socket to " +
                      host + ":" + port);
    main_socket.connect();
}

function disconnect_main() {
    if (!main_connected) {
        return;
    }
    try {
        main_socket.close();
    } catch (ex) {
        Titanium.API.error(ex);
        alert(ex);
    }
    main_connected = false;
    main_socket = null;
}

// ============================================================================
// Public interface
// ============================================================================

function isConnected() {
    return connected;
}
exports.isConnected = isConnected;

function connect() {
    connect_main();
}
exports.connect = connect;

disconnect = function () {
    var EVENTS = require('common/EVENTS');
    disconnect_imm();
    disconnect_main();
    immport = null;
    code = null;
    connected = false;
    Titanium.App.fireEvent(EVENTS.WHISKER_STATUS_CHANGED, {});
};
exports.disconnect = disconnect;

function send(command) {
    send_main(command);
}
exports.send = send;

function sendGetReply(command) {
    return send_imm_get_reply(command);
}
exports.sendGetReply = sendGetReply;

resetClock = function () {
    sendGetSuccess(CMD_RESETCLOCK);
};
exports.resetClock = resetClock;

function getNetworkLatencyMs() {
    if (!connected) {
        return null;
    }
    var reply,
        failure = "whisker: server didn't follow Ping protocol",
        latency;
    reply = send_imm_get_reply(CMD_TEST_NETWORK_LATENCY);
    if (!PING_REGEX.test(reply)) {
        Titanium.API.error(failure);
        alert(failure);
        return null;
    }
    reply = send_imm_get_reply(CMD_PING_ACKNOWLEDGED);
    latency = parseInt(reply, 10);
    if (isNaN(latency)) {
        return null;
    }
    return latency;
}
exports.getNetworkLatencyMs = getNetworkLatencyMs;
