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
#include <QPointer>
#include <QString>

#include "tasklib/task.h"

class CamcopsApp;
class OpenableWidget;
class Questionnaire;
class TaskFactory;

void initializePhq8(TaskFactory& factory);

class Phq8 : public Task
{
    Q_OBJECT

public:
    Phq8(
        CamcopsApp& app,
        DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK,
        QObject* parent = nullptr
    );
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString description() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
    int totalScore() const;
    int nCoreSymptoms() const;
    int nOtherSymptoms() const;
    static QString severity(int score);

public:
    static const QString PHQ8_TABLENAME;

protected:
    QPointer<Questionnaire> m_questionnaire;
};
