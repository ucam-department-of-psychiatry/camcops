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

#include "gaf.h"

#include "common/appstrings.h"
#include "common/textconst.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"

const QString QPREFIX("q");
const QString Gaf::GAF_TABLENAME("gaf");
const QString SCORE("score");

void initializeGaf(TaskFactory& factory)
{
    static TaskRegistrar<Gaf> registered(factory);
}

Gaf::Gaf(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, GAF_TABLENAME, false, true, false)  // ... anon, clin, resp
{
    addField(SCORE, QMetaType::fromType<QString>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Gaf::shortname() const
{
    return "GAF";
}

QString Gaf::longname() const
{
    return tr("Global Assessment of Functioning");
}

QString Gaf::description() const
{
    return tr("Single scale from 1–100.");
}

// ============================================================================
// Instance info
// ============================================================================

bool Gaf::isComplete() const
{
    const int score = valueInt(SCORE);
    // ... an absent score will give 0 and thus fail
    return score >= 1 && score <= 100;
}

QStringList Gaf::summary() const
{
    return QStringList{fieldSummary(SCORE, appstring(appstrings::GAF_SCORE))};
}

QStringList Gaf::detail() const
{
    return completenessInfo() + summary();
}

OpenableWidget* Gaf::editor(const bool read_only)
{
    QuPagePtr page(
        (new QuPage{
             getClinicianQuestionnaireBlockRawPointer(),
             (new QuText(TextConst::dataCollectionOnlyAnnouncement()))
                 ->setBold(),
             new QuText(appstring(appstrings::GAF_SCORE) + ":"),
             new QuLineEditInteger(fieldRef(SCORE), 0, 100),
         })
            ->setTitle(longname())
    );

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Clinician);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}
