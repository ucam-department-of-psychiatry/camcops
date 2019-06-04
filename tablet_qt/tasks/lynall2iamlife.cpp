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

#include "lynall2iamlife.h"
#include "common/textconst.h"
#include "lib/version.h"
#include "tasklib/taskfactory.h"


const QString Lynall2IamLife::LYNALL_2_IAM_LIFE_TABLENAME("lynall_2_iam_life");


void initializeLynall2IamLife(TaskFactory& factory)
{
    static TaskRegistrar<Lynall2IamLife> registered(factory);
}


Lynall2IamLife::Lynall2IamLife(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, LYNALL_2_IAM_LIFE_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    // *** add fields

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Lynall2IamLife::shortname() const
{
    return "Lynall_2_IAM_Life";
}


QString Lynall2IamLife::longname() const
{
    return tr("Lynall M-E — 2 — IAM — Life events");
}


QString Lynall2IamLife::description() const
{
    return tr("Life events questionnaire for IAM immunopsychiatry study.");
}



Version Lynall2IamLife::minimumServerVersion() const
{
    return Version(2, 3, 3);
}


// ============================================================================
// Instance info
// ============================================================================

bool Lynall2IamLife::isComplete() const
{
    // ***
}


QStringList Lynall2IamLife::summary() const
{
    return QStringList{textconst.noSummarySeeFacsimile()};
}


QStringList Lynall2IamLife::detail() const
{
    return QStringList{textconst.noDetailSeeFacsimile()};
}


OpenableWidget* Lynall2IamLife::editor(const bool read_only)
{
    // ***
}


// ============================================================================
// Signal handlers
// ============================================================================

void Lynall2IamLife::updateMandatory()
{
    // ***
}

#endif
