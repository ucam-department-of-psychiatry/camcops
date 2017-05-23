/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

/*

===============================================================================
Comments
===============================================================================

- Sounds: originals (Rogers 1999 Psychopharm 146:482) were:
    correct = 1200 Hz, 164 ms, volume not given
    incorrect = 200 Hz, 550 ms, volume not given
  However, on the tablet, using the Audacity tone generator with the same
  parameters (in other respects) for the stimuli, makes the incorrect one
  nearly inaudible. So let's use different notes.
- Actual source in my chord.py. All are sine waves.
    correct = E5 + G5 + C6 (Cmaj), 164 ms
    incorrect = A4 + C5 + Eb5 + F#5 (Adim7), 550 ms

- Any further control required over over exact values used for shape/colour/
  number?

*/

#include "ided3d.h"
#include <functional>
#include <QDebug>
#include <QGraphicsScene>
#include <QGraphicsView>
#include <QPen>
#include <QPushButton>
#include "common/textconst.h"
#include "db/ancillaryfunc.h"
#include "lib/datetime.h"
#include "lib/graphicsfunc.h"
#include "lib/mathfunc.h"
#include "lib/random.h"
#include "lib/stringfunc.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "widgets/adjustablepie.h"
#include "widgets/svgwidgetclickable.h"
#include "widgets/openablewidget.h"
using ccrandom::coin;
using datetime::now;
using graphicsfunc::ButtonAndProxy;
using graphicsfunc::ButtonConfig;
using graphicsfunc::LabelAndProxy;
using graphicsfunc::makeSvg;
using graphicsfunc::makeText;
using graphicsfunc::makeTextButton;
using graphicsfunc::SvgWidgetAndProxy;
using graphicsfunc::TextConfig;
using stringfunc::replaceFirst;


// ============================================================================
// Constants
// ============================================================================

// Table names
const QString IDED3D::IDED3D_TABLENAME("ided3d");
const QString IDED3D::Stage::STAGE_TABLENAME("ided3d_stages");
const QString IDED3D::Trial::TRIAL_TABLENAME("ided3d_trials");

// Fieldnames: IDED3D
const QString IDED3D::FN_LAST_STAGE("last_stage");
const QString IDED3D::FN_MAX_TRIALS_PER_STAGE("max_trials_per_stage");
const QString IDED3D::FN_PROGRESS_CRITERION_X("progress_criterion_x");
const QString IDED3D::FN_PROGRESS_CRITERION_Y("progress_criterion_y");
const QString IDED3D::FN_MIN_NUMBER("min_number");
const QString IDED3D::FN_MAX_NUMBER("max_number");
const QString IDED3D::FN_PAUSE_AFTER_BEEP_MS("pause_after_beep_ms");
const QString IDED3D::FN_ITI_MS("iti_ms");
const QString IDED3D::FN_COUNTERBALANCE_DIMENSIONS("counterbalance_dimensions");
const QString IDED3D::FN_VOLUME("volume");
const QString IDED3D::FN_OFFER_ABORT("offer_abort");
const QString IDED3D::FN_DEBUG_DISPLAY_STIMULI_ONLY("debug_display_stimuli_only");
const QString IDED3D::FN_SHAPE_DEFINITIONS_SVG("shape_definitions_svg");
const QString IDED3D::FN_ABORTED("aborted");
const QString IDED3D::FN_FINISHED("finished");
const QString IDED3D::FN_LAST_TRIAL_COMPLETED("last_trial_completed");

// Fieldnames: Stage
const QString IDED3D::Stage::FN_FK_TO_TASK("ided3d_id");
const QString IDED3D::Stage::FN_STAGE("stage");
const QString IDED3D::Stage::FN_STAGE_NAME("stage_name");
const QString IDED3D::Stage::FN_RELEVANT_DIMENSION("relevant_dimension");
const QString IDED3D::Stage::FN_CORRECT_EXEMPLAR("correct_exemplar");
const QString IDED3D::Stage::FN_INCORRECT_EXEMPLAR("incorrect_exemplar");
const QString IDED3D::Stage::FN_CORRECT_STIMULUS_SHAPES("correct_stimulus_shapes");
const QString IDED3D::Stage::FN_CORRECT_STIMULUS_COLOURS("correct_stimulus_colours");
const QString IDED3D::Stage::FN_CORRECT_STIMULUS_NUMBERS("correct_stimulus_numbers");
const QString IDED3D::Stage::FN_INCORRECT_STIMULUS_SHAPES("incorrect_stimulus_shapes");
const QString IDED3D::Stage::FN_INCORRECT_STIMULUS_COLOURS("incorrect_stimulus_colours");
const QString IDED3D::Stage::FN_INCORRECT_STIMULUS_NUMBERS("incorrect_stimulus_numbers");
const QString IDED3D::Stage::FN_FIRST_TRIAL_NUM("first_trial_num");
const QString IDED3D::Stage::FN_N_COMPLETED_TRIALS("n_completed_trials");
const QString IDED3D::Stage::FN_N_CORRECT("n_correct");
const QString IDED3D::Stage::FN_N_INCORRECT("n_incorrect");
const QString IDED3D::Stage::FN_STAGE_PASSED("stage_passed");
const QString IDED3D::Stage::FN_STAGE_FAILED("stage_failed");

// Fieldnames: Trial
const QString IDED3D::Trial::FN_FK_TO_TASK("ided3d_id");
const QString IDED3D::Trial::FN_TRIAL("trial");
const QString IDED3D::Trial::FN_STAGE("stage");
const QString IDED3D::Trial::FN_CORRECT_LOCATION("correct_location");
const QString IDED3D::Trial::FN_INCORRECT_LOCATION("incorrect_location");
const QString IDED3D::Trial::FN_CORRECT_SHAPE("correct_shape");
const QString IDED3D::Trial::FN_CORRECT_COLOUR("correct_colour");
const QString IDED3D::Trial::FN_CORRECT_NUMBER("correct_number");
const QString IDED3D::Trial::FN_INCORRECT_SHAPE("incorrect_shape");
const QString IDED3D::Trial::FN_INCORRECT_COLOUR("incorrect_colour");
const QString IDED3D::Trial::FN_INCORRECT_NUMBER("incorrect_number");
const QString IDED3D::Trial::FN_TRIAL_START_TIME("trial_start_time");
const QString IDED3D::Trial::FN_RESPONDED("responded");
const QString IDED3D::Trial::FN_RESPONSE_TIME("response_time");
const QString IDED3D::Trial::FN_RESPONSE_LATENCY_MS("response_latency_ms");
const QString IDED3D::Trial::FN_CORRECT("correct");
const QString IDED3D::Trial::FN_INCORRECT("incorrect");

// Questionnaire bit
const QString TAG_WARNING_PROGRESS_CRITERION("pc");
const QString TAG_WARNING_MIN_MAX("mm");

// Strings shown to the user


// Graphics
const qreal SCENE_WIDTH = 1000;
const qreal SCENE_HEIGHT = 750;  // 4:3 aspect ratio
const QColor SCENE_BACKGROUND("black");  // try: "salmon"
const int BORDER_WIDTH_PX = 3;
const QColor BUTTON_BACKGROUND("blue");
const QColor TEXT_COLOUR("white");
const QColor BUTTON_PRESSED_BACKGROUND("olive");
const QColor ABORT_BUTTON_BACKGROUND("darkred");
const qreal TEXT_SIZE_PX = 20;  // will be scaled
const int BUTTON_RADIUS = 5;
const int PADDING = 5;
const Qt::Alignment BUTTON_TEXT_ALIGN = Qt::AlignCenter;
const Qt::Alignment TEXT_ALIGN = Qt::AlignCenter;
const int STIMSIZE = 120;  // max width/height
const int STIM_STROKE_WIDTH = 3;

// Dimensions
const QString DIM_SHAPE("shape");
const QString DIM_COLOUR("colour");
const QString DIM_NUMBER("number");

// Shapes
const QStringList SHAPE_DEFINITIONS{
    /*
        List of paths.
        MULTI.PAT contained 96, but were only 12 things repeated 8 times.
        All stimuli redrawn.
        Good online editor:
            http://jsfiddle.net/DFhUF/1393/
        ... being jsfiddle set to the Raphael 2.1.0 framework "onLoad".
        Code:

var path = [
    // DETAILS HERE
    ["m10,-53 l20,100 l-60,0 z m50,60 l-120,20 l0,-50 z"], // 0: up-pointing triangle and right-pointing triangle
    ["m0,-50 l-57,57 l28,28 l28,-28 l28,28 l28,-28 z"], // 1: stealth bomber flying up
    ["m-15,-50 l-45,25 l90,0 z m15,35 l-45,25 l90,0 z m15,35 l-45,25 l90,0 z"], // 2: stacked triangle hats slightly offset horizontally
    ["m-60,-11 l94,55 l26,-28 l-38,-15 l38,-15 l-26,-28 l-94,55 z"], // 3: small-tailed fish with gaping mouth pointing right
    ["m-20,-50 l-40,50 l45,0 l0,50 l30,0 l0,-50 l45,0 l-45,-50 z"], // 4: top-truncated tree
    ["m-60,-36 l120,0 l0,72 l-40,0 l0,-36 l-40,0 l0,36, l-40,0 z"], // 5: side view of block table, or blocky inverted U
    ["m0,-40 l60,40 l-40,27 l0,13 l-40,0 l0,-13 l-40,-27 z"], // 6: diamond-like tree
    ["m-33,40 l-27,-40 l27,-40 l33,27 l33,-27 l27,40 l-27,40 l-33,-27 z"], // 7: bow tie
    ["m-60,-30 l60,-30 l60,30 l0,60 l-60,30 l-60,-30 z"], // 8: hexagon
    ["m-60,60 l120,0 l-60,-60 z m0,-120 l120,0 l-60,60 z"], // 9: hourglass of triangles
    ["m-60,-40 l0,68 l120,0 l-45,-30 l0,11 l-45,-38 l0,23 z"], // 10: mountain range
    ["m-60,0 l34,-43 l86,0 l-34,43 l34,43 l-86,0 z"], // 11: left-pointing arrow feathers
],
index = 10,  // currently working on this one
s = 120,  // target size; width and height
c = 250,  // centre
paper = Raphael(0, 0, c*2, c*2),
crosshairs = ["M", 0, c, "L", c*2, c, "M", c, 0,  "L", c, c*2],
chattr = {stroke: "#f00", opacity: 1, "stroke-width" : 1},
gridattr = {stroke: "#888", opacity: 0.5, "stroke-width" : 1},
textattr = {fill: "red", font: "20px Arial", "text-anchor": "middle"},
pathattr = {stroke: "#808", opacity: 1, "stroke-width" : 1, fill: "#ccf"},
i;
paper.path(path[index]).translate(c, c).attr(pathattr);
for (i = 0; i < 2*c; i += 10) {
paper.path(["M", 0, i, "L", 2*c, i]).attr(gridattr);
paper.path(["M", i, 0, "L", i, 2*c]).attr(gridattr);
}
paper.rect(c - s/2, c - s/2, s, s).attr(chattr);
paper.path(crosshairs).attr(chattr);
paper.text(c, c, "0").attr(textattr);

    */

    // 0: up-pointing triangle and right-pointing triangle
    "m10,-53 l20,100 l-60,0 z m50,60 l-120,20 l0,-50 z",

    // 1: stealth bomber flying up
    "m0,-50 l-57,57 l28,28 l28,-28 l28,28 l28,-28 z",

    // 2: stacked triangle hats slightly offset horizontally
    "m-15,-50 l-45,25 l90,0 z m15,35 l-45,25 l90,0 z m15,35 l-45,25 l90,0 z",

    // 3: small-tailed fish with gaping mouth pointing right
    "m-60,-11 l94,55 l26,-28 l-38,-15 l38,-15 l-26,-28 l-94,55 z",

    // 4: top-truncated tree
    "m-20,-50 l-40,50 l45,0 l0,50 l30,0 l0,-50 l45,0 l-45,-50 z",

    // 5: side view of block table, or blocky inverted U
    "m-60,-36 l120,0 l0,72 l-40,0 l0,-36 l-40,0 l0,36, l-40,0 z",

    // 6: diamond-like tree
    "m0,-40 l60,40 l-40,27 l0,13 l-40,0 l0,-13 l-40,-27 z",

    // 7: bow tie
    "m-33,40 l-27,-40 l27,-40 l33,27 l33,-27 l27,40 l-27,40 l-33,-27 z",

    // 8: hexagon
    "m-60,-30 l60,-30 l60,30 l0,60 l-60,30 l-60,-30 z",

    // 9: hourglass of triangles
    "m-60,60 l120,0 l-60,-60 z m0,-120 l120,0 l-60,60 z",

    // 10: mountain range
    "m-60,-40 l0,68 l120,0 l-45,-30 l0,11 l-45,-38 l0,23 z",

    // 11: left-pointing arrow feathers
    "m-60,0 l34,-43 l86,0 l-34,43 l34,43 l-86,0 z",
};

// Colours
const QVector<QColor> POSSIBLE_COLOURS{
    // HTML colour definitions of CGA colours
    QColor("#555"), // CGA: dark grey
    QColor("#55f"), // CGA: light blue
    QColor("#5f5"), // CGA: light green
    QColor("#5ff"), // CGA: light cyan
    QColor("#f55"), // CGA: light red
    QColor("#f5f"), // CGA: light magenta
    QColor("#ff5"), // CGA: yellow
    QColor("#fff"), // white
};
const QColor TEST_COLOUR("purple");

// Sound
const QString SOUND_FILE_CORRECT("ided3d/correct.wav");
const QString SOUND_FILE_INCORRECT("ided3d/incorrect.wav");
const qreal MIN_VOLUME = 0.0;
const qreal MAX_VOLUME = 1.0;  // NOTE: for Qt, need to scale volume to 0-100
const int VOLUME_DP = 2;

// Task constants
const int MAX_STAGES = 8;
const int MAX_NUMBER = 9;
const int MAX_COUNTERBALANCE_DIMENSIONS = 5;
const int DEFAULT_MAX_TRIALS_PER_STAGE = 50;
const int DEFAULT_PROGRESS_CRITERION_X = 6;  // as per Rogers et al. 1999
const int DEFAULT_PROGRESS_CRITERION_Y = 6;  // as per Rogers et al. 1999
const int DEFAULT_PAUSE_AFTER_BEEP_MS = 500;
const int DEFAULT_ITI_MS = 500;
const qreal DEFAULT_VOLUME = MAX_VOLUME;
const bool DEFAULT_OFFER_ABORT = false;

// Derived constants
const QRectF SCENE_RECT(0, 0, SCENE_WIDTH, SCENE_HEIGHT);
const TextConfig BASE_TEXT_CONFIG(TEXT_SIZE_PX, TEXT_COLOUR,
                                  SCENE_WIDTH, TEXT_ALIGN);


// ============================================================================
// Factory method
// ============================================================================

void initializeIDED3D(TaskFactory& factory)
{
    static TaskRegistrar<IDED3D> registered(factory);
}


// ============================================================================
// Trial
// ============================================================================

IDED3D::Trial::Trial(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    DatabaseObject(app, db, TRIAL_TABLENAME)
{
    addField(FN_FK_TO_TASK, QVariant::Int);
    // More keys
    addField(FN_TRIAL, QVariant::Int, true);  // 1-based trial number within this session
    addField(FN_STAGE, QVariant::Int, true);
    // Locations
    addField(FN_CORRECT_LOCATION, QVariant::Int);
    addField(FN_INCORRECT_LOCATION, QVariant::Int);
    // Stimuli
    addField(FN_CORRECT_SHAPE, QVariant::Int);
    addField(FN_CORRECT_COLOUR, QVariant::String);
    addField(FN_CORRECT_NUMBER, QVariant::Int);
    addField(FN_INCORRECT_SHAPE, QVariant::Int);
    addField(FN_INCORRECT_COLOUR, QVariant::String);
    addField(FN_INCORRECT_NUMBER, QVariant::Int);
    // Trial
    addField(FN_TRIAL_START_TIME, QVariant::DateTime);
    // Response
    addField(FN_RESPONDED, QVariant::Bool);
    addField(FN_RESPONSE_TIME, QVariant::DateTime);
    addField(FN_RESPONSE_LATENCY_MS, QVariant::Int);
    addField(FN_CORRECT, QVariant::Bool);
    addField(FN_INCORRECT, QVariant::Bool);

    load(load_pk);
}


// ============================================================================
// Stage
// ============================================================================

IDED3D::Stage::Stage(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    DatabaseObject(app, db, STAGE_TABLENAME)
{
    addField(FN_FK_TO_TASK, QVariant::Int);
    // More keys
    addField(FN_STAGE, QVariant::Int, true);  // 1-based stage number within this session
    // Config
    addField(FN_STAGE_NAME, QVariant::String);
    addField(FN_RELEVANT_DIMENSION, QVariant::String);
    addField(FN_CORRECT_EXEMPLAR, QVariant::String);
    addField(FN_INCORRECT_EXEMPLAR, QVariant::String);
    addField(FN_CORRECT_STIMULUS_SHAPES, QVariant::String);
    addField(FN_CORRECT_STIMULUS_COLOURS, QVariant::String);
    addField(FN_CORRECT_STIMULUS_NUMBERS, QVariant::String);
    addField(FN_INCORRECT_STIMULUS_SHAPES, QVariant::String);
    addField(FN_INCORRECT_STIMULUS_COLOURS, QVariant::String);
    addField(FN_INCORRECT_STIMULUS_NUMBERS, QVariant::String);
    // Results
    addField(FN_FIRST_TRIAL_NUM, QVariant::Int);  // 1-based
    addField(FN_N_COMPLETED_TRIALS, QVariant::Int);
    addField(FN_N_CORRECT, QVariant::Int);
    addField(FN_N_INCORRECT, QVariant::Int);
    addField(FN_STAGE_PASSED, QVariant::Bool);
    addField(FN_STAGE_FAILED, QVariant::Bool);

    load(load_pk);
}


// ============================================================================
// IDED3D
// ============================================================================

IDED3D::IDED3D(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, IDED3D_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    // Config
    addField(FN_LAST_STAGE, QVariant::Int);
    addField(FN_MAX_TRIALS_PER_STAGE, QVariant::Int);
    addField(FN_PROGRESS_CRITERION_X, QVariant::Int);
    addField(FN_PROGRESS_CRITERION_Y, QVariant::Int);
    addField(FN_MIN_NUMBER, QVariant::Int);
    addField(FN_MAX_NUMBER, QVariant::Int);
    addField(FN_PAUSE_AFTER_BEEP_MS, QVariant::Int);
    addField(FN_ITI_MS, QVariant::Int);
    addField(FN_COUNTERBALANCE_DIMENSIONS, QVariant::Int);
    addField(FN_VOLUME, QVariant::Double);
    addField(FN_OFFER_ABORT, QVariant::Bool);
    addField(FN_DEBUG_DISPLAY_STIMULI_ONLY, QVariant::Bool);
    addField(FN_SHAPE_DEFINITIONS_SVG, QVariant::String);
    // Results
    addField(FN_ABORTED, QVariant::Bool);
    getField(FN_ABORTED).setDefaultValue(false);
    addField(FN_FINISHED, QVariant::Bool);
    getField(FN_FINISHED).setDefaultValue(false);
    addField(FN_LAST_TRIAL_COMPLETED, QVariant::Int);

    load(load_pk);

    if (load_pk == dbconst::NONEXISTENT_PK) {
        // Default values:
        setValue(FN_LAST_STAGE, MAX_STAGES);
        setValue(FN_MAX_TRIALS_PER_STAGE, DEFAULT_MAX_TRIALS_PER_STAGE);
        setValue(FN_PROGRESS_CRITERION_X, DEFAULT_PROGRESS_CRITERION_X);
        setValue(FN_PROGRESS_CRITERION_Y, DEFAULT_PROGRESS_CRITERION_Y);
        setValue(FN_MIN_NUMBER, 1);
        setValue(FN_MAX_NUMBER, MAX_NUMBER);
        setValue(FN_PAUSE_AFTER_BEEP_MS, DEFAULT_PAUSE_AFTER_BEEP_MS);
        setValue(FN_ITI_MS, DEFAULT_ITI_MS);
        setValue(FN_VOLUME, DEFAULT_VOLUME);
        setValue(FN_OFFER_ABORT, DEFAULT_OFFER_ABORT);
        setValue(FN_DEBUG_DISPLAY_STIMULI_ONLY, false);
    }

}


// ============================================================================
// Class info
// ============================================================================

QString IDED3D::shortname() const
{
    return "ID/ED-3D";
}


QString IDED3D::longname() const
{
    return tr("Three-dimensional intradimensional/extradimensional "
              "set-shifting task");
}


QString IDED3D::menusubtitle() const
{
    return tr("Simple discrimination, reversal, compound discrimination, "
              "reversal, ID set shift, reversal, ED set shift, reversal. "
              "Dimensions of shape/colour/number.");
}


// ============================================================================
// Ancillary management
// ============================================================================

void IDED3D::loadAllAncillary(int pk)
{
    OrderBy stage_order_by{{Stage::FN_STAGE, true}};
    ancillaryfunc::loadAncillary<Stage, StagePtr>(
                m_stages, m_app, m_db,
                Stage::FN_FK_TO_TASK, stage_order_by, pk);
    OrderBy trial_order_by{{Trial::FN_TRIAL, true}};
    ancillaryfunc::loadAncillary<Trial, TrialPtr>(
                m_trials, m_app, m_db,
                Trial::FN_FK_TO_TASK, trial_order_by, pk);
}


QVector<DatabaseObjectPtr> IDED3D::getAncillarySpecimens() const
{
    return QVector<DatabaseObjectPtr>{
        StagePtr(new Stage(m_app, m_db)),
        TrialPtr(new Trial(m_app, m_db)),
    };
}


QVector<DatabaseObjectPtr> IDED3D::getAllAncillary() const
{
    QVector<DatabaseObjectPtr> ancillaries;
    for (auto stage : m_stages) {
        ancillaries.append(stage);
    }
    for (auto trial : m_trials) {
        ancillaries.append(trial);
    }
    return ancillaries;
}


// ============================================================================
// Instance info
// ============================================================================

bool IDED3D::isComplete() const
{
    return valueBool(FN_DEBUG_DISPLAY_STIMULI_ONLY) || valueBool(FN_FINISHED);
}


QStringList IDED3D::summary() const
{
    if (valueBool(FN_DEBUG_DISPLAY_STIMULI_ONLY)) {
        return QStringList{tr("Debug mode for displaying test stimuli only")};
    }
    QStringList lines;
    int n_trials = m_trials.length();
    lines.append(QString("Performed %1 trials").arg(n_trials));
    if (n_trials > 0) {
        TrialPtr last_trial = m_trials.at(n_trials - 1);
        lines.append(QString("Last trial was at stage %1")
                     .arg(last_trial->valueInt(Trial::FN_STAGE)));
    }
    return lines;
}


QStringList IDED3D::detail() const
{
    QStringList lines = completenessInfo() + recordSummaryLines();
    lines.append("\n");
    lines.append("Stages:");
    for (StagePtr stage : m_stages) {
        lines.append(stage->recordSummaryCSVString());
    }
    lines.append("\n");
    lines.append("Trials:");
    for (TrialPtr trial : m_trials) {
        lines.append(trial->recordSummaryCSVString());
    }
    return lines;
}


OpenableWidget* IDED3D::editor(bool read_only)
{
    // ------------------------------------------------------------------------
    // OK to edit?
    // ------------------------------------------------------------------------
    if (read_only) {
        qWarning() << "Task not editable! Shouldn't have got here.";
        return nullptr;
    }

    // ------------------------------------------------------------------------
    // Configure the task using a Questionnaire
    // ------------------------------------------------------------------------

    const int no_max = std::numeric_limits<int>::max();
    const QString warning_progress_criterion(tr(
            "WARNING: cannot proceed: must satisfy "
            "progress_criterion_x <= progress_criterion_y"));
    const QString warning_min_max(tr(
            "WARNING: cannot proceed: must satisfy "
            "min_number <= max_number"));

    QuPagePtr page((new QuPage{
        questionnairefunc::defaultGridRawPointer({
            {xstring("last_stage"),
             new QuLineEditInteger(fieldRef(FN_LAST_STAGE), 1, MAX_STAGES)},
            {xstring("max_trials_per_stage"),
             new QuLineEditInteger(fieldRef(FN_MAX_TRIALS_PER_STAGE), 1, no_max)},
            {xstring("progress_criterion_x"),
             new QuLineEditInteger(fieldRef(FN_PROGRESS_CRITERION_X), 1, no_max)},
            {xstring("progress_criterion_y"),
             new QuLineEditInteger(fieldRef(FN_PROGRESS_CRITERION_Y), 1, no_max)},
            {xstring("min_number"),
             new QuLineEditInteger(fieldRef(FN_MIN_NUMBER), 1, MAX_NUMBER)},
            {xstring("max_number"),
             new QuLineEditInteger(fieldRef(FN_MAX_NUMBER), 1, MAX_NUMBER)},
            {xstring("pause_after_beep_ms"),
             new QuLineEditInteger(fieldRef(FN_PAUSE_AFTER_BEEP_MS), 0, no_max)},
            {xstring("iti_ms"),
             new QuLineEditInteger(fieldRef(FN_ITI_MS), 0, no_max)},
            {xstring("counterbalance_dimensions"),
             new QuLineEditInteger(fieldRef(FN_COUNTERBALANCE_DIMENSIONS), 0, MAX_COUNTERBALANCE_DIMENSIONS)},
            {xstring("volume"),
             new QuLineEditDouble(fieldRef(FN_VOLUME), MIN_VOLUME, MAX_VOLUME, VOLUME_DP)},
            {xstring("offer_abort"),
             (new QuBoolean(xstring("offer_abort"),
                            fieldRef(FN_OFFER_ABORT)))->setAsTextButton(true)},
            {xstring("debug_display_stimuli_only"),
             (new QuBoolean(xstring("debug_display_stimuli_only"),
                            fieldRef(FN_DEBUG_DISPLAY_STIMULI_ONLY)))->setAsTextButton(true)},
        }),
        (new QuText(warning_progress_criterion))
                        ->setWarning(true)
                        ->addTag(TAG_WARNING_PROGRESS_CRITERION),
        (new QuText(warning_min_max))
                        ->setWarning(true)
                        ->addTag(TAG_WARNING_MIN_MAX),
    })->setTitle(longname()));

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Clinician);
    m_questionnaire->setReadOnly(read_only);
    m_questionnaire->setWithinChain(true);  // fast forward button, not stop

    connect(fieldRef(FN_PROGRESS_CRITERION_X).data(), &FieldRef::valueChanged,
            this, &IDED3D::validateQuestionnaire);
    connect(fieldRef(FN_PROGRESS_CRITERION_Y).data(), &FieldRef::valueChanged,
            this, &IDED3D::validateQuestionnaire);
    connect(fieldRef(FN_MIN_NUMBER).data(), &FieldRef::valueChanged,
            this, &IDED3D::validateQuestionnaire);
    connect(fieldRef(FN_MAX_NUMBER).data(), &FieldRef::valueChanged,
            this, &IDED3D::validateQuestionnaire);

    connect(m_questionnaire.data(), &Questionnaire::cancelled,
            this, &IDED3D::abort);
    connect(m_questionnaire.data(), &Questionnaire::completed,
            this, &IDED3D::startTask);

    validateQuestionnaire();

    // ------------------------------------------------------------------------
    // If the config questionnaire is successful, we'll launch the main task;
    // prepare this too.
    // ------------------------------------------------------------------------

    m_scene = new QGraphicsScene(SCENE_RECT);
    m_scene->setBackgroundBrush(QBrush(SCENE_BACKGROUND)); // *** not working
    m_graphics_widget = makeGraphicsWidget(m_scene, SCENE_BACKGROUND);

    m_widget = new OpenableWidget();

    // We start off by seeing the questionnaire:
    m_widget->setWidgetAsOnlyContents(m_questionnaire, 0, false, false);

    return m_widget;
}


// ============================================================================
// Config questionnaire internals
// ============================================================================

void IDED3D::validateQuestionnaire()
{
    if (!m_questionnaire) {
        return;
    }
    QVector<QuPage*> pages = m_questionnaire->getPages(true);
    Q_ASSERT(pages.size() == 1);
    QuPage* page = pages.at(0);

    bool duff_pc = valueInt(FN_PROGRESS_CRITERION_Y) < valueInt(FN_PROGRESS_CRITERION_X);
    bool duff_minmax = valueInt(FN_MAX_NUMBER) < valueInt(FN_MIN_NUMBER);

    m_questionnaire->setVisibleByTag(TAG_WARNING_PROGRESS_CRITERION, duff_pc);
    m_questionnaire->setVisibleByTag(TAG_WARNING_MIN_MAX, duff_minmax);
    page->blockProgress(duff_pc || duff_minmax);
}


// ============================================================================
// Main task internals
// ============================================================================

// MUST USE Qt::QueuedConnection - see comments in clearScene()
#define CONNECT_BUTTON(b, funcname) \
    connect(b.button, &QPushButton::clicked, \
            this, &IDED3D::funcname, \
            Qt::QueuedConnection)
// To use a Qt::ConnectionType parameter with a functor, we need a context
// See http://doc.qt.io/qt-5/qobject.html#connect-5
// That's the reason for the extra "this":
#define CONNECT_BUTTON_PARAM(b, funcname, param) \
    connect(b.button, &QPushButton::clicked, this, \
            std::bind(&IDED3D::funcname, this, param), \
            Qt::QueuedConnection)
#define CONNECT_SVG(svg, funcname) \
    connect(svg.widget, &SvgWidgetClickable::clicked, \
            this, &IDED3D::funcname, \
            Qt::QueuedConnection)
    // ... svg is an SvgItemAndRenderer


void IDED3D::startTask()
{
    m_widget->setWidgetAsOnlyContents(m_graphics_widget, 0, true, true);
    if (valueBool(FN_DEBUG_DISPLAY_STIMULI_ONLY)) {
        debugDisplayStimuli();
    }
    // ***
}


void IDED3D::debugDisplayStimuli()
{
    qDebug() << Q_FUNC_INFO;
    int n_stimuli = SHAPE_DEFINITIONS.size();
    qreal aspect = SCENE_WIDTH / SCENE_HEIGHT;
    QPair<int, int> x_y = mathfunc::gridDimensions(n_stimuli, aspect);
    int nx = x_y.first;
    int ny = x_y.second;
    QVector<qreal> x_centres = mathfunc::distribute(nx, 0, SCENE_WIDTH);
    QVector<qreal> y_centres = mathfunc::distribute(ny, 0, SCENE_HEIGHT);
    qreal scale = 0.8 * qMin(SCENE_WIDTH / nx, SCENE_HEIGHT / ny) / STIMSIZE;
    int n = 0;
    for (int y = 0; y < ny && n < n_stimuli; ++y) {
        for (int x = 0; x < nx && n < n_stimuli; ++x) {
            QPointF centre(x_centres[x], y_centres[y]);
            SvgWidgetAndProxy stim = showIndividualStimulus(n, TEST_COLOUR,
                                                            centre, scale);
            QString label = QString::number(n);
            makeText(m_scene, centre, BASE_TEXT_CONFIG, label);
            CONNECT_SVG(stim, finish);
            n += 1;
        }
    }
}


SvgWidgetAndProxy IDED3D::showIndividualStimulus(
        int stimulus_num, const QColor& colour,
        const QPointF& centre, qreal scale)
{
    Q_ASSERT(stimulus_num >= 0 && stimulus_num < SHAPE_DEFINITIONS.size());
    const QString& base_svg = SHAPE_DEFINITIONS.at(stimulus_num);
    // ***
    /*
    QString path_contents = QString(
                "s%1 "  // scale
                "t%2,%3 "
                "%4")  // translate (correcting for current scaling)
            .arg(scale)
            .arg(centre.x() / scale)
            .arg(centre.y() / scale)
            .arg(base_svg);
    */
    QString path_contents = base_svg;
    Q_UNUSED(scale);
    QString svg = graphicsfunc::svgFromPathContents(
                path_contents, colour, STIM_STROKE_WIDTH, colour);
    qDebug().noquote() << "showIndividualStimulus: svg:" << svg;
    return makeSvg(m_scene, centre, svg);
}



void IDED3D::abort()
{
    Q_ASSERT(m_widget);
    editFinishedAbort();
    emit m_widget->finished();
}


void IDED3D::finish()
{
    Q_ASSERT(m_widget);
    editFinishedProperly();
    emit m_widget->finished();
}
