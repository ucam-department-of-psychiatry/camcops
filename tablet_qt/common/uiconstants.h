/*
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

#pragma once
#include <QColor>
#include <QMargins>
#include <QSize>
#include <QSizePolicy>
#include <QString>

namespace UiConst {

    // ========================================================================
    // Sizes, size policies
    // ========================================================================

    extern const QSize ICONSIZE;
    extern const QSize SMALL_ICONSIZE;
    extern const int SPACE;
    extern const int BIGSPACE;
    extern const int MEDIUMSPACE;
    extern const int HEADER_HLINE_WIDTH;
    extern const int QUESTIONNAIRE_HLINE_WIDTH;
    extern const int MCQGRID_VLINE_WIDTH;
    extern const int MCQGRID_VSPACING;
    extern const int MCQGRID_HSPACING;
    extern const int DEFAULT_COLSPAN_Q;
    extern const int DEFAULT_COLSPAN_A;

    extern const QMargins NO_MARGINS;

    // ========================================================================
    // Stylesheets
    // ========================================================================

    extern const QString CSS_CAMCOPS_MAIN;
    extern const QString CSS_CAMCOPS_MENU;
    extern const QString CSS_CAMCOPS_QUESTIONNAIRE;
    extern const QString CSS_CAMCOPS_CAMERA;
    extern const QString CSS_CAMCOPS_DIAGNOSTIC_CODE;

    // ========================================================================
    // Fonts, colours
    // ========================================================================

    enum class FontSize {
        Normal,
        Big,
        Title,
        Heading,
        Menus,
        Normal_x2,
    };

    extern const QString WARNING_COLOUR;

    extern const QColor BLACK_TRANSPARENT;
    extern const QColor BUTTON_UNPRESSED_COLOUR;
    extern const QColor BUTTON_PRESSED_COLOUR;
    extern const QColor BUTTON_DISABLED_COLOUR;
    extern const qreal DISABLED_ICON_OPACITY;

    // ========================================================================
    // Images
    // ========================================================================

    extern const QString ICON_ADDICTION;
    extern const QString ICON_AFFECTIVE;
    extern const QString ICON_ALLTASKS;
    extern const QString ICON_ANONYMOUS;
    extern const QString ICON_CAMCOPS;
    extern const QString ICON_CATATONIA;
    extern const QString ICON_CHAIN;
    extern const QString ICON_CHECK_DISABLED;
    extern const QString ICON_CHECK_UNSELECTED_REQUIRED;
    extern const QString ICON_CHOOSE_PATIENT;
    extern const QString ICON_CLINICAL;
    extern const QString ICON_COGNITIVE;
    extern const QString ICON_EXECUTIVE;
    extern const QString ICON_FIELD_INCOMPLETE_MANDATORY;
    extern const QString ICON_FIELD_INCOMPLETE_OPTIONAL;
    extern const QString ICON_FIELD_PROBLEM;
    extern const QString ICON_GLOBAL;
    extern const QString ICON_HASCHILD;
    extern const QString ICON_HASPARENT;
    extern const QString ICON_INFO;
    extern const QString ICON_PATIENT_SUMMARY;
    extern const QString ICON_PERSONALITY;
    extern const QString ICON_PSYCHOSIS;
    extern const QString ICON_RADIO_DISABLED;
    extern const QString ICON_RADIO_UNSELECTED_REQUIRED;
    extern const QString ICON_READ_ONLY;
    extern const QString ICON_RESEARCH;
    extern const QString ICON_SETS_CLINICAL;
    extern const QString ICON_SETS_RESEARCH;
    extern const QString ICON_SETTINGS;
    extern const QString ICON_STOP;
    extern const QString ICON_UPLOAD;
    extern const QString ICON_WARNING;
    extern const QString ICON_WHISKER;

    // CBS = CamCOPS button stem
    extern const QString CBS_ADD;
    extern const QString CBS_BACK;
    extern const QString CBS_CAMERA;
    extern const QString CBS_CANCEL;
    extern const QString CBS_CHOOSE_PAGE;
    extern const QString CBS_DELETE;
    extern const QString CBS_EDIT;
    extern const QString CBS_FAST_FORWARD;
    extern const QString CBS_FINISH;
    extern const QString CBS_FINISHFLAG;
    extern const QString CBS_LOCKED;
    extern const QString CBS_NEXT;
    extern const QString CBS_OK;
    extern const QString CBS_PRIVILEGED;
    extern const QString CBS_RELOAD;
    extern const QString CBS_ROTATE_ANTICLOCKWISE;
    extern const QString CBS_ROTATE_CLOCKWISE;
    extern const QString CBS_SPEAKER;
    extern const QString CBS_SPEAKER_PLAYING;
    extern const QString CBS_TIME_NOW;
    extern const QString CBS_UNLOCKED;
    extern const QString CBS_ZOOM;

    // ========================================================================
    // Sounds
    // ========================================================================

    extern const int MIN_VOLUME;
    extern const int MAX_VOLUME;
    extern const QString DEMO_SOUND_URL;
    extern const QString DEMO_SOUND_URL_2;
    extern const QString SOUND_COUNTDOWN_FINISHED;

    // ========================================================================
    // Common text
    // ========================================================================

    extern const QString NOT_SPECIFIED;

    extern const QString SEVERE;
    extern const QString MODERATELY_SEVERE;
    extern const QString MODERATE;
    extern const QString MILD;
    extern const QString NONE;

    extern const QString TERMS_CONDITIONS;

    // ========================================================================
    // Test text
    // ========================================================================

    extern const QString LOREM_IPSUM_1;
    extern const QString LOREM_IPSUM_2;

    // ========================================================================
    // Network
    // ========================================================================

    extern const int IP_PORT_MIN;
    extern const int IP_PORT_MAX;
    extern const int NETWORK_TIMEOUT_MS_MIN;
    extern const int NETWORK_TIMEOUT_MS_MAX;
}
