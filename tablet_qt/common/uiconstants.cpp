#include "uiconstants.h"

namespace UiConst {

    // ========================================================================
    // Sizes
    // ========================================================================

    const QSize ICONSIZE(48, 48);
    const QSize SMALL_ICONSIZE(24, 24);
    const int SPACE = 4;
    const int BIGSPACE = 16;
    const int MEDIUMSPACE = 8;
    const int HEADER_HLINE_WIDTH = 3;
    const int QUESTIONNAIRE_HLINE_WIDTH = 1;

    // ========================================================================
    // Stylesheets
    // ========================================================================

    #define stylesheetFilename(filename) (":/stylesheets/" filename)

    const QString CSS_CAMCOPS = stylesheetFilename("camcops.css");
    const QString CSS_CAMCOPS_MENU = stylesheetFilename("camcops_menu.css");
    const QString CSS_CAMCOPS_QUESTIONNAIRE = stylesheetFilename("camcops_questionnaire.css");

    // ========================================================================
    // Fonts, colours
    // ========================================================================

    const QString WARNING_COLOUR = "red";

    const QColor BLACK_TRANSPARENT(0, 0, 0, 0);  // a=0 means fully transparent
    const QColor BUTTON_UNPRESSED_COLOUR(127, 127, 127, 100);
    const QColor BUTTON_PRESSED_COLOUR(100, 100, 255, 200);
    const QColor BUTTON_DISABLED_COLOUR(127, 127, 127, 200);
    const qreal DISABLED_ICON_OPACITY = 0.5;

    // ========================================================================
    // Images
    // ========================================================================

    const QString ICON_ADDICTION = "addiction.png";
    const QString ICON_AFFECTIVE = "affective.png";
    const QString ICON_ALLTASKS = "alltasks.png";
    const QString ICON_ANONYMOUS = "anonymous.png";
    const QString ICON_CAMCOPS = "camcops.png";
    const QString ICON_CATATONIA = "catatonia.png";
    const QString ICON_CHAIN = "chain.png";
    const QString ICON_CHOOSE_PATIENT = "choose_patient.png";
    const QString ICON_CLINICAL = "clinical.png";
    const QString ICON_COGNITIVE = "cognitive.png";
    const QString ICON_EXECUTIVE = "executive.png";
    const QString ICON_FIELD_INCOMPLETE_MANDATORY = "field_incomplete_mandatory.png";
    const QString ICON_FIELD_INCOMPLETE_OPTIONAL = "field_incomplete_optional.png";
    const QString ICON_FIELD_PROBLEM = "field_problem.png";
    const QString ICON_GLOBAL = "global.png";
    const QString ICON_HASCHILD = "hasChild.png";
    const QString ICON_HASPARENT = "hasParent.png";
    const QString ICON_INFO = "info.png";
    const QString ICON_PATIENT_SUMMARY = "patient_summary.png";
    const QString ICON_PERSONALITY = "personality.png";
    const QString ICON_PSYCHOSIS = "psychosis.png";
    const QString ICON_READ_ONLY = "read_only.png";
    const QString ICON_RESEARCH = "research.png";
    const QString ICON_SETS_CLINICAL = "sets_clinical.png";
    const QString ICON_SETS_RESEARCH = "sets_research.png";
    const QString ICON_SETTINGS = "settings.png";
    const QString ICON_STOP = "stop.png";
    const QString ICON_UPLOAD = "upload.png";
    const QString ICON_WARNING = "warning.png";
    const QString ICON_WHISKER = "whisker.png";

    // Filename stems
    const QString CBS_ADD = "add.png";
    const QString CBS_BACK = "back.png";
    const QString CBS_CAMERA = "camera.png";
    const QString CBS_CANCEL = "cancel.png";
    const QString CBS_CHOOSE_PAGE = "choose_page.png";
    const QString CBS_DELETE = "delete.png";
    const QString CBS_EDIT = "edit.png";
    const QString CBS_FAST_FORWARD = "fast_forward.png";
    const QString CBS_FINISH = "finish.png";
    const QString CBS_FINISHFLAG = "finishflag.png";
    const QString CBS_LOCKED = "locked.png";
    const QString CBS_NEXT = "next.png";
    const QString CBS_OK = "ok.png";
    const QString CBS_PRIVILEGED = "privileged.png";
    const QString CBS_RELOAD = "reload.png";
    const QString CBS_ROTATE_ANTICLOCKWISE = "rotate_anticlockwise.png";
    const QString CBS_ROTATE_CLOCKWISE = "rotate_clockwise.png";
    const QString CBS_SPEAKER = "speaker.png";
    const QString CBS_SPEAKER_PLAYING = "speaker_playing.png";
    const QString CBS_TIME_NOW = "time_now.png";
    const QString CBS_UNLOCKED = "unlocked.png";
    const QString CBS_ZOOM = "zoom.png";

    // ========================================================================
    // Sounds
    // ========================================================================

    const int MIN_VOLUME = 0;
    const int MAX_VOLUME = 100;

    const QString DEMO_SOUND_URL = "qrc:///sounds/camcops/portal_still_alive.mp3";  // *** change; copyright
    const QString DEMO_SOUND_URL_2 = "qrc:///sounds/camcops/soundtest.wav";  // *** change; copyright
    const QString SOUND_COUNTDOWN_FINISHED = "qrc:///sounds/camcops/countdown_finished.wav";

}
