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

#include "cardinalexpectationdetection.h"
#include <QTimer>
#include "questionnairelib/questionnaire.h"
#include "tasklib/taskregistrar.h"


// ============================================================================
// Constants
// ============================================================================

const QString CardinalExpectationDetection::CARDINALEXPDET_TABLENAME(
        "cardinal_expdet");

// Fieldnames
const QString FN_NUM_BLOCKS("num_blocks");
const QString FN_STIMULUS_COUNTERBALANCING("stimulus_counterbalancing");
const QString FN_IS_DETECTION_RESPONSE_ON_RIGHT("is_detection_response_on_right");
const QString FN_PAUSE_EVERY_N_TRIALS("pause_every_n_trials");
const QString FN_CUE_DURATION_S("cue_duration_s");
const QString FN_VISUAL_CUE_INTENSITY("visual_cue_intensity");
const QString FN_AUDITORY_CUE_INTENSITY("auditory_cue_intensity");
const QString FN_ISI_DURATION_S("isi_duration_s");
const QString FN_VISUAL_TARGET_DURATION_S("visual_target_duration_s");
const QString FN_VISUAL_BACKGROUND_INTENSITY("visual_background_intensity");
const QString FN_VISUAL_TARGET_0_INTENSITY("visual_target_0_intensity");
const QString FN_VISUAL_TARGET_1_INTENSITY("visual_target_1_intensity");
const QString FN_AUDITORY_BACKGROUND_INTENSITY("auditory_background_intensity");
const QString FN_AUDITORY_TARGET_0_INTENSITY("auditory_target_0_intensity");
const QString FN_AUDITORY_TARGET_1_INTENSITY("auditory_target_1_intensity");
const QString FN_ITI_MIN_S("iti_min_s");
const QString FN_ITI_MAX_S("iti_max_s");

// Text for user
const QString TX_CONFIG_TITLE("Configure Expectation–Detection task");
const QString TX_CONFIG_INSTRUCTIONS_1("You’ll need to set these parameters:");
const QString TX_CONFIG_INSTRUCTIONS_2(
        "Configure these based on the results of the ExpDetThreshold task. "
        "(DO NOT alter your tablet device’s brightness or volume, or the "
        "environmental lighting/noise conditions.)");
const QString TX_CONFIG_INSTRUCTIONS_3(
        "These parameters are less likely to need changing:");
const QString TX_CONFIG_STIMULUS_COUNTERBALANCING(
        "Stimulus counterbalancing (0–7):");
const QString TX_CONFIG_NUM_BLOCKS(
        "Number of trial blocks (24 trials/block):");
const QString TX_CONFIG_PAUSE_EVERY_N_TRIALS(
        "Pause every n trials (0 for no pausing):");
const QString TX_CONFIG_IS_DETECTION_RESPONSE_ON_RIGHT(
        "“Detection” responses are towards the right");
const QString TX_CONFIG_CUE_DURATION_S(
        "Cue duration (s) (cus is multimodal; auditory+visual):");
const QString TX_CONFIG_VISUAL_CUE_INTENSITY(
        "Visual cue intensity (0.0–1.0, usually 1.0):");
const QString TX_CONFIG_AUDITORY_CUE_INTENSITY(
        "Auditory cue intensity (0.0–1.0, usually 1.0):");
const QString TX_CONFIG_ISI_DURATION_S(
        "Interstimulus interval (ISI) (s) (e.g. 0.2):");
const QString TX_CONFIG_VISUAL_BACKGROUND_INTENSITY(
        "Visual background intensity (0.0–1.0, usually 1.0):");
const QString TX_CONFIG_INTENSITY_PREFIX("Intensity (0.0–1.0) for:");
const QString TX_CONFIG_AUDITORY_BACKGROUND_INTENSITY(
        "Auditory background intensity (0.0–1.0, usually 1.0):");
const QString TX_CONFIG_ITI_MIN_S(
        "Intertrial interval (ITI) minimum duration (s):");
const QString TX_CONFIG_ITI_MAX_S(
        "Intertrial interval (ITI) maximum duration (s):");
const QString TX_INSTRUCTIONS_1(
        "Please ensure you can see and hear this tablet/computer clearly.");
const QString TX_INSTRUCTIONS_2(
        "The experimenter will assist you with any headphones required.");
const QString TX_INSTRUCTIONS_3(
        "Once you have started the task, please follow the instructions that "
        "appear on the screen.");
const QString TX_DETECTION_Q_PREFIX("Did you");
const QString TX_DETECTION_Q_VISUAL("see a");
const QString TX_DETECTION_Q_AUDITORY("hear a");
const QString TX_OPTION_0("No,\ndefinitely not");
const QString TX_OPTION_1("No,\nprobably not");
const QString TX_OPTION_2("Unsure");
const QString TX_OPTION_3("Yes,\nprobably");
const QString TX_OPTION_4("Yes,\ndefinitely");
const QString TX_PAUSE_PROMPT("When you’re ready, touch here to continue.");
const QString TX_NUM_TRIALS_LEFT("Number of trials to go:");
const QString TX_TIME_LEFT("Estimated time left (minutes):");
const QString TX_POINTS("Your score on this trial was:");
const QString TX_CUMULATIVE_POINTS("Your total score so far is:");


// ============================================================================
// Factory method
// ============================================================================

void initializeCardinalExpectationDetection(TaskFactory& factory)
{
    static TaskRegistrar<CardinalExpectationDetection> registered(factory);
}


// ============================================================================
// CardinalExpectationDetection
// ============================================================================

CardinalExpectationDetection::CardinalExpectationDetection(
        CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, CARDINALEXPDET_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    // Config
    addField(FN_NUM_BLOCKS, QVariant::Int);
    addField(FN_STIMULUS_COUNTERBALANCING, QVariant::Int);
    addField(FN_IS_DETECTION_RESPONSE_ON_RIGHT, QVariant::Bool);
    addField(FN_PAUSE_EVERY_N_TRIALS, QVariant::Bool);
    // ... cue
    addField(FN_CUE_DURATION_S, QVariant::Double);
    addField(FN_VISUAL_CUE_INTENSITY, QVariant::Double);
    addField(FN_AUDITORY_CUE_INTENSITY, QVariant::Double);
    // ... ISI
    addField(FN_ISI_DURATION_S, QVariant::Double);
    // ... target
    addField(FN_VISUAL_TARGET_DURATION_S, QVariant::Double);
    addField(FN_VISUAL_BACKGROUND_INTENSITY, QVariant::Double);  // 0 to 1
    addField(FN_VISUAL_TARGET_0_INTENSITY, QVariant::Double);  // 0 to 1
    addField(FN_VISUAL_TARGET_1_INTENSITY, QVariant::Double);  // 0 to 1
    addField(FN_AUDITORY_BACKGROUND_INTENSITY, QVariant::Double);  // 0 to 1
    addField(FN_AUDITORY_TARGET_0_INTENSITY, QVariant::Double);  // 0 to 1
    addField(FN_AUDITORY_TARGET_1_INTENSITY, QVariant::Double);  // 0 to 1
    // ... ITI
    addField(FN_ITI_MIN_S, QVariant::Double);
    addField(FN_ITI_MAX_S, QVariant::Double);


#ifdef ARGH  // ***

    ***


    ***

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

    // Internal data
    m_player = QSharedPointer<QMediaPlayer>(new QMediaPlayer(),
                                            &QObject::deleteLater);
    connect(m_player.data(), &QMediaPlayer::mediaStatusChanged,
            this, &CardinalExpectationDetection::mediaStatusChanged);
#else
    Q_UNUSED(load_pk);
#endif
    m_timer = QSharedPointer<QTimer>(new QTimer());
    m_timer->setSingleShot(true);
}


CardinalExpectationDetection::~CardinalExpectationDetection()
{
#ifdef ARGH  // ***
    // Necessary: for rationale, see QuAudioPlayer::~QuAudioPlayer()
    if (m_player_correct) {
        m_player_correct->stop();
    }
    if (m_player_incorrect) {
        m_player_incorrect->stop();
    }
#endif
}


// ============================================================================
// Class info
// ============================================================================

QString CardinalExpectationDetection::shortname() const
{
    return "Cardinal_ExpDet";
}


QString CardinalExpectationDetection::longname() const
{
    return tr("Cardinal RN — Expectation–Detection task");
}


QString CardinalExpectationDetection::menusubtitle() const
{
    return tr("Putative assay of proneness to hallucinations");
}


// ============================================================================
// Ancillary management
// ============================================================================

void CardinalExpectationDetection::loadAllAncillary(int pk)
{
#ifdef ARGH  // ***

    OrderBy stage_order_by{{IDED3DStage::FN_STAGE, true}};
    ancillaryfunc::loadAncillary<IDED3DStage, IDED3DStagePtr>(
                m_stages, m_app, m_db,
                IDED3DStage::FN_FK_TO_TASK, stage_order_by, pk);
    OrderBy trial_order_by{{IDED3DTrial::FN_TRIAL, true}};
    ancillaryfunc::loadAncillary<IDED3DTrial, IDED3DTrialPtr>(
                m_trials, m_app, m_db,
                IDED3DTrial::FN_FK_TO_TASK, trial_order_by, pk);
#else
    Q_UNUSED(pk);
#endif
}


QVector<DatabaseObjectPtr> CardinalExpectationDetection::getAncillarySpecimens() const
{
    return QVector<DatabaseObjectPtr>{
#ifdef ARGH  // ***
        IDED3DStagePtr(new IDED3DStage(m_app, m_db)),
        IDED3DTrialPtr(new IDED3DTrial(m_app, m_db)),
#endif
    };
}


QVector<DatabaseObjectPtr> CardinalExpectationDetection::getAllAncillary() const
{
    QVector<DatabaseObjectPtr> ancillaries;
#ifdef ARGH  // ***
    for (auto stage : m_stages) {
        ancillaries.append(stage);
    }
    for (auto trial : m_trials) {
        ancillaries.append(trial);
    }
#endif
    return ancillaries;
}


// ============================================================================
// Instance info
// ============================================================================

bool CardinalExpectationDetection::isComplete() const
{
#ifdef ARGH  // ***
    return valueBool(FN_FINISHED);
#else
return false;
#endif
}


QStringList CardinalExpectationDetection::summary() const
{
    QStringList lines;
#ifdef ARGH  // ***
    int n_trials = m_trials.length();
    lines.append(QString("Performed %1 trial(s).").arg(n_trials));
    if (n_trials > 0) {
        IDED3DTrialPtr last_trial = m_trials.at(n_trials - 1);
        lines.append(QString("Last trial was at stage %1.")
                     .arg(last_trial->valueInt(IDED3DTrial::FN_STAGE)));
    }
#endif
    return lines;
}


QStringList CardinalExpectationDetection::detail() const
{
    QStringList lines = completenessInfo() + recordSummaryLines();
#ifdef ARGH  // ***
    lines.append("\n");
    lines.append("Stages:");
    for (IDED3DStagePtr stage : m_stages) {
        lines.append(stage->recordSummaryCSVString());
    }
    lines.append("\n");
    lines.append("Trials:");
    for (IDED3DTrialPtr trial : m_trials) {
        lines.append(trial->recordSummaryCSVString());
    }
#endif
    return lines;
}


OpenableWidget* CardinalExpectationDetection::editor(bool read_only)
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
#ifdef ARGH  // ***

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
    // Because our main m_widget isn't itself a questionnaire, we need to hook
    // up these, too:
    questionnairefunc::connectQuestionnaireToTask(m_questionnaire.data(), this);

    validateQuestionnaire();

    // ------------------------------------------------------------------------
    // If the config questionnaire is successful, we'll launch the main task;
    // prepare this too.
    // ------------------------------------------------------------------------

    m_scene = new QGraphicsScene(SCENE_RECT);
    m_scene->setBackgroundBrush(QBrush(SCENE_BACKGROUND)); // *** not working
    m_graphics_widget = makeGraphicsWidget(m_scene, SCENE_BACKGROUND,
                                           true, true);
    connect(m_graphics_widget.data(), &OpenableWidget::aborting,
            this, &IDED3D::abort);

    m_widget = new OpenableWidget();

    // We start off by seeing the questionnaire:
    m_widget->setWidgetAsOnlyContents(m_questionnaire, 0, false, false);

    return m_widget;
#else
    return nullptr;
#endif
}


// ============================================================================
// Config questionnaire internals
// ============================================================================

void CardinalExpectationDetection::validateQuestionnaire()
{
#ifdef ARGH  // ***
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
#endif
}


// ============================================================================
// Connection macros
// ============================================================================

// MUST USE Qt::QueuedConnection - see comments in clearScene()
#define CONNECT_BUTTON(b, funcname) \
    connect(b.button, &QPushButton::clicked, \
            this, &CardinalExpectationDetection::funcname, \
            Qt::QueuedConnection)
// To use a Qt::ConnectionType parameter with a functor, we need a context
// See http://doc.qt.io/qt-5/qobject.html#connect-5
// That's the reason for the extra "this":
#define CONNECT_BUTTON_PARAM(b, funcname, param) \
    connect(b.button, &QPushButton::clicked, \
            this, std::bind(&CardinalExpectationDetection::funcname, this, param), \
            Qt::QueuedConnection)
// For debugging:
#define CONNECT_SVG_CLICKED(svg, funcname) \
    connect(svg.widget, &SvgWidgetClickable::clicked, \
            this, &CardinalExpectationDetection::funcname, \
            Qt::QueuedConnection)
    // ... svg is an SvgItemAndRenderer
    // ... use "pressed" not "clicked" for rapid response detection.


// ============================================================================
// Calculation/assistance functions for main task
// ============================================================================


// ============================================================================
// Main task internals
// ============================================================================

void CardinalExpectationDetection::startTask()
{
#ifdef ARGH  // ***

    qDebug() << Q_FUNC_INFO;
    m_widget->setWidgetAsOnlyContents(m_graphics_widget, 0, false, false);
    if (valueBool(FN_DEBUG_DISPLAY_STIMULI_ONLY)) {
        debugDisplayStimuli();
        return;
    }

    // Store a version of the shape definitions, in JSON format
    setValue(FN_SHAPE_DEFINITIONS_SVG, IDED3DExemplars::allShapesAsJson());
    // Similarly for colours
    setValue(FN_COLOUR_DEFINITIONS_RGB, IDED3DExemplars::allColoursAsJson());
    editStarted();  // will have been stopped by the end of the questionnaire?

    // Double-check we have a PK before we create stages/trials
    save();

    // Make the stages
    makeStages();

    // Prep the sounds
    m_player_correct = QSharedPointer<QMediaPlayer>(new QMediaPlayer(),
                                                    &QObject::deleteLater);
    m_player_incorrect = QSharedPointer<QMediaPlayer>(new QMediaPlayer(),
                                                      &QObject::deleteLater);
    // ... for rationale, see QuAudioPlayer::makeWidget()
    m_player_correct->setMedia(uifunc::resourceUrl(SOUND_FILE_CORRECT));
    m_player_incorrect->setMedia(uifunc::resourceUrl(SOUND_FILE_INCORRECT));
    m_player_correct->setVolume(mathfunc::proportionToIntPercent(
                                    valueInt(FN_VOLUME)));
    m_player_incorrect->setVolume(mathfunc::proportionToIntPercent(
                                      valueInt(FN_VOLUME)));
    connect(m_player_correct.data(), &QMediaPlayer::mediaStatusChanged,
            this, &IDED3D::mediaStatusChanged);
    connect(m_player_incorrect.data(), &QMediaPlayer::mediaStatusChanged,
            this, &IDED3D::mediaStatusChanged);

    // Start
    ButtonAndProxy start = makeTextButton(
                m_scene,
                QRectF(0.2 * SCENE_WIDTH, 0.6 * SCENE_HEIGHT,
                       0.6 * SCENE_WIDTH, 0.1 * SCENE_HEIGHT),
                BASE_BUTTON_CONFIG,
                TX_START);
    CONNECT_BUTTON(start, nextTrial);
#endif
}


void CardinalExpectationDetection::abort()
{
#ifdef ARGH  // ***
#ifdef DEBUG_STEP_DETAIL
    qDebug() << Q_FUNC_INFO;
#endif
    setValue(FN_ABORTED, true);
    Q_ASSERT(m_widget);
    editFinishedAbort();
    emit m_widget->finished();
#endif
}


void CardinalExpectationDetection::finish()
{
#ifdef ARGH  // ***
#ifdef DEBUG_STEP_DETAIL
    qDebug() << Q_FUNC_INFO;
#endif
    setValue(FN_FINISHED, true);
    Q_ASSERT(m_widget);
    editFinishedProperly();
    emit m_widget->finished();
#endif
}
