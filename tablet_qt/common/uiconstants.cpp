#include "uiconstants.h"
#include <QObject>  // for tr()

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
    const int QUESTIONNAIRE_HLINE_WIDTH = 2;
    const int MCQGRID_VLINE_WIDTH = 1;
    const int MCQGRID_VSPACING = 5;
    const int MCQGRID_HSPACING = 5;

    const QMargins NO_MARGINS(0, 0, 0, 0);

    // ========================================================================
    // Stylesheets
    // ========================================================================

    #define camcopsStylesheetFilename(filename) (":/resources/camcops/stylesheets/" filename)

    const QString CSS_CAMCOPS_MAIN(camcopsStylesheetFilename("main.css"));
    const QString CSS_CAMCOPS_MENU(camcopsStylesheetFilename("menu.css"));
    const QString CSS_CAMCOPS_QUESTIONNAIRE(camcopsStylesheetFilename(
                "questionnaire.css"));
    const QString CSS_CAMCOPS_CAMERA(camcopsStylesheetFilename("camera.css"));
    const QString CSS_CAMCOPS_DIAGNOSTIC_CODE(
            camcopsStylesheetFilename("diagnostic_code.css"));

    // ========================================================================
    // Fonts, colours
    // ========================================================================

    const QString WARNING_COLOUR("red");

    const QColor BLACK_TRANSPARENT(0, 0, 0, 0);  // a=0 means fully transparent
    const QColor BUTTON_UNPRESSED_COLOUR(127, 127, 127, 100);
    const QColor BUTTON_PRESSED_COLOUR(100, 100, 255, 200);
    const QColor BUTTON_DISABLED_COLOUR(127, 127, 127, 200);
    const qreal DISABLED_ICON_OPACITY = 0.5;

    // ========================================================================
    // Images
    // ========================================================================

    const QString ICON_ADDICTION("addiction.png");
    const QString ICON_AFFECTIVE("affective.png");
    const QString ICON_ALLTASKS("alltasks.png");
    const QString ICON_ANONYMOUS("anonymous.png");
    const QString ICON_CAMCOPS("camcops.png");
    const QString ICON_CATATONIA("catatonia.png");
    const QString ICON_CHAIN("chain.png");
    const QString ICON_CHOOSE_PATIENT("choose_patient.png");
    const QString ICON_CLINICAL("clinical.png");
    const QString ICON_COGNITIVE("cognitive.png");
    const QString ICON_EXECUTIVE("executive.png");
    const QString ICON_FIELD_INCOMPLETE_MANDATORY("field_incomplete_mandatory.png");
    const QString ICON_FIELD_INCOMPLETE_OPTIONAL("field_incomplete_optional.png");
    const QString ICON_FIELD_PROBLEM("field_problem.png");
    const QString ICON_GLOBAL("global.png");
    const QString ICON_HASCHILD("hasChild.png");
    const QString ICON_HASPARENT("hasParent.png");
    const QString ICON_INFO("info.png");
    const QString ICON_PATIENT_SUMMARY("patient_summary.png");
    const QString ICON_PERSONALITY("personality.png");
    const QString ICON_PSYCHOSIS("psychosis.png");
    const QString ICON_READ_ONLY("read_only.png");
    const QString ICON_RESEARCH("research.png");
    const QString ICON_SETS_CLINICAL("sets_clinical.png");
    const QString ICON_SETS_RESEARCH("sets_research.png");
    const QString ICON_SETTINGS("settings.png");
    const QString ICON_STOP("stop.png");
    const QString ICON_UPLOAD("upload.png");
    const QString ICON_WARNING("warning.png");
    const QString ICON_WHISKER("whisker.png");

    // Filename stems
    const QString CBS_ADD("add.png");
    const QString CBS_BACK("back.png");
    const QString CBS_CAMERA("camera.png");
    const QString CBS_CANCEL("cancel.png");
    const QString CBS_CHOOSE_PAGE("choose_page.png");
    const QString CBS_DELETE("delete.png");
    const QString CBS_EDIT("edit.png");
    const QString CBS_FAST_FORWARD("fast_forward.png");
    const QString CBS_FINISH("finish.png");
    const QString CBS_FINISHFLAG("finishflag.png");
    const QString CBS_LOCKED("locked.png");
    const QString CBS_NEXT("next.png");
    const QString CBS_OK("ok.png");
    const QString CBS_PRIVILEGED("privileged.png");
    const QString CBS_RELOAD("reload.png");
    const QString CBS_ROTATE_ANTICLOCKWISE("rotate_anticlockwise.png");
    const QString CBS_ROTATE_CLOCKWISE("rotate_clockwise.png");
    const QString CBS_SPEAKER("speaker.png");
    const QString CBS_SPEAKER_PLAYING("speaker_playing.png");
    const QString CBS_TIME_NOW("time_now.png");
    const QString CBS_UNLOCKED("unlocked.png");
    const QString CBS_ZOOM("zoom.png");

    // ========================================================================
    // Sounds
    // ========================================================================

    const int MIN_VOLUME = 0;
    const int MAX_VOLUME = 100;

    const QString DEMO_SOUND_URL("qrc:///resources/camcops/sounds/portal_still_alive.mp3");  // *** change; copyright
    const QString DEMO_SOUND_URL_2("qrc:///resources/camcops/sounds/soundtest.wav");  // *** change; copyright
    const QString SOUND_COUNTDOWN_FINISHED("qrc:///resources/camcops/sounds/countdown_finished.wav");

    // ========================================================================
    // Common text
    // ========================================================================

    const QString NOT_SPECIFIED(QObject::tr("<not specified>"));

    const QString SEVERE(QObject::tr("Severe"));
    const QString MODERATELY_SEVERE(QObject::tr("Moderately severe"));
    const QString MODERATE(QObject::tr("Moderate"));
    const QString MILD(QObject::tr("Mild"));
    const QString NONE(QObject::tr("None"));

    const QString TERMS_CONDITIONS(
        "1. By using the Cambridge Cognitive and Psychiatric Assessment Kit "
        "application or web interface (“CamCOPS”), you are agreeing in full "
        "to these Terms and Conditions of Use. If you do not agree to these "
        "terms, do not use the software.\n\n"
        "2. Content that is original to CamCOPS is licensed under the Apache "
        "License, Version 2.0 (the “License”); you may not use this software "
        "except in compliance with the License. You may obtain a copy of the "
        "License at\n\n"
        "    http://www.apache.org/licenses/LICENSE-2.0\n\n"
        "Unless required by applicable law or agreed to in writing, software "
        "distributed under the License is distributed on an “AS IS” BASIS, "
        "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or "
        "implied. See the License for the specific language governing "
        "permissions and limitations under the License.\n\n"
        "3. Content created by others and distributed with CamCOPS may be in "
        "the public domain, or distributed under other licenses or "
        "permissions. THERE MAY BE CRITERIA THAT APPLY TO YOU THAT MEAN YOU "
        "ARE NOT PERMITTED TO USE SPECIFIC TASKS. IT IS YOUR RESPONSIBILITY "
        "TO CHECK THAT YOU ARE LEGALLY ENTITLED TO USE EACH TASK. You agree "
        "that the authors of CamCOPS are not responsible for any consequences "
        "that arise from your use of an unauthorized task.\n\n"
        "4. While efforts have been made to ensure that CamCOPS is reliable "
        "and accurate, you agree that the authors and distributors of CamCOPS "
        "are not responsible for errors, omissions, or defects in the "
        "content, nor liable for any direct, indirect, incidental, special "
        "and/or consequential damages, in whole or in part, resulting from "
        "your use or any user’s use of or reliance upon its content.\n\n"
        "5. Content contained in or accessed through CamCOPS should not be "
        "relied upon for medical purposes in any way. This software is not "
        "designed for use by the general public. If medical advice is "
        "required you should seek expert medical assistance. You agree that "
        "you will not rely on this software for any medical purpose.\n\n"
        "6. Regarding the European Union Council Directive 93/42/EEC of 14 "
        "June 1993 concerning medical devices (amended by further directives "
        "up to and including Directive 2007/47/EC of 5 September 2007) "
        "(“Medical Devices Directive”): CamCOPS is not intended primarily for "
        "the diagnosis and/or monitoring of human disease. If it is used for "
        "such purposes, it must be used EXCLUSIVELY FOR CLINICAL "
        "INVESTIGATIONS in an appropriate setting by persons professionally "
        "qualified to do so. It has NOT undergone a conformity assessment "
        "under the Medical Devices Directive, and thus cannot be marketed or "
        "put into service as a medical device. You agree that you will not "
        "use it as a medical device.\n\n"
        "7. THIS SOFTWARE IS NOT DESIGNED FOR USE BY THE GENERAL PUBLIC. "
        "BY CONTINUING TO USE THIS SOFTWARE YOU ARE CONFIRMING THAT YOU ARE "
        "A CLINICIAN, AND THAT YOU RETAIN RESPONSIBILITY FOR DIAGNOSIS AND "
        "MANAGEMENT.\n\n"
        "These terms and conditions were last revised on 2016-11-29."
    );
    // ... *** change licence details to GPL

    // ========================================================================
    // Test text
    // ========================================================================

    const QString LOREM_IPSUM_1(  // http://www.lipsum.com/
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent "
        "sed cursus mauris. Ut vulputate felis quis dolor molestie convallis. "
        "Donec lectus diam, accumsan quis tortor at, congue laoreet augue. Ut "
        "mollis consectetur elit sit amet tincidunt. Vivamus facilisis, mi et "
        "eleifend ullamcorper, lorem metus faucibus ante, ut commodo urna "
        "neque bibendum magna. Lorem ipsum dolor sit amet, consectetur "
        "adipiscing elit. Praesent nec nisi ante. Sed vitae sem et eros "
        "elementum condimentum. Proin porttitor purus justo, sit amet "
        "vulputate velit imperdiet nec. Nam posuere ipsum id nunc accumsan "
        "tristique. Etiam pellentesque ornare tortor, a scelerisque dui "
        "accumsan ac. Ut tincidunt dolor ultrices, placerat urna nec, "
        "scelerisque mi."
    );
    const QString LOREM_IPSUM_2(
        "Nunc vitae neque eu odio feugiat consequat ac id neque. "
        "Suspendisse id libero massa."
    );

    // ========================================================================
    // Network
    // ========================================================================

    const int IP_PORT_MIN = 0;
    const int IP_PORT_MAX = 65536;
    const int NETWORK_TIMEOUT_MS_MIN = 100;
    const int NETWORK_TIMEOUT_MS_MAX = 5 * 60 * 1000;
}
