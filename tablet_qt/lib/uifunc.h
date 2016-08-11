#pragma once
#include <QAbstractButton>
#include <QLabel>
#include <QObject>
#include <QString>

#define iconFilename(filename) (":/images/camcops/" filename)
#define iconPngFilename(stem) iconFilename(stem ".png")
#define iconTouchedPngFilename(stem) iconFilename(stem "_T.png")

// ============================================================================
// QPixmap loader
// ============================================================================

QPixmap getPixmap(const QString& filename);

// ============================================================================
// Icons
// ============================================================================

QLabel* iconWidget(const QString& filename,
                   QWidget* parent = nullptr,
                   bool scale = true);


#define ICON_ADDICTION iconFilename("addiction.png")
#define ICON_ALLTASKS iconFilename("affective.png")
#define ICON_ANONYMOUS iconFilename("anonymous.png")
#define ICON_CAMCOPS iconFilename("camcops.png")
#define ICON_CATATONIA iconFilename("catatonia.png")
#define ICON_CHAIN iconFilename("chain.png")
#define ICON_CHECK_DISABLED iconFilename("check_disabled.png")
#define ICON_CHECK_UNSELECTED_REQUIRED iconFilename("check_unselected_required.png")
#define ICON_CHOOSE_PATIENT iconFilename("choose_patient.png")
#define ICON_CLINICAL iconFilename("clinical.png")
#define ICON_COGNITIVE iconFilename("cognitive.png")
#define ICON_EXECUTIVE iconFilename("executive.png")
#define ICON_FIELD_INCOMPLETE_MANDATORY iconFilename("field_incomplete_mandatory.png")
#define ICON_FIELD_INCOMPLETE_OPTIONAL iconFilename("field_incomplete_optional.png")
#define ICON_FIELD_PROBLEM iconFilename("field_problem.png")
#define ICON_GLOBAL iconFilename("global.png")
#define ICON_HASCHILD iconFilename("hasChild.png")
#define ICON_HASPARENT iconFilename("hasParent.png")
#define ICON_INFO iconFilename("info.png")
#define ICON_PATIENT_SUMMARY iconFilename("patient_summary.png")
#define ICON_PERSONALITY iconFilename("personality.png")
#define ICON_PSYCHOSIS iconFilename("psychosis.png")
#define ICON_RADIO_DISABLED iconFilename("radio_disabled.png")
#define ICON_RADIO_UNSELECTED_REQUIRED iconFilename("radio_unselected_required.png")
#define ICON_READ_ONLY iconFilename("read_only.png")
#define ICON_RESEARCH iconFilename("research.png")
#define ICON_SETS_CLINICAL iconFilename("sets_clinical.png")
#define ICON_SETS_RESEARCH iconFilename("sets_research.png")
#define ICON_SETTINGS iconFilename("settings.png")
#define ICON_STOP iconFilename("stop.png")
#define ICON_UPLOAD iconFilename("upload.png")
#define ICON_WARNING iconFilename("warning.png")
#define ICON_WHISKER iconFilename("whisker.png")

// ============================================================================
// Buttons
// ============================================================================

QAbstractButton* iconButton(const QString& normal_filename,
                            const QString& pressed_filename = "",
                            QWidget* parent = nullptr);

#define makeIconButton(stem, parent) \
    iconButton(iconPngFilename(stem), iconTouchedPngFilename(stem), parent)

#define CAMCOPS_BUTTON_ADD(p) makeIconButton("add", p)
#define CAMCOPS_BUTTON_BACK(p) makeIconButton("back", p)
#define CAMCOPS_BUTTON_CAMERA(p) makeIconButton("camera", p)
#define CAMCOPS_BUTTON_CANCEL(p) makeIconButton("cancel", p)
#define CAMCOPS_BUTTON_CHECK_FALSE_BLACK(p) makeIconButton("check_false_black", p)
#define CAMCOPS_BUTTON_CHECK_FALSE_RED(p) makeIconButton("check_false_red", p)
#define CAMCOPS_BUTTON_CHECK_TRUE_BLACK(p) makeIconButton("check_true_black", p)
#define CAMCOPS_BUTTON_CHECK_TRUE_RED(p) makeIconButton("check_true_red", p)
#define CAMCOPS_BUTTON_CHECK_UNSELECTED(p) makeIconButton("check_unselected", p)
#define CAMCOPS_BUTTON_CHOOSE_PAGE(p) makeIconButton("choose_page", p)
#define CAMCOPS_BUTTON_DELETE(p) makeIconButton("delete", p)
#define CAMCOPS_BUTTON_EDIT(p) makeIconButton("edit", p)
#define CAMCOPS_BUTTON_FAST_FORWARD(p) makeIconButton("fast_forward", p)
#define CAMCOPS_BUTTON_FINISH(p) makeIconButton("finish", p)
#define CAMCOPS_BUTTON_FINISHFLAG(p) makeIconButton("finishflag", p)
#define CAMCOPS_BUTTON_LOCKED(p) makeIconButton("locked", p)
#define CAMCOPS_BUTTON_NEXT(p) makeIconButton("next", p)
#define CAMCOPS_BUTTON_OK(p) makeIconButton("ok", p)
#define CAMCOPS_BUTTON_PRIVILEGED(p) makeIconButton("privileged", p)
#define CAMCOPS_BUTTON_RADIO_SELECTED(p) makeIconButton("radio_selected", p)
#define CAMCOPS_BUTTON_RADIO_UNSELECTED(p) makeIconButton("radio_unselected", p)
#define CAMCOPS_BUTTON_RELOAD(p) makeIconButton("reload", p)
#define CAMCOPS_BUTTON_ROTATE_ANTICLOCKWISE(p) makeIconButton("rotate_anticlockwise", p)
#define CAMCOPS_BUTTON_ROTATE_CLOCKWISE(p) makeIconButton("rotate_clockwise", p)
#define CAMCOPS_BUTTON_SPEAKER(p) makeIconButton("speaker", p)
#define CAMCOPS_BUTTON_SPEAKER_PLAYING(p) makeIconButton("speaker_playing", p)
#define CAMCOPS_BUTTON_TIME_NOW(p) makeIconButton("time_now", p)
#define CAMCOPS_BUTTON_UNLOCKED(p) makeIconButton("unlocked", p)
#define CAMCOPS_BUTTON_ZOOM(p) makeIconButton("zoom", p)


// ============================================================================
// Killing the app
// ============================================================================

void stopApp(const QString& error);

// ============================================================================
// Alerts
// ============================================================================

void alert(const QString& text, const QString& title = QObject::tr("Alert"));
