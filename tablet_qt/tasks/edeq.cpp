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

#include "edeq.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/questionnaire.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 28;
const QString QPREFIX("q");


const QString Edeq::EDEQ_TABLENAME("edeq");


void initializeEdeq(TaskFactory& factory)
{
    static TaskRegistrar<Edeq> registered(factory);
}

Edeq::Edeq(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, EDEQ_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}
// ============================================================================
// Class info
// ============================================================================

QString Edeq::shortname() const
{
    return "EDE-Q";
}


QString Edeq::longname() const
{
    return tr("Eating Disorder Examination Questionnaire");
}


QString Edeq::description() const
{
    return tr("A self-report version of the Eating Disorder Examination (EDE)");
}


QStringList Edeq::fieldNames() const
{
    return strseq(QPREFIX, FIRST_Q, N_QUESTIONS);
}

// ============================================================================
// Instance info
// ============================================================================


bool Edeq::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}
