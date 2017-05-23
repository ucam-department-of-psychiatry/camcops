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

#pragma once
#include <QColor>
#include <QPointer>
#include <QSharedPointer>
#include <QString>
#include "lib/graphicsfunc.h"
#include "tasklib/task.h"

class CamcopsApp;
class OpenableWidget;
class QGraphicsScene;
class TaskFactory;

void initializeIDED3D(TaskFactory& factory);


class IDED3D : public Task
{
    Q_OBJECT
public:
    IDED3D(CamcopsApp& app, const QSqlDatabase& db,
           int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    virtual bool isEditable() const override { return false; }
    virtual bool isCrippled() const override { return false; }
    // ------------------------------------------------------------------------
    // Ancillary management
    // ------------------------------------------------------------------------
    virtual void loadAllAncillary(int pk) override;
    virtual QVector<DatabaseObjectPtr> getAncillarySpecimens() const override;
    virtual QVector<DatabaseObjectPtr> getAllAncillary() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Internals
    // ------------------------------------------------------------------------
protected:

    class Trial : public DatabaseObject {
        friend class IDED3D;
    public:
        Trial(CamcopsApp& app, const QSqlDatabase& db,
              int load_pk = dbconst::NONEXISTENT_PK);
    protected:
        static const QString TRIAL_TABLENAME;
        static const QString FN_FK_TO_TASK;
        static const QString FN_TRIAL;
        static const QString FN_STAGE;
        static const QString FN_CORRECT_LOCATION;
        static const QString FN_INCORRECT_LOCATION;
        static const QString FN_CORRECT_SHAPE;
        static const QString FN_CORRECT_COLOUR;
        static const QString FN_CORRECT_NUMBER;
        static const QString FN_INCORRECT_SHAPE;
        static const QString FN_INCORRECT_COLOUR;
        static const QString FN_INCORRECT_NUMBER;
        static const QString FN_TRIAL_START_TIME;
        static const QString FN_RESPONDED;
        static const QString FN_RESPONSE_TIME;
        static const QString FN_RESPONSE_LATENCY_MS;
        static const QString FN_CORRECT;
        static const QString FN_INCORRECT;
    };
    using TrialPtr = QSharedPointer<Trial>;

    class Stage : public DatabaseObject {
        friend class IDED3D;
    public:
        Stage(CamcopsApp& app, const QSqlDatabase& db,
              int load_pk = dbconst::NONEXISTENT_PK);
    protected:
        static const QString STAGE_TABLENAME;
        static const QString FN_FK_TO_TASK;
        static const QString STAGE_FN_FK_TO_TASK;
        static const QString FN_STAGE;
        static const QString FN_STAGE_NAME;
        static const QString FN_RELEVANT_DIMENSION;
        static const QString FN_CORRECT_EXEMPLAR;
        static const QString FN_INCORRECT_EXEMPLAR;
        static const QString FN_CORRECT_STIMULUS_SHAPES;
        static const QString FN_CORRECT_STIMULUS_COLOURS;
        static const QString FN_CORRECT_STIMULUS_NUMBERS;
        static const QString FN_INCORRECT_STIMULUS_SHAPES;
        static const QString FN_INCORRECT_STIMULUS_COLOURS;
        static const QString FN_INCORRECT_STIMULUS_NUMBERS;
        static const QString FN_FIRST_TRIAL_NUM;
        static const QString FN_N_COMPLETED_TRIALS;
        static const QString FN_N_CORRECT;
        static const QString FN_N_INCORRECT;
        static const QString FN_STAGE_PASSED;
        static const QString FN_STAGE_FAILED;
    };
    using StagePtr = QSharedPointer<Stage>;

    void startTask();
    void debugDisplayStimuli();
    graphicsfunc::SvgWidgetAndProxy showIndividualStimulus(
            int stimulus_num, const QColor& colour,
            const QPointF& centre, qreal scale);

protected slots:
    void validateQuestionnaire();
    void abort();
    void finish();

protected:
    QPointer<OpenableWidget> m_widget;
    QPointer<Questionnaire> m_questionnaire;
    QPointer<OpenableWidget> m_graphics_widget;
    QPointer<QGraphicsScene> m_scene;
    QVector<StagePtr> m_stages;
    QVector<TrialPtr> m_trials;

public:
    static const QString IDED3D_TABLENAME;
protected:
    static const QString FN_LAST_STAGE;
    static const QString FN_MAX_TRIALS_PER_STAGE;
    static const QString FN_PROGRESS_CRITERION_X;
    static const QString FN_PROGRESS_CRITERION_Y;
    static const QString FN_MIN_NUMBER;
    static const QString FN_MAX_NUMBER;
    static const QString FN_PAUSE_AFTER_BEEP_MS;
    static const QString FN_ITI_MS;
    static const QString FN_COUNTERBALANCE_DIMENSIONS;
    static const QString FN_VOLUME;
    static const QString FN_OFFER_ABORT;
    static const QString FN_DEBUG_DISPLAY_STIMULI_ONLY;
    static const QString FN_SHAPE_DEFINITIONS_SVG;
    static const QString FN_ABORTED;
    static const QString FN_FINISHED;
    static const QString FN_LAST_TRIAL_COMPLETED;
};
