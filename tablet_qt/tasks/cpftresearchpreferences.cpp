/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include <QPointer>
#include <QString>
#include <QStringList>
#include <QVector>

#include "cpftresearchpreferences.h"

#include "common/textconst.h"
#include "core/camcopsapp.h"
#include "db/databasemanager.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qupage.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"

const QString CPFTResearchPreferences::CPFTRESEARCHPREFERENCES_TABLENAME(
    "cpft_research_preferences");

void initializeCPFTResearchPreferences(TaskFactory& factory)
{
    static TaskRegistrar<CPFTResearchPreferences> registered(factory);
}


CPFTResearchPreferences::CPFTResearchPreferences(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, CPFTRESEARCHPREFERENCES_TABLENAME,
         false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    // TODO: Add fields here

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString CPFTResearchPreferences::shortname() const
{
    return "CPFT_Research_Preferences";
}


QString CPFTResearchPreferences::longname() const
{
    return tr("CPFT Research Preferences");
}


QString CPFTResearchPreferences::description() const
{
    return tr("CPFT Patients' preferences for being contacted about research");
}


// ============================================================================
// Instance info
// ============================================================================

bool CPFTResearchPreferences::isComplete() const
{
    // TODO

    return true;
}


QStringList CPFTResearchPreferences::summary() const
{
    // TODO

    return QStringList{TextConst::noSummarySeeFacsimile()};
}


QStringList CPFTResearchPreferences::detail() const
{
    QStringList lines;

    // TODO

    return completenessInfo() + lines;
}


OpenableWidget* CPFTResearchPreferences::editor(const bool read_only)
{
    QuPagePtr page(new QuPage);
    page->setTitle(description());
    page->addElement(new QuHeading(xstring("title")));

    // TODO: Page elements

    QVector<QuPagePtr> pages{page};

    m_questionnaire = new Questionnaire(m_app, pages);
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}
