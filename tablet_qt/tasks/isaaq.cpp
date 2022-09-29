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

#include "isaaq.h"
#include "common/textconst.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcqgrid.h"
#include "tasklib/taskfactory.h"
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_A_QUESTIONS = 15;
const int N_B_QUESTIONS = 10;
const QString A_PREFIX("a");
const QString B_PREFIX("b");


const QString Isaaq::ISAAQ_TABLENAME("isaaq");


void initializeIsaaq(TaskFactory& factory)
{
    static TaskRegistrar<Isaaq> registered(factory);
}

Isaaq::Isaaq(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    IsaaqCommon(app, db, ISAAQ_TABLENAME)
{
    addFields(strseq(A_PREFIX, FIRST_Q, N_A_QUESTIONS), QVariant::Int);
    addFields(strseq(B_PREFIX, FIRST_Q, N_B_QUESTIONS), QVariant::Int);

    load(load_pk);
}


// ============================================================================
// Class info
// ============================================================================

QString Isaaq::shortname() const
{
    return "ISAAQ";
}


QString Isaaq::longname() const
{
    return tr("Internet Severity and Activities Addiction Questionnaire");
}


QString Isaaq::description() const
{
    return tr("Questionnaire on problematic internet use.");
}


QStringList Isaaq::fieldNames() const
{
    return strseq(A_PREFIX, FIRST_Q, N_A_QUESTIONS) +
        strseq(B_PREFIX, FIRST_Q, N_B_QUESTIONS);
}


// ============================================================================
// Instance info
// ============================================================================

QVector<QuElement*> Isaaq::buildElements()
{
    auto instructions = new QuHeading(xstring("instructions"));
    auto grid_a = buildGrid(A_PREFIX, FIRST_Q, N_A_QUESTIONS, xstring("a_title"));
    auto grid_b_heading = new QuHeading(xstring("b_heading"));
    auto grid_b = buildGrid(B_PREFIX, FIRST_Q, N_B_QUESTIONS, xstring("b_title"));

    QVector<QuElement*> elements{
                    instructions,
                    grid_a,
                    grid_b_heading,
                    grid_b
    };

    return elements;
}
