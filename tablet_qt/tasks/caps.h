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

void initializeCaps(TaskFactory& factory);

class Caps : public Task
{
    Q_OBJECT

public:
    Caps(
        CamcopsApp& app,
        DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK
    );
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString description() const override;

    virtual bool prohibitsCommercial() const override
    {
        return true;
    }

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
    int distressScore() const;
    int intrusivenessScore() const;
    int frequencyScore() const;

protected:
    bool questionComplete(int q) const;
    QVariant endorse(int q) const;
    QVariant distress(int q) const;
    QVariant intrusiveness(int q) const;
    QVariant frequency(int q) const;
    // ------------------------------------------------------------------------
    // Signal handlers
    // ------------------------------------------------------------------------
public slots:
    void endorseChanged(const FieldRef* fieldref);

protected:
    bool needsDetail(int q);

protected:
    QPointer<Questionnaire> m_questionnaire;
    QMap<int, FieldRefPtr> m_fr_distress;
    QMap<int, FieldRefPtr> m_fr_intrusiveness;
    QMap<int, FieldRefPtr> m_fr_frequency;

public:
    static const QString CAPS_TABLENAME;
};
