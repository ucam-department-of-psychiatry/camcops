/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#if 0

#include "lynall1iam.h"
#include "common/textconst.h"
#include "lib/version.h"
#include "tasklib/taskfactory.h"


const QString Lynall1IamMedicalHistory::LYNALL_1_IAM_MEDICALHISTORY_TABLENAME(
        "lynall_1_iam_medicalhistory");


void initializeLynall1IamMedicalHistory(TaskFactory& factory)
{
    static TaskRegistrar<Lynall1IamMedicalHistory> registered(factory);
}


Lynall1IamMedicalHistory::Lynall1IamMedicalHistory(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, LYNALL_1_IAM_MEDICALHISTORY_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    // *** add fields

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Lynall1IamMedicalHistory::shortname() const
{
    return "Lynall_1_MedicalHistory";
}


QString Lynall1IamMedicalHistory::longname() const
{
    return "Lynall M-E — 1 — IAM — Medical history";
}


QString Lynall1IamMedicalHistory::description() const
{
    return "Medical history details for IAM immunopsychiatry study.";
}


QString Lynall1IamMedicalHistory::infoFilenameStem() const
{
    return "lynall_1";
}


Version Lynall1IamMedicalHistory::minimumServerVersion() const
{
    return Version(2, 3, 3);
}


// ============================================================================
// Instance info
// ============================================================================

bool Lynall1IamMedicalHistory::isComplete() const
{
    // ***
}


QStringList Lynall1IamMedicalHistory::summary() const
{
    return QStringList{textconst::NO_SUMMARY_SEE_FACSIMILE()};
}


QStringList Lynall1IamMedicalHistory::detail() const
{
    // ***
}


OpenableWidget* Lynall1IamMedicalHistory::editor(const bool read_only)
{
    // ***
}


// ============================================================================
// Signal handlers
// ============================================================================

void Lynall1IamMedicalHistory::updateMandatory()
{
    // ***
}

#endif
