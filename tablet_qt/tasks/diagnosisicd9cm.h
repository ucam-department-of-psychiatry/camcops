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
#include <QString>

#include "taskxtra/diagnosistaskbase.h"

class CamcopsApp;
class OpenableWidget;
class TaskFactory;

void initializeDiagnosisIcd9CM(TaskFactory& factory);

class DiagnosisIcd9CM : public DiagnosisTaskBase
{
    Q_OBJECT

public:
    DiagnosisIcd9CM(
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
    // Ancillary management
    // ------------------------------------------------------------------------
    virtual QStringList ancillaryTables() const override;
    virtual QString ancillaryTableFKToTaskFieldname() const override;
    virtual void loadAllAncillary(int pk) override;
    virtual QVector<DatabaseObjectPtr> getAncillarySpecimens() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    // ------------------------------------------------------------------------
    // DiagnosisTaskBase extras
    // ------------------------------------------------------------------------
    virtual DiagnosticCodeSetPtr makeCodeset() const override;
    virtual DiagnosisItemBasePtr makeItem() const override;

public:
    static const QString DIAGNOSIS_ICD9CM_TABLENAME;
};
