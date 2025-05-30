/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#pragma once
#include <QColor>
#include <QMediaPlayer>
#include <QPointer>
#include <QSharedPointer>
#include <QString>

#include "graphics/graphicsfunc.h"
#include "tasklib/task.h"

class CamcopsApp;
class OpenableWidget;
class QGraphicsScene;
class QTimer;
class TaskFactory;

class IDED3DStage;
class IDED3DTrial;

void initializeIDED3D(TaskFactory& factory);

// "Meta object features not supported for nested classes"
// ... so Stage, Trial must be standalone
// ... so they may as well have their own .h/.cpp files for ease of reading


class IDED3D : public Task
{
    Q_OBJECT
    using FuncPtr = void (IDED3D::*)();
    // ... a pointer to a member function of IDED3D that takes no
    // parameters and returns void
    using IDED3DStagePtr = QSharedPointer<IDED3DStage>;
    using IDED3DTrialPtr = QSharedPointer<IDED3DTrial>;

public:
    IDED3D(
        CamcopsApp& app,
        DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK
    );
    ~IDED3D() override;

protected:
    QMap<QString, QMetaType> initTypes();
    QMap<QString, QVariant> initDefaultValues();
    QMap<QString, QVariant> initMinValues();
    QMap<QString, QVariant> initMaxValues();

    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------

public:
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString description() const override;

    virtual bool isEditable() const override
    {
        return false;
    }

    virtual bool isCrippled() const override
    {
        return false;
    }

    // ------------------------------------------------------------------------
    // Ancillary management
    // ------------------------------------------------------------------------
    virtual QStringList ancillaryTables() const override;
    virtual QString ancillaryTableFKToTaskFieldname() const override;
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

protected:
    virtual void applySettings(const QJsonObject& settings) override;
    void applySetting(const QString fieldname, const QJsonValue value);

    // ------------------------------------------------------------------------
    // Validation for questionnaire
    // ------------------------------------------------------------------------
protected slots:
    void validateQuestionnaire();

protected:
    bool validateSettings();

    // ------------------------------------------------------------------------
    // Calculation/assistance functions for main task
    // ------------------------------------------------------------------------

protected:
    void makeStages();
    void debugDisplayStimuli();
    graphicsfunc::SvgWidgetAndProxy showIndividualStimulus(
        int stimulus_num,
        const QColor& colour,
        const QPointF& centre,
        qreal scale,
        bool debug = false
    );
    QVector<QPointF> stimCentres(int n) const;
    QRectF locationRect(int location) const;
    void showEmptyBox(
        int location, bool touchable = false, bool correct = false
    );
    void showCompositeStimulus(
        int shape, int colour_number, int number, int location, bool correct
    );
    bool stagePassed() const;
    int getNumTrialsThisStage() const;
    bool stageFailed() const;
    void clearScene();
    void setTimeout(int time_ms, FuncPtr callback);
    // NB QObject has startTimer(), calling timerEvent()

    // ------------------------------------------------------------------------
    // Main task proper
    // ------------------------------------------------------------------------

protected:
    void startTask();
protected slots:
    void nextTrial();
    void startTrial();
    void recordResponse(bool correct);
    void showAnswer(bool correct);
    void mediaStatusChanged(QMediaPlayer::MediaStatus status);
    void waitAfterBeep();
    void iti();
    void thanks();
    void abort();
    void finish();

    // ------------------------------------------------------------------------
    // Data
    // ------------------------------------------------------------------------

protected:
    QPointer<OpenableWidget> m_widget;
    QPointer<Questionnaire> m_questionnaire;
    QPointer<OpenableWidget> m_graphics_widget;
    QPointer<QGraphicsScene> m_scene;
    QVector<IDED3DStagePtr> m_stages;
    QVector<IDED3DTrialPtr> m_trials;
    int m_current_stage;  // zero-based
    int m_current_trial;  // zero-based
    QSharedPointer<QTimer> m_timer;
    QSharedPointer<QMediaPlayer> m_player_correct;
    // ... not owned by other widgets
    QSharedPointer<QMediaPlayer> m_player_incorrect;
    // ... not owned by other widgets

    QMap<QString, QVariant> m_default_values;
    QMap<QString, QMetaType> m_types;
    QMap<QString, QVariant> m_min_values;
    QMap<QString, QVariant> m_max_values;

    // ------------------------------------------------------------------------
    // Constants
    // ------------------------------------------------------------------------

public:
    static const QString IDED3D_TABLENAME;
};
