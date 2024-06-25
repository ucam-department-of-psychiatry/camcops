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

#include "isaaqed.h"

#include "lib/stringfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using stringfunc::strseq;

const int FIRST_Q = 11;
const int LAST_Q = 20;
const QString Q_PREFIX("e");


const QString IsaaqEd::ISAAQED_TABLENAME("isaaqed");

void initializeIsaaqEd(TaskFactory& factory)
{
    static TaskRegistrar<IsaaqEd> registered(factory);
}

IsaaqEd::IsaaqEd(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    IsaaqCommon(app, db, ISAAQED_TABLENAME)
{
    addFields(strseq(Q_PREFIX, FIRST_Q, LAST_Q), QMetaType::fromType<int>());

    load(load_pk);
}

// ============================================================================
// Class info
// ============================================================================

QString IsaaqEd::shortname() const
{
    return "ISAAQ-ED";
}

QString IsaaqEd::longname() const
{
    return tr(
        "Internet Severity and Activities Addiction Questionnaire, Eating "
        "Disorders Appendix"
    );
}

QString IsaaqEd::description() const
{
    return tr(
        "Supplementary questionnaire (see ISAAQ) on problematic internet use "
        "relating to eating disorders."
    );
}

QStringList IsaaqEd::fieldNames() const
{
    return strseq(Q_PREFIX, FIRST_Q, LAST_Q);
}

QVector<QuElement*> IsaaqEd::buildElements()
{
    auto heading = new QuHeading(xstring("heading"));
    auto grid = buildGrid(Q_PREFIX, FIRST_Q, LAST_Q, xstring("grid_title"));

    QVector<QuElement*> elements{heading, grid};

    return elements;
}
