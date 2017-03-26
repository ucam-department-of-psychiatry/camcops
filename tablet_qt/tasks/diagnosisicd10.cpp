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

#include "diagnosisicd10.h"
#include "db/ancillaryfunc.h"
#include "diagnosis/icd10.h"
#include "questionnairelib/qudiagnosticcode.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qutext.h"
#include "tasks/diagnosisicd10item.h"
#include "tasklib/taskfactory.h"

const QString DIAGNOSIS_ICD10_TABLENAME("diagnosis_icd10");


void initializeDiagnosisIcd10(TaskFactory& factory)
{
    static TaskRegistrar<DiagnosisIcd10> registered(factory);
}


DiagnosisIcd10::DiagnosisIcd10(CamcopsApp& app, const QSqlDatabase& db,
                               int load_pk) :
    DiagnosisTaskBase(app, db, DIAGNOSIS_ICD10_TABLENAME, load_pk)
{
}


// ============================================================================
// Class info
// ============================================================================

QString DiagnosisIcd10::shortname() const
{
    return "Diagnosis_ICD10";
}


QString DiagnosisIcd10::longname() const
{
    return tr("Diagnostic coding (ICD-10)");
}


QString DiagnosisIcd10::menusubtitle() const
{
    return tr("Diagnostic codes, using ICD-10 codes.");
}


// ============================================================================
// Ancillary management
// ============================================================================

void DiagnosisIcd10::loadAllAncillary(int pk)
{
    OrderBy order_by{{DiagnosisIcd10Item::SEQNUM, true}};
    ancillaryfunc::loadAncillary<DiagnosisIcd10Item, DiagnosisItemBasePtr>(
                m_items, m_app, m_db,
                DiagnosisIcd10Item::FK_NAME, order_by, pk);
}


QList<DatabaseObjectPtr> DiagnosisIcd10::getAncillarySpecimens() const
{
    return QList<DatabaseObjectPtr>{
        DatabaseObjectPtr(new DiagnosisIcd10Item(m_app, m_db)),
    };
}


// ============================================================================
// DiagnosisTaskBase extras
// ============================================================================

DiagnosticCodeSetPtr DiagnosisIcd10::makeCodeset() const
{
    return DiagnosticCodeSetPtr(new Icd10(m_app));
}


DiagnosisItemBasePtr DiagnosisIcd10::makeItem() const
{
    return DiagnosisItemBasePtr(new DiagnosisIcd10Item(m_app, m_db));
}
