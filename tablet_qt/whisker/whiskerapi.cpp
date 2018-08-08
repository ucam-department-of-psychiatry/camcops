/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#include "whiskerapi.h"
#include <QDebug>
#include "lib/convert.h"
#include "whisker/whiskerconstants.h"

using namespace whiskerconstants;

namespace whiskerapi {

// ============================================================================
// Private helper functions
// ============================================================================

QString onVal(bool on)
{
    return on ? VAL_ON : VAL_OFF;
}


// ============================================================================
// Helper structs
// ============================================================================

// ----------------------------------------------------------------------------
// Pen
// ----------------------------------------------------------------------------

Pen::Pen(int width, const QColor& colour, PenStyle style) :
    width(width),
    colour(colour),
    style(style)
{
}


QString Pen::whiskerOptionString() const
{
    const QStringList args{
        FLAG_PEN_COLOUR,
        QString::number(colour.red()),
        QString::number(colour.green()),
        QString::number(colour.blue()),
        FLAG_PEN_WIDTH,
        QString::number(width),
        FLAG_PEN_STYLE,
        PEN_STYLE_FLAGS[style],
    };
    return msgFromArgs(args);
}


// ----------------------------------------------------------------------------
// Brush
// ----------------------------------------------------------------------------

Brush::Brush(const QColor& colour, const QColor& bg_colour, bool opaque,
             BrushStyle style, BrushHatchStyle hatch_style) :
    colour(colour),
    bg_colour(bg_colour),
    opaque(opaque),
    style(style),
    hatch_style(hatch_style)
{
}


QString Brush::whiskerOptionString() const
{
    QStringList args{BRUSH_STYLE_FLAGS[style]};
    if (style == BrushStyle::Solid) {
        args.append(QString::number(colour.red()));
        args.append(QString::number(colour.green()));
        args.append(QString::number(colour.blue()));
    } else if (style == BrushStyle::Hatched) {
        args.append(BRUSH_HATCH_VALUES[hatch_style]);
        args.append(QString::number(colour.red()));
        args.append(QString::number(colour.green()));
        args.append(QString::number(colour.blue()));
        if (opaque) {
            args.append(FLAG_BRUSH_OPAQUE);
            args.append(FLAG_BRUSH_BACKGROUND);
            args.append(QString::number(bg_colour.red()));
            args.append(QString::number(bg_colour.green()));
            args.append(QString::number(bg_colour.blue()));
        } else {
            args.append(FLAG_BRUSH_TRANSPARENT);
        }
    }
    return msgFromArgs(args);
}


// ============================================================================
// Helper functions
// ============================================================================

bool onOffToBoolean(const QString& msg)
{
    return msg == VAL_ON;
}


QString quote(const QString& s)
{
    return QUOTE + s + QUOTE;  // suboptimal! Doesn't escape quotes.
}


QString msgFromArgs(const QStringList& args)
{
    QStringList nonempty_args;
    for (const QString& arg : args) {
        if (!arg.isEmpty()) {
            nonempty_args.append(arg);
        }
    }
    return nonempty_args.join(" ");
}


// ============================================================================
// API handler. Distinct from any particular network/threading
// model, so all can use it (e.g. by inheritance), but hooks in to whichever
// you choose.
// ============================================================================

/*

WhiskerApi::WhiskerApi(const ImmSendGetReplyFn& whisker_immsend_get_reply_fn,
                       const QString& sysevent_prefix) :
    m_immsend_get_reply_fn(whisker_immsend_get_reply_fn),
    m_sysevent_prefix(sysevent_prefix),
    m_sysevent_counter(0)
{

}


class WhiskerApi(object):
    def __init__(self,
                 whisker_immsend_get_reply_fn: Callable[..., str],
                 sysevent_prefix: str = "sys_",
                 **kwargs) -> None:
        """
        The function whisker_immsend_get_reply_fn must take arguments *args,
        join stringified versions of them using a space as the separator, and
        send them to the Whisker server via the immediate socket, returning the
        string that the server sent back.
        """
        super().__init__(**kwargs)
        self._immsend_get_reply = whisker_immsend_get_reply_fn
        self.sysevent_prefix = sysevent_prefix
        self.sysevent_counter = 0
        self.callback_handler = CallbackHandler()

    # -------------------------------------------------------------------------
    # Internal derived comms
    # -------------------------------------------------------------------------

    def _immresp(self, *args) -> str:
        reply = self._immsend_get_reply(*args)
        (reply, whisker_timestamp) = split_timestamp(reply)
        return reply

    def _immbool(self, *args) -> bool:
        reply = self._immresp(*args)
        return reply == RESPONSE_SUCCESS

    def _immresp_with_timestamp(self, *args) -> Tuple[str, Optional[int]]:
        reply = self._immsend_get_reply(*args)
        (reply, whisker_timestamp) = split_timestamp(reply)
        return reply, whisker_timestamp

    # -------------------------------------------------------------------------
    # Front-end functions for these
    # -------------------------------------------------------------------------

    def get_command_boolean(self, *args) -> bool:
        return self._immbool(*args)

    def command(self, *args) -> bool:
        return self._immbool(*args)

    def command_exc(self, *args) -> None:
        """Complete command or raise WhiskerCommandFailed."""
        if not self._immbool(*args):
            raise WhiskerCommandFailed(msg_from_args(*args))

    def get_response(self, *args) -> str:
        return self._immresp(*args)

    def get_response_with_timestamp(self, *args) -> Tuple[str, Optional[int]]:
        return self._immresp_with_timestamp(*args)

    # -------------------------------------------------------------------------
    # Custom event handling, e.g. for line flashing
    # -------------------------------------------------------------------------

    def get_new_sysevent(self, *args) -> str:
        self.sysevent_counter += 1
        return self.sysevent_prefix + "_".join(
            str(x) for x in [self.sysevent_counter] + list(args)
        ).replace(" ", "")

    def process_backend_event(self, event: str) -> bool:
        """Returns True if the backend API has dealt with the event and it
        doesn't need to go to the main behavioural task."""
        n_called, swallow_event = self.callback_handler.process_event(event)
        return (
            (n_called > 0 and swallow_event) or
            event.startswith(self.sysevent_prefix)
        )

    def send_after_delay(self, delay_ms: int, msg: str,
                         event: str = '') -> None:
        event = event or self.get_new_sysevent("send", msg)
        self.timer_set_event(event, delay_ms)
        self.callback_handler.add_single(event, self._immsend_get_reply, [msg])

    def call_after_delay(self,
                         delay_ms: int,
                         callback: Callable[..., None],
                         args: List[Any] = None,
                         kwargs: List[Any] = None,
                         event: str = '') -> None:
        args = args or []
        kwargs = kwargs or {}
        event = event or self.get_new_sysevent("call")
        self.timer_set_event(event, delay_ms)
        self.callback_handler.add_single(event, callback, args, kwargs)

    def call_on_event(self,
                      event: str,
                      callback: Callable[..., None],
                      args: List[Any] = None,
                      kwargs: List[Any] = None,
                      swallow_event: bool = False) -> None:
        args = args or []
        kwargs = kwargs or {}
        self.callback_handler.add_persistent(event, callback, args, kwargs,
                                             swallow_event=swallow_event)

    def clear_event_callback(self,
                             event: str,
                             callback: Callable[..., None] = None) -> None:
        self.callback_handler.remove(event, callback=callback)

    def clear_all_callbacks(self) -> None:
        self.callback_handler.clear()

    def debug_callbacks(self) -> None:
        self.callback_handler.debug()

    # -------------------------------------------------------------------------
    # Line flashing
    # -------------------------------------------------------------------------

    def flash_line_pulses(self,
                          line: str,
                          count: int,
                          on_ms: int,
                          off_ms: int,
                          on_at_rest: bool = False) -> int:
        assert count > 0
        # Generally better to ping-pong the events, rather than line them up
        # in advance, in case the user specifies very rapid oscillation that
        # exceeds the network bandwidth, or something; better to be slow than
        # to garbage up the sequence.
        if on_at_rest:
            # Currently at rest = on.
            # For 4 flashes:
            # OFF .. ON .... OFF .. ON .... OFF .. ON .... OFF .. ON
            on_now = False
            timing_sequence = [off_ms] + (count - 1) * [on_ms, off_ms]
        else:
            # Currently at rest = off.
            # For 4 flashes:
            # ON .... OFF .. ON .... OFF .. ON .... OFF .. ON .... OFF
            on_now = True
            timing_sequence = [on_ms] + (count - 1) * [off_ms, on_ms]
        total_duration_ms = sum(timing_sequence)
        self.flash_line_ping_pong(line, on_now, timing_sequence)
        return total_duration_ms

    def flash_line_ping_pong(self,
                             line: str,
                             on_now: bool,
                             timing_sequence: List[int]) -> None:
        """
        line: line number/name
        on_now: switch it on or off now?
        timing_sequence: array of times (in ms) for the next things
        """
        self.line_on(line) if on_now else self.line_off(line)
        if not timing_sequence:
            return
        delay_ms = timing_sequence[0]
        timing_sequence = timing_sequence[1:]
        event = self.get_new_sysevent(line, "off" if on_now else "on")
        self.call_after_delay(delay_ms, self.flash_line_ping_pong,
                              args=[line, not on_now, timing_sequence],
                              event=event)

    # -------------------------------------------------------------------------
    # Whisker command set: comms, misc
    # -------------------------------------------------------------------------

    def timestamps(self, on: bool) -> bool:
        return self._immbool(CMD_TIMESTAMPS, _on_val(on))

    def reset_clock(self) -> bool:
        return self._immbool(CMD_RESET_CLOCK)

    def get_server_version(self) -> str:
        return self._immresp(CMD_VERSION)

    def get_server_version_numeric(self) -> float:
        return float(self.get_server_version())

    def get_server_time_ms(self) -> int:
        return int(self._immresp(CMD_REQUEST_TIME))

    def get_client_number(self) -> int:
        return int(self._immresp(CMD_CLIENT_NUMBER))

    def permit_client_messages(self, permit: bool) -> bool:
        return self._immbool(CMD_PERMIT_CLIENT_MESSAGES, _on_val(permit))

    def send_to_client(self, client_num: int, *args) -> bool:
        return self._immbool(CMD_SEND_TO_CLIENT, client_num,
                             msg_from_args(*args))

    def set_media_directory(self, directory: str) -> bool:
        return self._immbool(CMD_SET_MEDIA_DIRECTORY, quote(directory))

    def report_name(self, *args) -> bool:
        return self._immbool(CMD_REPORT_NAME, msg_from_args(*args))
        # quotes not necessary

    def report_status(self, *args) -> bool:
        return self._immbool(CMD_REPORT_STATUS, msg_from_args(*args))
        # quotes not necessary

    def report_comment(self, *args) -> bool:
        return self._immbool(CMD_REPORT_COMMENT, msg_from_args(*args))
        # quotes not necessary

    def get_network_latency_ms(self) -> Optional[int]:
        reply = self._immresp(CMD_TEST_NETWORK_LATENCY)
        if reply != PING:
            return None
        try:
            reply = self._immresp(PING_ACK)
            return int(reply)
        except (TypeError, ValueError):
            return None

    def ping(self) -> bool:
        reply = self._immresp(PING)
        success = reply == PING_ACK
        return success

    def shutdown(self) -> bool:
        return self._immbool(CMD_SHUTDOWN)

    def authenticate_get_challenge(self, package: str,
                                   client_name: str) -> Optional[str]:
        reply = self._immresp(CMD_AUTHENTICATE, package, client_name)
        if not reply.startswith(MSG_AUTHENTICATE_CHALLENGE + " "):
            return None
        challenge = reply.split()[1]
        return challenge

    def authenticate_provide_response(self, response: str) -> bool:
        return self._immbool(CMD_AUTHENTICATE_RESPONSE, response)

    # -------------------------------------------------------------------------
    # Whisker command set: logs
    # -------------------------------------------------------------------------

    def log_open(self, filename: str) -> bool:
        return self._immbool(CMD_LOG_OPEN, quote(filename))

    def log_set_options(self,
                        events: bool = True,
                        key_events: bool = True,
                        client_client: bool = True,
                        comms: bool = False,
                        signature: bool = True) -> bool:
        return self._immbool(
            CMD_LOG_SET_OPTIONS,
            FLAG_EVENTS, _on_val(events),
            FLAG_KEYEVENTS, _on_val(key_events),
            FLAG_CLIENTCLIENT, _on_val(client_client),
            FLAG_COMMS, _on_val(comms),
            FLAG_SIGNATURE, _on_val(signature),
        )

    def log_pause(self) -> bool:
        return self._immbool(CMD_LOG_PAUSE)

    def log_resume(self) -> bool:
        return self._immbool(CMD_LOG_RESUME)

    def log_write(self, *args) -> bool:
        return self._immbool(CMD_LOG_WRITE, msg_from_args(*args))

    def log_close(self) -> bool:
        return self._immbool(CMD_LOG_CLOSE)

    # -------------------------------------------------------------------------
    # Whisker command set: timers
    # -------------------------------------------------------------------------

    def timer_set_event(self, event: str, duration_ms: int,
                        reload_count: int = 0) -> bool:
        return self._immbool(CMD_TIMER_SET_EVENT, duration_ms, reload_count,
                             event)

    def timer_clear_event(self, event: str) -> bool:
        return self._immbool(CMD_TIMER_CLEAR_EVENT, event)

    def timer_clear_all_events(self) -> bool:
        return self._immbool(CMD_TIMER_CLEAR_ALL_EVENTS)

    # -------------------------------------------------------------------------
    # Whisker command set: claiming, relinquishing
    # -------------------------------------------------------------------------

    def claim_group(self, group: str, prefix: str = "",
                    suffix: str = "") -> bool:
        args = [CMD_CLAIM_GROUP, group]
        if prefix:
            args += [FLAG_PREFIX, prefix]
        if suffix:
            args += [FLAG_SUFFIX, suffix]
        return self._immbool(*args)

    def claim_line(self,
                   number: int = None,
                   group: str = None,
                   device: str = None,
                   output: bool = False,
                   reset_state: ResetState = ResetState.leave,
                   alias: str = "") -> bool:
        assert (
            (is_ducktype_nonnegative_int(number) or (group and device)) and
            not (number is not None and group)
        ), "Specify number [integer >= 0] OR (group AND device)"
        assert isinstance(reset_state, ResetState)
        args = [CMD_LINE_CLAIM]  # type: List[Any]
        if number is not None:
            args.append(number)
        else:
            args.extend([group, device])
        args.extend([
            FLAG_OUTPUT if output else FLAG_INPUT,
            LINE_RESET_FLAGS[ResetState.input if not output else reset_state]
        ])
        if alias:
            args.extend([FLAG_ALIAS, alias])
        return self._immbool(*args)

    def relinquish_all_lines(self) -> bool:
        return self._immbool(CMD_LINE_RELINQUISH_ALL)

    def line_set_alias(self, line: str, alias: str) -> bool:
        return self._immbool(CMD_LINE_SET_ALIAS, line, alias)

    def claim_audio(self, number: int = None, group: str = None,
                    device: str = None, alias: str = "") -> bool:
        assert (
            (is_ducktype_nonnegative_int(number) or (group and device)) and
            not (number is not None and group)
        ), "Specify number [integer >= 0] OR (group AND device)"
        args = [CMD_AUDIO_CLAIM]  # type: List[Any]
        if number is not None:
            args.append(number)
        else:
            args.extend([group, device])
        if alias:
            args.extend([FLAG_ALIAS, alias])
        return self._immbool(*args)

    def audio_set_alias(self, from_: str, to: str) -> bool:
        return self._immbool(CMD_AUDIO_SET_ALIAS, from_, to)

    def relinquish_all_audio(self) -> bool:
        return self._immbool(CMD_AUDIO_RELINQUISH_ALL)

    def claim_display(self, number: int = None, group: str = None,
                      device: str = None, alias: str = "") -> bool:
        # Autocreating debug views not supported (see C++ WhiskerClientLib).
        assert (
            (is_ducktype_nonnegative_int(number) or (group and device)) and
            not (number is not None and group)
        ), "Specify number [integer >= 0] OR (group AND device)"
        args = [CMD_DISPLAY_CLAIM]  # type: List[Any]
        if number is not None:
            args.append(number)
        else:
            args.extend([group, device])
        if alias:
            args.extend([FLAG_ALIAS, alias])
        return self._immbool(*args)

    def display_set_alias(self, from_: str, to: str) -> bool:
        return self._immbool(CMD_DISPLAY_SET_ALIAS, from_, to)

    def relinquish_all_displays(self) -> bool:
        return self._immbool(CMD_DISPLAY_RELINQUISH_ALL)

    def display_create_device(self, name: str, resize: bool = True,
                              directdraw: bool = True,
                              rectangle: Rectangle = None,
                              debug_touches: bool = False) -> bool:
        args = [
            CMD_DISPLAY_CREATE_DEVICE,
            name,
            FLAG_RESIZE, _on_val(resize),
            FLAG_DIRECTDRAW, _on_val(directdraw),
        ]  # type: List[Any]
        if rectangle:
            args.extend([
                rectangle.left,
                rectangle.top,
                rectangle.width,
                rectangle.height
            ])
        if debug_touches:
            args.append(FLAG_DEBUG_TOUCHES)
        return self._immbool(*args)

    def display_delete_device(self, device: str) -> bool:
        return self._immbool(CMD_DISPLAY_DELETE_DEVICE, device)

    # -------------------------------------------------------------------------
    # Whisker command set: lines
    # -------------------------------------------------------------------------

    def line_set_state(self, line: str, on: bool) -> bool:
        return self._immbool(CMD_LINE_SET_STATE, line, _on_val(on))

    def line_read_state(self, line: str) -> Optional[bool]:
        """Returns a boolean representing the line state, or None upon
        failure."""
        reply = self._immresp(CMD_LINE_READ_STATE, line)
        if reply == VAL_ON:
            return True
        elif reply == VAL_OFF:
            return False
        else:
            return None

    def line_set_event(self, line: str, event: str,
                       event_type: LineEventType = LineEventType.on) -> bool:
        assert isinstance(event_type, LineEventType)
        return self._immbool(CMD_LINE_SET_EVENT, line,
                             LINE_EVENT_TYPES[event_type], event)

    def line_clear_event(self, event: str) -> bool:
        return self._immbool(CMD_LINE_CLEAR_EVENT, event)

    def line_clear_event_by_line(self, line: str,
                                 event_type: LineEventType) -> bool:
        assert isinstance(event_type, LineEventType)
        return self._immbool(CMD_LINE_CLEAR_EVENTS_BY_LINE, line,
                             LINE_EVENT_TYPES[event_type])

    def line_clear_all_events(self) -> bool:
        return self._immbool(CMD_LINE_CLEAR_ALL_EVENTS)

    def line_set_safety_timer(self, line: str, time_ms: int,
                              safety_state: SafetyState) -> bool:
        assert isinstance(safety_state, SafetyState)
        return self._immbool(CMD_LINE_SET_SAFETY_TIMER, line, time_ms,
                             LINE_SAFETY_STATES[safety_state])

    def line_clear_safety_timer(self, line: str) -> bool:
        return self._immbool(CMD_LINE_CLEAR_SAFETY_TIMER, line)

    # -------------------------------------------------------------------------
    # Whisker command set: audio
    # -------------------------------------------------------------------------

    def audio_play_wav(self, device: str, filename: str) -> bool:
        return self._immbool(CMD_AUDIO_PLAY_FILE, device, quote(filename))

    def audio_load_tone(self, device: str, buffer_: str,
                        frequency_hz: int, tone_type: ToneType,
                        duration_ms: int) -> bool:
        assert isinstance(tone_type, ToneType)
        return self._immbool(
            CMD_AUDIO_LOAD_TONE,
            device,
            buffer_,
            frequency_hz,
            AUDIO_TONE_TYPES[tone_type],
            duration_ms
        )

    def audio_load_wav(self, device: str, sound: str, filename: str) -> bool:
        return self._immbool(CMD_AUDIO_LOAD_SOUND, device, sound,
                             quote(filename))

    def audio_play_sound(self, device: str, sound: str,
                         loop: bool = False) -> bool:
        args = [CMD_AUDIO_PLAY_SOUND, device, sound]
        if loop:
            args.append(FLAG_LOOP)
        return self._immbool(*args)

    def audio_unload_sound(self, device: str, sound: str) -> bool:
        return self._immbool(CMD_AUDIO_UNLOAD_SOUND, device, sound)

    def audio_stop_sound(self, device: str, sound: str) -> bool:
        return self._immbool(CMD_AUDIO_STOP_SOUND, device, sound)

    def audio_silence_device(self, device: str) -> bool:
        return self._immbool(CMD_AUDIO_SILENCE_DEVICE, device)

    def audio_unload_all(self, device: str) -> bool:
        return self._immbool(CMD_AUDIO_UNLOAD_ALL, device)

    def audio_set_sound_volume(self, device: str, sound: str,
                               volume: int) -> bool:
        return self._immbool(CMD_AUDIO_SET_SOUND_VOLUME, device, sound, volume)

    def audio_silence_all_devices(self) -> bool:
        return self._immbool(CMD_AUDIO_SILENCE_ALL_DEVICES)

    def audio_get_sound_duration_ms(self, device: str,
                                    sound: str) -> Optional[int]:
        reply = self._immresp(CMD_AUDIO_GET_SOUND_LENGTH, device, sound)
        try:
            return int(reply)
        except (TypeError, ValueError):
            return None

    # -------------------------------------------------------------------------
    # Whisker command set: display: display operations
    # -------------------------------------------------------------------------

    def display_get_size(self, device: str) -> Optional[SizeType]:
        """Returns a (width, height) tuple, or None."""
        reply = self._immresp(CMD_DISPLAY_GET_SIZE, device)
        try:
            (prefix, width_str, height_str) = reply.split()
            assert prefix == MSG_SIZE
            width = int(width_str)
            height = int(height_str)
            return width, height
        except (AttributeError, TypeError, ValueError, AssertionError):
            return None

    def display_scale_documents(self, device: str, scale: bool = True) -> bool:
        return self._immbool(CMD_DISPLAY_SCALE_DOCUMENTS, device,
                             _on_val(scale))

    def display_show_document(self, device: str, doc: str) -> bool:
        return self._immbool(CMD_DISPLAY_SHOW_DOCUMENT, device, doc)

    def display_blank(self, device: str) -> bool:
        return self._immbool(CMD_DISPLAY_BLANK, device)

    # -------------------------------------------------------------------------
    # Whisker command set: display: document operations
    # -------------------------------------------------------------------------

    def display_create_document(self, doc: str) -> bool:
        return self._immbool(CMD_DISPLAY_CREATE_DOCUMENT, doc)

    def display_delete_document(self, doc: str) -> bool:
        return self._immbool(CMD_DISPLAY_DELETE_DOCUMENT, doc)

    def display_set_document_size(self, doc: str,
                                  width: int, height: int) -> bool:
        return self._immbool(CMD_DISPLAY_SET_DOCUMENT_SIZE, doc, width, height)

    def display_set_background_colour(self, doc: str,
                                      colour: ColourType = BLACK) -> bool:
        return self._immbool(CMD_DISPLAY_SET_BACKGROUND_COLOUR, doc,
                             colour[0], colour[1], colour[2])

    def display_delete_obj(self, doc: str, obj: str) -> bool:
        return self._immbool(CMD_DISPLAY_DELETE_OBJECT, doc, obj)

    def display_add_obj(self, doc: str, obj: str, obj_type: str,
                        *parameters) -> bool:
        return self._immbool(CMD_DISPLAY_ADD_OBJECT, doc, obj, obj_type,
                             *parameters)

    def display_set_event(
            self, doc: str, obj: str, event: str,
            event_type: DocEventType = DocEventType.touch_down) -> bool:
        assert isinstance(event_type, DocEventType)
        return self._immbool(CMD_DISPLAY_SET_EVENT, doc, obj,
                             DOC_EVENT_TYPES[event_type], quote(event))

    def display_clear_event(
            self, doc: str, obj: str,
            event_type: DocEventType = DocEventType.touch_down) -> bool:
        assert isinstance(event_type, DocEventType)
        return self._immbool(CMD_DISPLAY_CLEAR_EVENT, doc, obj,
                             DOC_EVENT_TYPES[event_type])

    def display_set_obj_event_transparency(self, doc: str, obj: str,
                                           transparent: bool = False) -> bool:
        return self._immbool(CMD_DISPLAY_SET_OBJ_EVENT_TRANSPARENCY,
                             doc, obj, _on_val(transparent))

    def display_event_coords(self, on: bool) -> bool:
        return self._immbool(CMD_DISPLAY_EVENT_COORDS, _on_val(on))

    def display_bring_to_front(self, doc: str, obj: str) -> bool:
        return self._immbool(CMD_DISPLAY_BRING_TO_FRONT, doc, obj)

    def display_send_to_back(self, doc: str, obj: str) -> bool:
        return self._immbool(CMD_DISPLAY_SEND_TO_BACK, doc, obj)

    def display_keyboard_events(
            self, doc: str,
            key_event_type: KeyEventType = KeyEventType.down) -> bool:
        assert isinstance(key_event_type, KeyEventType)
        return self._immbool(CMD_DISPLAY_KEYBOARD_EVENTS, doc,
                             KEY_EVENT_TYPES[key_event_type])

    def display_cache_changes(self, doc: str) -> bool:
        return self._immbool(CMD_DISPLAY_CACHE_CHANGES, doc)

    def display_show_changes(self, doc: str) -> bool:
        return self._immbool(CMD_DISPLAY_SHOW_CHANGES, doc)

    @contextmanager
    def display_cache_wrapper(self, doc: str) -> Generator[None, None, None]:
        """
        Use like:
            with something.display_cache_wrapper(doc):
                # do some display-related things
        """
        self.display_cache_changes(doc)
        yield
        self.display_show_changes(doc)

    def display_get_document_size(self, doc: str) -> Optional[SizeType]:
        """Returns a (width, height) tuple, or None."""
        reply = self._immresp(CMD_DISPLAY_GET_DOCUMENT_SIZE, doc)
        try:
            (prefix, width_str, height_str) = reply.split()
            assert prefix == MSG_SIZE
            width = int(width_str)
            height = int(height_str)
            return width, height
        except (AttributeError, TypeError, ValueError, AssertionError):
            return None

    def display_get_object_extent(self, doc: str,
                                  obj: str) -> Optional[Rectangle]:
        """Returns a rect, or None."""
        reply = self._immresp(CMD_DISPLAY_GET_OBJECT_EXTENT, doc, obj)
        try:
            (prefix, left_str, top_str, right_str, bottom_str) = reply.split()
            assert prefix == MSG_EXTENT
            rect = Rectangle(
                left=int(left_str),
                right=int(right_str),
                top=int(top_str),
                bottom=int(bottom_str),
            )
            return rect
        except (AttributeError, TypeError, ValueError, AssertionError):
            return None

    def display_set_background_event(
            self, doc: str, event: str,
            event_type: DocEventType = DocEventType.touch_down) -> bool:
        assert isinstance(event_type, DocEventType)
        return self._immbool(CMD_DISPLAY_SET_BACKGROUND_EVENT, doc,
                             DOC_EVENT_TYPES[event_type], quote(event))

    def display_clear_background_event(
            self, doc: str,
            event_type: DocEventType = DocEventType.touch_down) -> bool:
        assert isinstance(event_type, DocEventType)
        return self._immbool(CMD_DISPLAY_CLEAR_BACKGROUND_EVENT, doc,
                             DOC_EVENT_TYPES[event_type])

    # -------------------------------------------------------------------------
    # Whisker command set: display: specific object creation
    # -------------------------------------------------------------------------

    def display_add_obj_text(
            self,
            doc: str,
            obj: str,
            pos: PointType,
            text: str,
            height: int = 0,
            font: str = "",
            italic: bool = False,
            underline: bool = False,
            weight: int = 0,
            colour: ColourType = WHITE,
            opaque: bool = False,
            bg_colour: ColourType = BLACK,
            valign: TextVerticalAlign = TextVerticalAlign.top,
            halign: TextHorizontalAlign = TextHorizontalAlign.left) -> bool:
        """Position is an (x, y) tuple. Colours are R, G, B tuples."""
        assert_ducktype_pos(pos)
        assert_ducktype_colour(colour)
        assert_ducktype_colour(bg_colour)
        assert isinstance(valign, TextVerticalAlign)
        assert isinstance(halign, TextHorizontalAlign)
        if font:
            fontargs = [FLAG_FONT, quote(font)]
        else:
            fontargs = []
        args = [
            pos[0], pos[1],
            quote(text),
            FLAG_HEIGHT, height,
            FLAG_TEXT_WEIGHT, weight,
            FLAG_TEXT_ITALIC if italic else "",
            FLAG_TEXT_UNDERLINE if underline else "",
            FLAG_TEXT_OPAQUE if opaque else "",
            FLAG_TEXT_COLOUR, colour[0], colour[1], colour[2],
            FLAG_BACKCOLOUR, bg_colour[0], bg_colour[1], bg_colour[2],
            TEXT_HALIGN_FLAGS[halign],
            TEXT_VALIGN_FLAGS[valign],
        ] + fontargs
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_TEXT, *args)

    def display_add_obj_bitmap(
            self,
            doc: str,
            obj: str,
            pos: PointType,
            filename: str,
            stretch: bool = False,
            height: int = -1,
            width: int = -1,
            valign: VerticalAlign = VerticalAlign.top,
            halign: HorizontalAlign = HorizontalAlign.left) -> bool:
        assert_ducktype_pos(pos)
        assert isinstance(valign, VerticalAlign)
        assert isinstance(halign, HorizontalAlign)
        args = [
            pos[0], pos[1],
            quote(filename),
            FLAG_BITMAP_STRETCH if stretch else FLAG_BITMAP_CLIP,
            FLAG_HEIGHT, height,
            FLAG_WIDTH, width,
            HALIGN_FLAGS[halign],
            VALIGN_FLAGS[valign],
        ]
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_BITMAP, *args)

    def display_add_obj_line(self,
                             doc: str,
                             obj: str,
                             start: PointType,
                             end: PointType,
                             pen: Pen) -> bool:
        """Coordinates are (x, y) tuples."""
        assert_ducktype_pos(start)
        assert_ducktype_pos(end)
        assert isinstance(pen, Pen)
        args = [
            start[0], start[1],
            end[0], end[1],
            pen.whisker_option_string,
        ]
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_LINE, *args)

    def display_add_obj_arc(self,
                            doc: str,
                            obj: str,
                            rect: Rectangle,
                            start, end, pen) -> bool:
        """The arc fits into the rect."""
        assert isinstance(rect, Rectangle)
        assert_ducktype_pos(start)
        assert_ducktype_pos(end)
        assert isinstance(pen, Pen)
        args = [
            rect.left, rect.top,
            rect.right, rect.bottom,
            start[0], start[1],
            end[0], end[1],
            pen.whisker_option_string,
        ]
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_ARC, *args)

    def display_add_obj_bezier(self,
                               doc: str,
                               obj: str,
                               start: PointType,
                               control1: PointType,
                               control2: PointType,
                               end: PointType,
                               pen: Pen) -> bool:
        assert_ducktype_pos(start)
        assert_ducktype_pos(control1)
        assert_ducktype_pos(control2)
        assert_ducktype_pos(end)
        assert isinstance(pen, Pen)
        """The control points 'pull' the curve."""
        args = [
            start[0], start[1],
            control1[0], control1[1],
            control2[0], control2[1],
            end[0], end[1],
            pen.whisker_option_string,
        ]
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_BEZIER, *args)

    def display_add_obj_chord(self,
                              doc: str,
                              obj: str,
                              rect: Rectangle,
                              line_start: PointType,
                              line_end: PointType,
                              pen: Pen,
                              brush: Brush) -> bool:
        """The chord is the intersection of an ellipse (defined by the rect)
        and a line that intersects it."""
        assert isinstance(rect, Rectangle)
        assert_ducktype_pos(line_start)
        assert_ducktype_pos(line_end)
        assert isinstance(pen, Pen)
        assert isinstance(brush, Brush)
        args = [
            rect.left, rect.top,
            rect.right, rect.bottom,
            line_start[0], line_start[1],
            line_end[0], line_end[1],
            pen.whisker_option_string,
            brush.whisker_option_string,
        ]
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_CHORD, *args)

    def display_add_obj_ellipse(self,
                                doc: str,
                                obj: str,
                                rect: Rectangle,
                                pen: Pen,
                                brush: Brush) -> bool:
        """The ellipse fits into the rectangle (and its centre is at the centre
        of the rectangle)."""
        assert isinstance(rect, Rectangle)
        assert isinstance(pen, Pen)
        assert isinstance(brush, Brush)
        args = [
            rect.left, rect.top,
            rect.right, rect.bottom,
            pen.whisker_option_string,
            brush.whisker_option_string,
        ]
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_ELLIPSE, *args)

    def display_add_obj_pie(self,
                            doc: str,
                            obj: str,
                            rect: Rectangle,
                            arc_start: PointType,
                            arc_end: PointType,
                            pen: Pen,
                            brush: Brush) -> bool:
        """See Whisker docs."""
        assert isinstance(rect, Rectangle)
        assert_ducktype_pos(arc_start)
        assert_ducktype_pos(arc_end)
        assert isinstance(pen, Pen)
        assert isinstance(brush, Brush)
        args = [
            rect.left, rect.top,
            rect.right, rect.bottom,
            arc_start[0], arc_start[1],
            arc_end[0], arc_end[1],
            pen.whisker_option_string,
            brush.whisker_option_string,
        ]
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_PIE, *args)

    def display_add_obj_polygon(self,
                                doc: str,
                                obj: str,
                                points: List[PointType],
                                pen: Pen,
                                brush: Brush,
                                alternate: bool = False) -> bool:
        """See Whisker docs."""
        assert len(points) >= 3
        assert isinstance(pen, Pen)
        assert isinstance(brush, Brush)
        args = [str(len(points))]  # type: List[Any]
        for point in points:
            assert_ducktype_pos(point)
            args.extend([point[0], point[1]])
        args.extend([
            FLAG_POLYGON_ALTERNATE if alternate else FLAG_POLYGON_WINDING,
            pen.whisker_option_string,
            brush.whisker_option_string,
        ])
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_POLYGON, *args)

    def display_add_obj_rectangle(self,
                                  doc: str,
                                  obj: str,
                                  rect: Rectangle,
                                  pen: Pen,
                                  brush: Brush) -> bool:
        """See Whisker docs."""
        assert isinstance(rect, Rectangle)
        assert isinstance(pen, Pen)
        assert isinstance(brush, Brush)
        args = [
            rect.left, rect.top,
            rect.right, rect.bottom,
            pen.whisker_option_string,
            brush.whisker_option_string,
        ]
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_RECTANGLE, *args)

    def display_add_obj_roundrect(self,
                                  doc: str,
                                  obj: str,
                                  rect: Rectangle,
                                  ellipse_height: int,
                                  ellipse_width: int,
                                  pen: Pen,
                                  brush: Brush) -> bool:
        """See Whisker docs."""
        assert isinstance(rect, Rectangle)
        assert isinstance(pen, Pen)
        assert isinstance(brush, Brush)
        args = [
            rect.left, rect.top,
            rect.right, rect.bottom,
            ellipse_width, ellipse_height,
            pen.whisker_option_string,
            brush.whisker_option_string,
        ]
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_ROUNDRECT, *args)

    def display_add_obj_camcogquadpattern(self,
                                          doc: str,
                                          obj: str,
                                          pos: PointType,
                                          pixel_width: int,
                                          pixel_height: int,
                                          top_left_patterns: List[int],
                                          top_right_patterns: List[int],
                                          bottom_left_patterns: List[int],
                                          bottom_right_patterns: List[int],
                                          top_left_colour: ColourType,
                                          top_right_colour: ColourType,
                                          bottom_left_colour: ColourType,
                                          bottom_right_colour: ColourType,
                                          bg_colour: ColourType) -> bool:
        """
        See Whisker docs.
        Patterns are lists (of length 8) of bytes.
        Colours are R, G, B tuples.
        """
        assert len(top_left_patterns) == 8
        assert len(top_right_patterns) == 8
        assert len(bottom_left_patterns) == 8
        assert len(bottom_right_patterns) == 8
        assert_ducktype_colour(top_left_colour)
        assert_ducktype_colour(top_right_colour)
        assert_ducktype_colour(bottom_left_colour)
        assert_ducktype_colour(bottom_right_colour)
        assert_ducktype_colour(bg_colour)
        args = [pos[0], pos[1], pixel_width, pixel_height]
        args.extend(top_left_patterns)
        args.extend(top_right_patterns)
        args.extend(bottom_left_patterns)
        args.extend(bottom_right_patterns)
        args.extend(top_left_colour)
        args.extend(top_right_colour)
        args.extend(bottom_left_colour)
        args.extend(bottom_right_colour)
        args.extend(bg_colour)
        return self.display_add_obj(doc, obj, VAL_OBJTYPE_CAMCOGQUADPATTERN,
                                    *args)

    # -------------------------------------------------------------------------
    # Whisker command set: display: video extras
    # -------------------------------------------------------------------------

    def display_add_obj_video(self,
                              doc: str,
                              video: str,
                              pos: PointType,
                              filename: str,
                              loop: bool = False,
                              playmode: VideoPlayMode = VideoPlayMode.wait,
                              width: int = -1,
                              height: int = -1,
                              play_audio: bool = True,
                              valign: VerticalAlign = VerticalAlign.top,
                              halign: HorizontalAlign = HorizontalAlign.left,
                              bg_colour: ColourType = BLACK) -> bool:
        assert isinstance(playmode, VideoPlayMode)
        assert isinstance(valign, VerticalAlign)
        assert isinstance(halign, HorizontalAlign)
        assert_ducktype_colour(bg_colour)
        args = [
            pos[0], pos[1],
            quote(filename),
            FLAG_LOOP if loop else FLAG_VIDEO_NOLOOP,
            VIDEO_PLAYMODE_FLAGS[playmode],
            FLAG_WIDTH, width,
            FLAG_HEIGHT, height,
            FLAG_VIDEO_AUDIO if play_audio else FLAG_VIDEO_NOAUDIO,
            HALIGN_FLAGS[halign],
            VALIGN_FLAGS[valign],
            FLAG_BACKCOLOUR, bg_colour[0], bg_colour[1], bg_colour[2],
        ]
        return self.display_add_obj(doc, video, VAL_OBJTYPE_VIDEO, *args)

    def display_set_audio_device(self, display_device: str,
                                 audio_device: str) -> bool:
        """Devices may be specified as numbers or names."""
        return self._immbool(CMD_DISPLAY_SET_AUDIO_DEVICE, display_device,
                             audio_device)

    def video_play(self, doc: str, video: str) -> bool:
        return self._immbool(CMD_VIDEO_PLAY, doc, video)

    def video_pause(self, doc: str, video: str) -> bool:
        return self._immbool(CMD_VIDEO_PAUSE, doc, video)

    def video_stop(self, doc: str, video: str) -> bool:
        return self._immbool(CMD_VIDEO_STOP, doc, video)

    def video_timestamps(self, on: bool) -> bool:
        return self._immbool(CMD_VIDEO_TIMESTAMPS, _on_val(on))

    def video_get_time_ms(self, doc: str, video: str) -> Optional[int]:
        reply = self._immresp(CMD_VIDEO_GET_TIME, doc, video)
        try:
            return int(reply.split()[1])
        except (IndexError, ValueError):
            return None

    def video_get_duration_ms(self, doc: str, video: str) -> Optional[int]:
        reply = self._immresp(CMD_VIDEO_GET_DURATION, doc, video)
        try:
            return int(reply.split()[1])
        except (IndexError, ValueError):
            return None

    def video_seek_relative(self, doc: str, video: str, time_ms: int) -> bool:
        return self._immbool(CMD_VIDEO_SEEK_RELATIVE, doc, video, time_ms)

    def video_seek_absolute(self, doc: str, video: str, time_ms: int) -> bool:
        return self._immbool(CMD_VIDEO_SEEK_ABSOLUTE, doc, video, time_ms)

    def video_set_volume(self, doc: str, video: str, volume: int) -> bool:
        return self._immbool(CMD_VIDEO_SET_VOLUME, doc, video, volume)

    # -------------------------------------------------------------------------
    # Shortcuts to Whisker commands
    # -------------------------------------------------------------------------

    def line_on(self, line: str) -> None:
        self.line_set_state(line, True)

    def line_off(self, line: str) -> None:
        self.line_set_state(line, False)

    def broadcast(self, *args) -> bool:
        return self.send_to_client(-1, *args)


WhiskerApi::WhiskerApi()
{

}

*/

}  // namespace whiskerapi

