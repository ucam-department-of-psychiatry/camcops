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

// By Joe Kearney, Rudolf Cardinal.

#pragma once
#include <QPointer>
#include <QString>

#include "tasklib/task.h"

void initializeGboGReS(TaskFactory& factory);

class GboGReS : public Task
{
    Q_OBJECT

public:
    GboGReS(
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
    virtual QString infoFilenameStem() const override;
    virtual QString xstringTaskname() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task specific
    // ------------------------------------------------------------------------

protected:
    QString completedBy() const;
    QString extraGoalsDescription() const;
    QString numGoalsDescription() const;
protected slots:
    void updateMandatory();

public:
    static const QString GBOGRES_TABLENAME;

protected:
    QPointer<Questionnaire> m_questionnaire;
};
