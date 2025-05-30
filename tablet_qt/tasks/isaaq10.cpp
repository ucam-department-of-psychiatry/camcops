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

#include "isaaq10.h"

#include "lib/stringfunc.h"
#include "lib/version.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_A_QUESTIONS = 10;
const int N_B_QUESTIONS = 10;
const QString A_PREFIX("a");
const QString B_PREFIX("b");


const QString Isaaq10::ISAAQ10_TABLENAME("isaaq10");
const QString OLD_ISAAQ_TABLENAME("isaaq");
const Version ISAAQ10_REPLACES_ISAAQ(2, 4, 15);

void initializeIsaaq10(TaskFactory& factory)
{
    static TaskRegistrar<Isaaq10> registered(factory);
}

Isaaq10::Isaaq10(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    IsaaqCommon(app, db, ISAAQ10_TABLENAME)
{
    addFields(
        strseq(A_PREFIX, FIRST_Q, N_A_QUESTIONS), QMetaType::fromType<int>()
    );
    addFields(
        strseq(B_PREFIX, FIRST_Q, N_B_QUESTIONS), QMetaType::fromType<int>()
    );

    load(load_pk);
}

// ============================================================================
// Class info
// ============================================================================

QString Isaaq10::shortname() const
{
    return "ISAAQ-10";
}

QString Isaaq10::longname() const
{
    return tr(
        "Internet Severity and Activities Addiction Questionnaire, 10-items"
    );
}

QString Isaaq10::description() const
{
    return tr("Questionnaire on problematic internet use.");
}

QStringList Isaaq10::fieldNames() const
{
    return strseq(A_PREFIX, FIRST_Q, N_A_QUESTIONS)
        + strseq(B_PREFIX, FIRST_Q, N_B_QUESTIONS);
}

void Isaaq10::upgradeDatabase(
    const Version& old_version, const Version& new_version
)
{
    Q_UNUSED(old_version)
    if (old_version < ISAAQ10_REPLACES_ISAAQ
        && new_version >= ISAAQ10_REPLACES_ISAAQ) {
        // The actual version check is a bit redundant. In principle we might
        // care if we ever re-introduce the "isaaq" table, but we shouldn't do
        // that. The purpose here is that if we upgrade the client in place
        // from a version before 2.4.15 (when the ISAAQ-10 task arrives and the
        // old 15-item ISAAQ task is deleted), we must delete the old "isaaq"
        // table, or the server will fail on upload.
        m_db.dropTable(OLD_ISAAQ_TABLENAME);
    }
}

// ============================================================================
// Instance info
// ============================================================================

QVector<QuElement*> Isaaq10::buildElements()
{
    auto instructions = new QuHeading(xstring("instructions"));
    auto grid_a
        = buildGrid(A_PREFIX, FIRST_Q, N_A_QUESTIONS, xstring("a_title"));
    auto grid_b_heading = new QuHeading(xstring("b_heading"));
    auto grid_b
        = buildGrid(B_PREFIX, FIRST_Q, N_B_QUESTIONS, xstring("b_title"));

    QVector<QuElement*> elements{instructions, grid_a, grid_b_heading, grid_b};

    return elements;
}
