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
#include "db/databaseobject.h"
#include "lib/uifunc.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/qutext.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"

const QString CPFTResearchPreferences::CPFTRESEARCHPREFERENCES_TABLENAME(
    "cpft_research_preferences");

// Field names
const QString FN_CONTACT_PREFERENCE("contact_preference");
const QString FN_CONTACT_BY_EMAIL("contact_by_email");
const QString FN_RESEARCH_OPT_OUT("research_opt_out");

const QString Q_XML_PREFIX = "q_";

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
    addField(FN_CONTACT_PREFERENCE, QVariant::Char);
    addField(FN_CONTACT_BY_EMAIL, QVariant::Bool);
    addField(FN_RESEARCH_OPT_OUT, QVariant::Bool);

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
    if (valueIsNull(FN_CONTACT_PREFERENCE)) {
        return false;
    }

    if (valueIsNull(FN_CONTACT_BY_EMAIL)) {
        return false;
    }

    if (valueIsNull(FN_RESEARCH_OPT_OUT)) {
        return false;
    }

    return true;
}


QStringList CPFTResearchPreferences::summary() const
{
    QStringList lines;

    const QString fmt = QString("%1 <b>%2</b>");

    lines.append(fmt.arg(xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE),
                         valueQChar(FN_CONTACT_PREFERENCE)));
    lines.append(fmt.arg(xstring(Q_XML_PREFIX + FN_CONTACT_BY_EMAIL),
                         uifunc::yesNo(valueBool(FN_CONTACT_BY_EMAIL))));
    lines.append(fmt.arg(xstring(Q_XML_PREFIX + FN_RESEARCH_OPT_OUT),
                         uifunc::yesNo(valueBool(FN_RESEARCH_OPT_OUT))));

    return lines;
}


QStringList CPFTResearchPreferences::detail() const
{
    return completenessInfo() + summary();
}


OpenableWidget* CPFTResearchPreferences::editor(const bool read_only)
{
    QuPagePtr page(new QuPage);
    page->setTitle(description());
    page->addElement(new QuHeading(xstring("title")));

    page->addElement(new QuText(xstring("intro")));
    page->addElement(new QuText(xstring("decisions")));
    page->addElement(new QuText(xstring("research_info")));
    page->addElement(new QuText(xstring("database_info")));
    page->addElement(new QuText(xstring("permission")));

    page->addElement(new QuText(xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE)));
    NameValueOptions contact_options;
    contact_options.append(NameValuePair(xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE + "_option_R"), "R"));
    contact_options.append(NameValuePair(xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE + "_option_Y"), "Y"));
    contact_options.append(NameValuePair(xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE + "_option_G"), "G"));
    page->addElement(new QuMcq(fieldRef(FN_CONTACT_PREFERENCE),
                               contact_options));

    page->addElement(new QuText(xstring(Q_XML_PREFIX + FN_CONTACT_BY_EMAIL)));
    NameValueOptions email_options;
    email_options.append(NameValuePair(xstring(Q_XML_PREFIX + FN_CONTACT_BY_EMAIL + "_option_Y"), true));
    email_options.append(NameValuePair(xstring(Q_XML_PREFIX + FN_CONTACT_BY_EMAIL + "_option_N"), false));
    page->addElement(new QuMcq(fieldRef(FN_CONTACT_BY_EMAIL),
                               email_options));

    page->addElement(new QuText(xstring(Q_XML_PREFIX + FN_RESEARCH_OPT_OUT)));
    NameValueOptions opt_out_options;
    opt_out_options.append(NameValuePair(xstring(Q_XML_PREFIX + FN_RESEARCH_OPT_OUT + "_option_Y"), true));
    opt_out_options.append(NameValuePair(xstring(Q_XML_PREFIX + FN_RESEARCH_OPT_OUT + "_option_N"), false));
    page->addElement(new QuMcq(fieldRef(FN_RESEARCH_OPT_OUT),
                               opt_out_options));

    QVector<QuPagePtr> pages{page};

    m_questionnaire = new Questionnaire(m_app, pages);
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}
