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

#include "lynall2iam.h"
#include "common/textconst.h"
#include "lib/version.h"
#include "tasklib/taskfactory.h"


const QString Lynall2IamLifeEvents::LYNALL_2_IAM_LIFEEVENTS_TABLENAME(
        "lynall_1_iam_medicalhistory");


void initializeLynall2IamLifeEvents(TaskFactory& factory)
{
    static TaskRegistrar<Lynall2IamLifeEvents> registered(factory);
}


Lynall2IamLifeEvents::Lynall2IamLifeEvents(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, LYNALL_2_IAM_LIFEEVENTS_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    // *** add fields

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Lynall2IamLifeEvents::shortname() const
{
    return "Lynall_2_LifeEvents";
}


QString Lynall2IamLifeEvents::longname() const
{
    return "Lynall M-E — 2 — IAM — Life events";
}


QString Lynall2IamLifeEvents::description() const
{
    return "Life events questionnaire for IAM immunopsychiatry study.";
}


QString Lynall2IamLifeEvents::infoFilenameStem() const
{
    return "lynall_2";
}


Version Lynall2IamLifeEvents::minimumServerVersion() const
{
    return Version(2, 3, 3);
}


// ============================================================================
// Instance info
// ============================================================================

bool Lynall2IamLifeEvents::isComplete() const
{
    // ***
}


QStringList Lynall2IamLifeEvents::summary() const
{
    return QStringList{textconst::NO_SUMMARY_SEE_FACSIMILE()};
}


QStringList Lynall2IamLifeEvents::detail() const
{
    // ***
}


OpenableWidget* Lynall2IamLifeEvents::editor(const bool read_only)
{
    // ***
}


// ============================================================================
// Signal handlers
// ============================================================================

void Lynall2IamLifeEvents::updateMandatory()
{
    // ***
}

#endif
