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

#include "aq10.h"

#include "aqfamily.h"
#include "db/databaseobject.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using stringfunc::strseq;

const int MIN_SCORE = 0;
const int MAX_SCORE = 10;

const QString Aq10::AQ10_TABLENAME("aq10");

void initializeAq10(TaskFactory& factory)
{
    static TaskRegistrar<Aq10> registered(factory);
}

Aq10::Aq10(
    CamcopsApp& app, DatabaseManager& db, const int load_pk, QObject* parent
) :
    AqFamily(
        app,
        db,
        AQ10_TABLENAME,
        10,  // Last question number
        {1, 7, 8, 10},  // agree scoring questions
        parent
    )
{
    addFields(
        strseq(m_q_prefix, m_first_q, m_last_q), QMetaType::fromType<int>()
    );

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Aq10::shortname() const
{
    return "AQ-10";
}

QString Aq10::longname() const
{
    return tr("Autism Spectrum Quotient – 10 items (Adult)");
}

QString Aq10::description() const
{
    return tr(
        "A 10-item self-administered \"red flag\" instrument to help "
        "frontline "
        "health professions decide whether to make a referral for a full "
        "diagnostic assessment for an autism spectrum condition (ASC) in "
        "adults."
    );
}

// ============================================================================
// Instance info
// ============================================================================

QStringList Aq10::summary() const
{
    return QStringList{
        rangeScore(xstring("score"), score(), MIN_SCORE, MAX_SCORE),
    };
}
