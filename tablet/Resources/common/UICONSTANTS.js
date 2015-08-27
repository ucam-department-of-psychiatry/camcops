// UICONSTANTS.js

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

/*jslint node: true, nomen: true, newcap: true */
"use strict";
/*global L */

var COLOURS = require('common/COLOURS'),
    platform = require('lib/platform'),
    _ANDROID_THEME_LIGHT = true, // otherwise, dark -- see theme_camcops.xml
    _MENU_TITLE_FONT = {fontSize: '16sp', fontWeight: 'normal'},
    _MENU_BASE_FONT = {fontSize: '14sp', fontWeight: 'normal'},
    _MENU_BOLD_FONT = {fontSize: '14sp', fontWeight: 'bold'},
    _MENU_ITALIC_FONT = {fontSize: '14sp', fontStyle: 'italic'},
    _MENU_BIGBOLD_FONT = {fontSize: '16sp', fontWeight: 'bold'},
    _IM_PR = "images/camcops/",  // image filename prefix
    _ICON_CHOOSE_PATIENT = platform.translateFilename(_IM_PR +
                                                      'choose_patient.png'),
    QUESTIONNAIRE_BASE_FONT_SIZE = 16,
    QUESTIONNAIRE_BIG_FONT_SIZE = 32;

function getVariableFontSpecifyingPercent(base, bold, italic, percent) {
    return {
        fontSize: Math.round(base * percent / 100).toString() + 'sp',
        fontWeight: bold ? 'bold' : 'normal',
        fontStyle: italic ? 'italic' : 'normal'
    };
}

function getVariableFont(base, bold, italic) {
    var storedvars = require('table/storedvars'),
        percent = storedvars.questionnaireTextSizePercent.getValue();
    if (percent === null) {
        percent = 100;
    }
    return getVariableFontSpecifyingPercent(base, bold, italic, percent);
}

module.exports = {
    //=========================================================================
    // Generic
    //=========================================================================
    CAMCOPS_URL: 'http://www.camcops.org/',
    CAMCOPS_URL_DOCS: 'http://www.camcops.org/documentation',

    //=========================================================================
    // General appearance
    //=========================================================================

    IOS7_TOP_STATUSBAR_HEIGHT: 20,
    // http://docs.appcelerator.com/titanium/latest/#!/guide/
    //        iOS_7_Migration_Guide

    ICONSIZE: 48,
    SPACE: 4,
    BIGSPACE: 16,
    MEDIUMSPACE: 8,

    DOB_DATE_FORMAT: "DD MMM YYYY",
    // ... e.g. 04 Apr 2013; http://momentjs.com/docs/
    TASK_DATETIME_FORMAT: "DD MMM YYYY, HH:mm", // e.g. 04 Apr 2013, 13:28
    DATETIME_TEXTENTRY_MAXLENGTH: 30, // e.g. "30 September 2003, 14:35"

    //=========================================================================
    // Main menu system
    //=========================================================================

    // Menus
    MENU_BG_COLOUR: COLOURS.BLACK,
    MENU_TITLE_COLOUR: COLOURS.WHITE,
    MENU_SEPARATOR_COLOUR: COLOURS.GRAY20,
    MENU_HEADER_RULE_HEIGHT: 2,
    MENU_HEADER_RULE_COLOUR: COLOURS.GRAY,
    MENU_SEARCHBAR_BG_COLOUR: (
        _ANDROID_THEME_LIGHT ? COLOURS.WHITE : COLOURS.BLACK
    ),
    // ... iOS ignores this and uses white regardless (which looks OK).

    GARISH_DEBUG_COLOUR_1: COLOURS.RED,
    GARISH_DEBUG_COLOUR_2: COLOURS.YELLOW,
    GARISH_DEBUG_COLOUR_3: COLOURS.MAGENTA,

    WAIT_COLOUR: COLOURS.YELLOW,
    WAIT_FONT: {
        fontFamily: 'Helvetica Neue',
        fontSize: 26,
        fontWeight: 'normal'
    },
    WAIT_TITLE_COLOUR: COLOURS.WHITE,
    WAIT_TITLE_FONT: {
        fontFamily: 'Helvetica Neue',
        fontSize: 26,
        fontWeight: 'bold'
    },
    WAIT_BACKGROUND_COLOUR: COLOURS.GRAY,
    WAIT_SPACE: 10,

    // Titles in general
    MENU_TITLE_FONT: _MENU_TITLE_FONT,
    MENU_SUBTITLE_FONT: _MENU_BOLD_FONT,

    // Patient row in menus
    PATIENT_COLOUR: COLOURS.YELLOW,
    NO_PATIENT_COLOUR: COLOURS.MAGENTA,
    PATIENT_FONT: _MENU_BIGBOLD_FONT,

    // Menu table rows
    ROW_TITLE_COLOUR: COLOURS.WHITE,
    ROW_TITLE_FONT: _MENU_BASE_FONT,
    ROW_SUBTITLE_COLOUR: COLOURS.GRAY75,
    ROW_SUBTITLE_FONT: _MENU_BASE_FONT,
    ROW_NOT_IMPLEMENTED_BACKGROUND_COLOUR: COLOURS.GRAY20,
    NOT_PERMISSIBLE_BACKGROUND_COLOUR: COLOURS.DARKRED,
    COPYRIGHT_DETAILS_PENDING_BACKGROUND_COLOUR: COLOURS.OLIVE,
    CRIPPLED_BACKGROUND_COLOUR: COLOURS.PURPLE,
    TABLE_BG_SELECTED_COLOUR: COLOURS.GREEN,

    MIN_TABLE_ROW_HEIGHT: 36,

    CHANGE_PATIENT_MENU_LINE: {
        maintitle: L('menutitle_choose_patient'),
        icon: _ICON_CHOOSE_PATIENT,
        window: 'screen/SelectPatientWindow',
        notIfLocked: true
    },

    // Menu footers
    FOOTER_COLOUR: COLOURS.GRAY,
    FOOTER_FONT: _MENU_BASE_FONT,
    FOOTER_HEIGHT: 20,

    // Patient lists
    PATIENT_ROW1_FONT: _MENU_BOLD_FONT,
    PATIENT_ROW1_COLOUR: COLOURS.WHITE,
    PATIENT_ROW2_FONT: _MENU_BASE_FONT,
    PATIENT_ROW2_COLOUR: COLOURS.GRAY75,

    // Task selector window
    TASK_TITLE_COLOUR_COMPLETE: COLOURS.WHITE,
    TASK_TITLE_COLOUR_INCOMPLETE: COLOURS.GRAY,
    TASK_DATE_FONT: _MENU_BASE_FONT,
    TASK_DATE_COLOUR_COMPLETE: COLOURS.WHITE,
    TASK_DATE_COLOUR_INCOMPLETE: COLOURS.GRAY,
    TASK_PATIENT_FONT: _MENU_BASE_FONT,
    TASK_PATIENT_COLOUR: COLOURS.YELLOW,
    TASK_SUMMARY_FONT: _MENU_BOLD_FONT,
    TASK_SUMMARY_COLOUR_COMPLETE: COLOURS.WHITE,
    TASK_SUMMARY_COLOUR_INCOMPLETE: COLOURS.GRAY,

    // Editing (patients, settings)
    EDITING_FONT: _MENU_BOLD_FONT,
    EDITING_TEXT_COLOUR: COLOURS.YELLOW,
    EDITING_LABEL_FONT: _MENU_BASE_FONT,
    EDITING_LABEL_COLOUR: COLOURS.WHITE,
    EDITING_INFO_FONT: _MENU_BOLD_FONT,
    EDITING_INFO_COLOUR: COLOURS.GREEN,
    EDITING_WARNING_COLOUR: COLOURS.RED,
    EDITING_PASSWORD_BACKGROUND: COLOURS.PROPERLYDARKGRAY,

    // Highlighting selected items in menu tables
    HIGHLIGHT_BG_COLOUR: COLOURS.BLUE,

    // Popup screens
    POPUP_BG_COLOUR: COLOURS.BLACK,
    POPUP_BORDER_COLOUR: COLOURS.GRAY20,
    POPUP_BORDER_SIZE: 20,

    // Icons
    ICON_CAMCOPS: platform.translateFilename(_IM_PR + 'camcops.png'),
    ICON_INFO: platform.translateFilename(_IM_PR + 'info.png'),
    ICON_TABLE_CHILDARROW: platform.translateFilename(_IM_PR + 'hasChild.png'),
    ICON_TABLE_PARENTARROW: platform.translateFilename(_IM_PR +
                                                       'hasParent.png'),
    ICON_PATIENT_SUMMARY: platform.translateFilename(_IM_PR +
                                                     'patient_summary.png'),
    ICON_UPLOAD: platform.translateFilename(_IM_PR + 'upload.png'),
    ICON_CHOOSE_PATIENT: _ICON_CHOOSE_PATIENT, // see top for this one
    ICON_STOP: platform.translateFilename(_IM_PR + 'stop.png'),
    ICON_WARNING: platform.translateFilename(_IM_PR + 'warning.png'),
    ICON_READ_ONLY: platform.translateFilename(_IM_PR + 'read_only.png'),
    // Button icons
    ICON_UNLOCKED: platform.translateFilename(_IM_PR + 'unlocked.png'),
    ICON_UNLOCKED_T: platform.translateFilename(_IM_PR + 'unlocked_T.png'),
    ICON_LOCKED: platform.translateFilename(_IM_PR + 'locked.png'),
    ICON_LOCKED_T: platform.translateFilename(_IM_PR + 'locked_T.png'),
    ICON_PRIVILEGED: platform.translateFilename(_IM_PR + 'privileged.png'),
    ICON_PRIVILEGED_T: platform.translateFilename(_IM_PR + 'privileged_T.png'),
    ICON_EDIT: platform.translateFilename(_IM_PR + 'edit.png'),
    ICON_EDIT_T: platform.translateFilename(_IM_PR + 'edit_T.png'),
    ICON_OK: platform.translateFilename(_IM_PR + 'ok.png'),
    ICON_OK_T: platform.translateFilename(_IM_PR + 'ok_T.png'),
    ICON_CANCEL: platform.translateFilename(_IM_PR + 'cancel.png'),
    ICON_CANCEL_T: platform.translateFilename(_IM_PR + 'cancel_T.png'),
    ICON_RELOAD: platform.translateFilename(_IM_PR + 'reload.png'),
    ICON_RELOAD_T: platform.translateFilename(_IM_PR + 'reload_T.png'),
    ICON_ADD: platform.translateFilename(_IM_PR + 'add.png'),
    ICON_ADD_T: platform.translateFilename(_IM_PR + 'add_T.png'),
    ICON_DELETE: platform.translateFilename(_IM_PR + 'delete.png'),
    ICON_DELETE_T: platform.translateFilename(_IM_PR + 'delete_T.png'),
    ICON_ZOOM: platform.translateFilename(_IM_PR + 'zoom.png'),
    ICON_ZOOM_T: platform.translateFilename(_IM_PR + 'zoom_T.png'),
    ICON_BACK: platform.translateFilename(_IM_PR + 'back.png'),
    ICON_BACK_T: platform.translateFilename(_IM_PR + 'back_T.png'),
    ICON_NEXT: platform.translateFilename(_IM_PR + 'next.png'),
    ICON_NEXT_T: platform.translateFilename(_IM_PR + 'next_T.png'),
    ICON_FINISH: platform.translateFilename(_IM_PR + 'finish.png'),
    ICON_FINISH_T: platform.translateFilename(_IM_PR + 'finish_T.png'),
    ICON_CAMERA: platform.translateFilename(_IM_PR + 'camera.png'),
    ICON_CAMERA_T: platform.translateFilename(_IM_PR + 'camera_T.png'),
    ICON_ROTATE_CLOCKWISE: platform.translateFilename(
        _IM_PR + 'rotate_clockwise.png'
    ),
    ICON_ROTATE_CLOCKWISE_T: platform.translateFilename(
        _IM_PR + 'rotate_clockwise_T.png'
    ),
    ICON_ROTATE_ANTICLOCKWISE: platform.translateFilename(
        _IM_PR + 'rotate_anticlockwise.png'
    ),
    ICON_ROTATE_ANTICLOCKWISE_T: platform.translateFilename(
        _IM_PR + 'rotate_anticlockwise_T.png'
    ),
    ICON_SPEAKER: platform.translateFilename(_IM_PR + 'speaker.png'),
    ICON_SPEAKER_T: platform.translateFilename(_IM_PR + 'speaker_T.png'),
    ICON_SPEAKER_PLAYING: platform.translateFilename(
        _IM_PR + 'speaker_playing.png'
    ),
    ICON_SPEAKER_PLAYING_T: platform.translateFilename(
        _IM_PR + 'speaker_playing_T.png'
    ),
    ICON_FINISHFLAG: platform.translateFilename(_IM_PR + 'finishflag.png'),
    ICON_FINISHFLAG_T: platform.translateFilename(_IM_PR + 'finishflag_T.png'),
    ICON_CHOOSE_PAGE: platform.translateFilename(_IM_PR + 'choose_page.png'),
    ICON_CHOOSE_PAGE_T: platform.translateFilename(_IM_PR + 'choose_page_T.png'),
    // Menu icons
    ICON_MENU_ADDICTION: platform.translateFilename(_IM_PR + 'addiction.png'),
    ICON_MENU_AFFECTIVE: platform.translateFilename(_IM_PR + 'affective.png'),
    ICON_MENU_CATATONIA: platform.translateFilename(_IM_PR + 'catatonia.png'),
    ICON_MENU_CLINICAL: platform.translateFilename(_IM_PR + 'clinical.png'),
    ICON_MENU_COGNITIVE: platform.translateFilename(_IM_PR + 'cognitive.png'),
    ICON_MENU_EXECUTIVE: platform.translateFilename(_IM_PR + 'executive.png'),
    ICON_MENU_GLOBAL: platform.translateFilename(_IM_PR + 'global.png'),
    ICON_MENU_PERSONALITY: platform.translateFilename(_IM_PR +
                                                      'personality.png'),
    ICON_MENU_PSYCHOSIS: platform.translateFilename(_IM_PR + 'psychosis.png'),
    ICON_MENU_RESEARCH: platform.translateFilename(_IM_PR + 'research.png'),
    ICON_MENU_SETTINGS: platform.translateFilename(_IM_PR + 'settings.png'),
    ICON_MENU_ANONYMOUS: platform.translateFilename(_IM_PR + 'anonymous.png'),
    ICON_MENU_HELP: platform.translateFilename(_IM_PR + 'info.png'), // re-use
    ICON_MENU_SETS_CLINICAL: platform.translateFilename(_IM_PR +
                                                        'sets_clinical.png'),
    ICON_MENU_SETS_RESEARCH: platform.translateFilename(_IM_PR +
                                                        'sets_research.png'),
    ICON_MENU_ALLTASKS: platform.translateFilename(_IM_PR + 'alltasks.png'),
    ICON_CHAIN: platform.translateFilename(_IM_PR + 'chain.png'),

    //=========================================================================
    // Questionnaire
    //=========================================================================

    // Events
    EVENT_TO_ELEMENT: 'EVENT_TO_ELEMENT',

    // Fonts
    getVariableFont: getVariableFont,
    getVariableFontSpecifyingPercent: getVariableFontSpecifyingPercent,
    QUESTIONNAIRE_BASE_FONT_SIZE: QUESTIONNAIRE_BASE_FONT_SIZE,
    QUESTIONNAIRE_BIG_FONT_SIZE: QUESTIONNAIRE_BIG_FONT_SIZE,

    // Questionnaire buttons
    ICON_RADIO_DISABLED: platform.translateFilename(
        _IM_PR + 'radio_disabled.png'
    ),
    ICON_RADIO_UNSELECTED: platform.translateFilename(
        _IM_PR + 'radio_unselected.png'
    ),
    ICON_RADIO_UNSELECTED_T: platform.translateFilename(
        _IM_PR + 'radio_unselected_T.png'
    ),
    ICON_RADIO_UNSELECTED_REQUIRED: platform.translateFilename(
        _IM_PR + 'radio_unselected_required.png'
    ),
    ICON_RADIO_SELECTED: platform.translateFilename(
        _IM_PR + 'radio_selected.png'
    ),
    ICON_RADIO_SELECTED_T: platform.translateFilename(
        _IM_PR + 'radio_selected_T.png'
    ),

    ICON_CHECK_DISABLED: platform.translateFilename(
        _IM_PR + 'check_disabled.png'
    ),
    ICON_CHECK_UNSELECTED: platform.translateFilename(
        _IM_PR + 'check_unselected.png'
    ),
    ICON_CHECK_UNSELECTED_T: platform.translateFilename(
        _IM_PR + 'check_unselected_T.png'
    ),
    ICON_CHECK_UNSELECTED_REQUIRED: platform.translateFilename(
        _IM_PR + 'check_unselected_required.png'
    ),
    ICON_CHECK_FALSE_BLACK: platform.translateFilename(
        _IM_PR + 'check_false_black.png'
    ),
    ICON_CHECK_FALSE_BLACK_T: platform.translateFilename(
        _IM_PR + 'check_false_black_T.png'
    ),
    ICON_CHECK_FALSE_RED: platform.translateFilename(
        _IM_PR + 'check_false_red.png'
    ),
    ICON_CHECK_FALSE_RED_T: platform.translateFilename(
        _IM_PR + 'check_false_red_T.png'
    ),
    ICON_CHECK_TRUE_BLACK: platform.translateFilename(
        _IM_PR + 'check_true_black.png'
    ),
    ICON_CHECK_TRUE_BLACK_T: platform.translateFilename(
        _IM_PR + 'check_true_black_T.png'
    ),
    ICON_CHECK_TRUE_RED: platform.translateFilename(
        _IM_PR + 'check_true_red.png'
    ),
    ICON_CHECK_TRUE_RED_T: platform.translateFilename(
        _IM_PR + 'check_true_red_T.png'
    ),

    ICON_FIELD_INCOMPLETE_MANDATORY: platform.translateFilename(
        _IM_PR + 'field_incomplete_mandatory.png'
    ),
    ICON_FIELD_INCOMPLETE_OPTIONAL: platform.translateFilename(
        _IM_PR + 'field_incomplete_optional.png'
    ),
    ICON_FIELD_PROBLEM: platform.translateFilename(
        _IM_PR + 'field_problem.png'
    ),

    ICON_TIME_NOW: platform.translateFilename(_IM_PR + 'time_now.png'),
    ICON_TIME_NOW_T: platform.translateFilename(_IM_PR + 'time_now_T.png'),

    ICON_NEXT_IN_CHAIN: platform.translateFilename(_IM_PR +
                                                   'fast_forward.png'),
    ICON_NEXT_IN_CHAIN_T: platform.translateFilename(
        _IM_PR + 'fast_forward_T.png'
    ),
    ICON_WHISKER: platform.translateFilename(_IM_PR + 'whisker.png'),

    // Questionnaire
    READONLYVIEWFINISHED: -3,
    ABORTED: -2,
    PREVIOUSQUESTION: -1,
    FINISHED: 0,
    NEXTQUESTION: 1,

    QUESTIONNAIRE_BG_COLOUR: COLOURS.WHITE,
    QUESTIONNAIRE_BG_COLOUR_READONLY: COLOURS.WHITE,
    QUESTIONNAIRE_BG_COLOUR_CLINICIAN: COLOURS.PALEYELLOW,
    QUESTIONNAIRE_BG_COLOUR_CLINICIAN_READONLY: COLOURS.PALEYELLOW,
    QUESTIONNAIRE_BG_COLOUR_CONFIG: COLOURS.LAVENDER,
    getQuestionnaireFont: function (big, bold, italic) {
        return getVariableFont(
            big ? QUESTIONNAIRE_BIG_FONT_SIZE : QUESTIONNAIRE_BASE_FONT_SIZE,
            bold,
            italic
        );
    },
    QUESTIONNAIRE_HEADING_BG_COLOUR: COLOURS.LIGHTGRAY,
    QUESTIONNAIRE_SEARCHBAR_BG_COLOUR: COLOURS.WHITE,

    QUESTIONNAIRE_CHECKMARK_IMAGE_SIZE: 32,
    QUESTIONNAIRE_WARNING_IMAGE_SIZE: 32,
    QUESTIONNAIRE_BUTTON_TEXT_COLOR: COLOURS.BLUE,
    QUESTIONNAIRE_BUTTON_BG_COLOR: COLOURS.LIGHTGRAY,
    QUESTIONNAIRE_READONLY_BUTTON_TEXT_COLOR: COLOURS.GRAY,
    SOUND_COUNTDOWN_FINISHED: platform.translateFilename(
        'sounds/camcops/countdown_finished.wav'
    ),
    IOS7_BUTTON_TEXT_FLANKER_LEFT: "<",
    IOS7_BUTTON_TEXT_FLANKER_RIGHT: ">",

    ALIGN_TOP: 0,
    ALIGN_CENTRE: 1,

    // ANDROID_PICKER_SPINNER_HEIGHT: 200,

    QUESTIONNAIRE_HEADER_RULE_HEIGHT: 1,
    QUESTIONNAIRE_HEADER_RULE_COLOUR: COLOURS.GRAY,

    QUESTIONNAIRE_TITLE_COLOUR: COLOURS.GRAY,
    QUESTION_COLOUR: COLOURS.BLACK,
    ANSWER_COLOUR: COLOURS.BLACK,
    ANSWER_BACKGROUND_COLOUR: COLOURS.VERYLIGHTGREEN,
    ANSWER_BACKGROUND_COLOUR_READONLY: COLOURS.VERYLIGHTGREEN,
    ANSWER_BACKGROUND_COLOUR_REQUIRED: COLOURS.YELLOW,
    READONLY_ANSWER_COLOUR: COLOURS.DARKRED,
    WARNING_COLOUR: COLOURS.RED,

    KEYBOARD_VALIDATION_DELAY_MS: 250,
    // 500 makes you start wondering why the mandatory indicator hasn't gone
    // yet

    DIAGNOSTICCODE_BACKGROUND: COLOURS.PALEYELLOW,
    DIAGNOSTICCODE_TEXT: COLOURS.BLACK,
    DIAGNOSTICCODE_BACKGROUND_SELECTED: COLOURS.BLUE,
    DIAGNOSTICCODE_TEXT_SELECTED: COLOURS.WHITE,
    DIAGNOSTICCODE_INSTRUCTION: COLOURS.GRAY,
    DIAGNOSTICCODE_TEXT_FONT: _MENU_BOLD_FONT,
    DIAGNOSTICCODE_INSTRUCTION_FONT: _MENU_ITALIC_FONT,
    DIAGNOSTICCODE_GO_UP_FONT: _MENU_BIGBOLD_FONT,

    TEXTBUTTON_NULL_BG: COLOURS.LIGHTGRAY,
    TEXTBUTTON_NULL_FG: COLOURS.BLACK,
    TEXTBUTTON_NULL_REQUIRED_BG: COLOURS.YELLOW,
    TEXTBUTTON_NULL_REQUIRED_FG: COLOURS.BLACK,
    TEXTBUTTON_0_BG: COLOURS.BLACK,
    TEXTBUTTON_0_FG: COLOURS.WHITE,
    TEXTBUTTON_1_BG: COLOURS.BLUE, // red makes you think "error"
    TEXTBUTTON_1_FG: COLOURS.WHITE,

    // can't set cursor colour in TextField/TextArea?
    // Cursor is thin and white in Android.
    // can't set hint colour; hint is light grey in iOS;
    // http://developer.appcelerator.com/question/121236/how-do-you-change-a-hints-color-in-a-text-field
    // ... in other words, the framework wants a dark background.

    ANDROID_WIDGET_BACKGROUND_COLOUR: (
        _ANDROID_THEME_LIGHT ? COLOURS.WHITE : COLOURS.PROPERLYDARKGRAY
        // ... Android date things are transparent
        // Light themes: black text, need pale background
        // Dark themes: white text, need dark background
    ),
    INSTRUCTION_COLOUR: COLOURS.GRAY,
    GRID_TITLEROW_BACKGROUND: COLOURS.LIGHTGRAY,
    GRID_TITLEROW_COLOUR: COLOURS.BLACK,
    GRID_RULE_HEIGHT: 1,
    GRID_RULE_COLOUR: COLOURS.GRAY,
    getGridSubtitleFont: function () {
        return getVariableFont(QUESTIONNAIRE_BASE_FONT_SIZE, true);
    },
    // QUESTIONNAIRE_DATETIME_FORMAT: "YYYY-MM-DD HH:mm", // e.g. 2013-01-27 03:45
    // QUESTIONNAIRE_DATE_FORMAT: "YYYY-MM-DD", // e.g. 2012-09-30
    QUESTIONNAIRE_DATETIME_FORMAT: "DD MMM YYYY, HH:mm", // e.g. 04 Apr 2013, 13:28
    QUESTIONNAIRE_DATE_FORMAT: "DD MMM YYYY", // e.g. 04 Apr 2013

    getRadioFont: function () {
        return getVariableFont(QUESTIONNAIRE_BASE_FONT_SIZE, false);
    },
    RADIO_BUTTON_ICON_SIZE: 48, // 64?
    RADIO_TEXT_COLOUR: COLOURS.BLACK,

    ELEMENT_TYPE_RADIO: 'radio',
    ELEMENT_TYPE_BOOLEAN: 'boolean',

    TYPEDVAR_TEXT: 'text',
    TYPEDVAR_TEXT_MULTILINE: 'multiline',
    TYPEDVAR_INTEGER: 'integer',
    TYPEDVAR_BIGINT: 'bigint',
    TYPEDVAR_REAL: 'real',

    CANVAS_DEFAULT_STROKEWIDTH: 2, // in pixels? Float, supposedly.
    CANVAS_DEFAULT_STROKECOLOUR: COLOURS.BLUE,
    CANVAS_DEFAULT_STROKEALPHA: 255, // 0-255
    CANVAS_DEFAULT_IMAGEWIDTH: 600, // or Titanium.UI.FILL ?
    CANVAS_DEFAULT_IMAGEHEIGHT: 600, // or Titanium.UI.FILL ?

    //=========================================================================
    // Support files
    //=========================================================================

    BLACK_WHITE_TEST_HTML: platform.translateFilename('task_html/bwtest.html'),
    MISSING_TASKS_HTML: platform.translateFilename('html/MISSING_TASKS.html'),
    CAMCOPS_HTML: platform.translateFilename('html/camcops.html'),
    SOUND_TEST: platform.translateFilename('sounds/camcops/soundtest.wav'),

    //=========================================================================
    // Webview tasks: stimuli
    // Things only go here because they're shared between >1 task!
    //=========================================================================
    // Auditory stuff: handled in Titanium
    // Visual stuff: handled by the webview
    // ExpectationDetection and ExpDetThreshold
    EXPDET: {
        AUDITORY_BACKGROUND: platform.translateFilename(
            'sounds/expdet/A_background.wav'
        ),
        AUDITORY_CUES: [
            platform.translateFilename('sounds/expdet/A_cue_00_pluck.wav'),
            platform.translateFilename('sounds/expdet/A_cue_01_river.wav'),
            platform.translateFilename('sounds/expdet/A_cue_02_bird.wav'),
            platform.translateFilename('sounds/expdet/A_cue_03_morse.wav'),
            platform.translateFilename('sounds/expdet/A_cue_04_cymbal.wav'),
            platform.translateFilename('sounds/expdet/A_cue_05_match.wav'),
            platform.translateFilename('sounds/expdet/A_cue_06_metal.wav'),
            platform.translateFilename('sounds/expdet/A_cue_07_bach.wav')
        ],
        AUDITORY_TARGETS: [
            platform.translateFilename('sounds/expdet/A_target_0_tone.wav'),
            platform.translateFilename('sounds/expdet/A_target_1_voice.wav')
        ],
        VISUAL_BACKGROUND: platform.translateFilenameForWebView(
            'images/expdet/V_background.png'
        ),
        VISUAL_CUES: [
            platform.translateFilenameForWebView('images/expdet/V_cue_00.png'),
            platform.translateFilenameForWebView('images/expdet/V_cue_01.png'),
            platform.translateFilenameForWebView('images/expdet/V_cue_02.png'),
            platform.translateFilenameForWebView('images/expdet/V_cue_03.png'),
            platform.translateFilenameForWebView('images/expdet/V_cue_04.png'),
            platform.translateFilenameForWebView('images/expdet/V_cue_05.png'),
            platform.translateFilenameForWebView('images/expdet/V_cue_06.png'),
            platform.translateFilenameForWebView('images/expdet/V_cue_07.png')
        ],
        VISUAL_TARGETS: [
            platform.translateFilenameForWebView(
                'images/expdet/V_target_0_circle.png'
            ),
            platform.translateFilenameForWebView(
                'images/expdet/V_target_1_word.png'
            )
        ],
        STIM_SIZE: 400 // stimulus height and width
    }
};
