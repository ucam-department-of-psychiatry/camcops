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

#include "lynalliamlife.h"
#include "common/textconst.h"
#include "lib/version.h"
#include "tasklib/taskfactory.h"


const QString LynallIamLife::LYNALL_IAM_LIFE_TABLENAME("lynall_iam_life");


void initializeLynallIamLife(TaskFactory& factory)
{
    static TaskRegistrar<LynallIamLife> registered(factory);
}


LynallIamLife::LynallIamLife(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, LYNALL_IAM_LIFE_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    // *** add fields

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString LynallIamLife::shortname() const
{
    return "Lynall_IAM_Life";
}


QString LynallIamLife::longname() const
{
    return tr("Lynall M-E — IAM — Life events");
}


QString LynallIamLife::description() const
{
    return tr("Life events questionnaire for IAM immunopsychiatry study.");
}


Version LynallIamLife::minimumServerVersion() const
{
    return Version(2, 3, 3);
}


// ============================================================================
// Instance info
// ============================================================================

bool LynallIamLife::isComplete() const
{
    // ***
}


QStringList LynallIamLife::summary() const
{
    return QStringList{textconst.noSummarySeeFacsimile()};
}


QStringList LynallIamLife::detail() const
{
    return QStringList{textconst.noDetailSeeFacsimile()};
}


OpenableWidget* LynallIamLife::editor(const bool read_only)
{
    // ***
}


// ============================================================================
// Signal handlers
// ============================================================================

void LynallIamLife::updateMandatory()
{
    // ***
}

#endif
