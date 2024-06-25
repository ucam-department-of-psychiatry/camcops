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

#include "cpftresearchpreferences.h"

#include <QPointer>
#include <QString>
#include <QStringList>
#include <QVector>

#include "core/camcopsapp.h"
#include "db/databasemanager.h"
#include "db/databaseobject.h"
#include "lib/uifunc.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"

const QString CPFTResearchPreferences::CPFTRESEARCHPREFERENCES_TABLENAME(
    "cpft_research_preferences"
);

// Field names
const QString FN_CONTACT_PREFERENCE("contact_preference");
const QString FN_CONTACT_BY_EMAIL("contact_by_email");
const QString FN_RESEARCH_OPT_OUT("research_opt_out");

const QString Q_XML_PREFIX = "q_";

const QChar CHOICE_RED = 'R';
const QChar CHOICE_YELLOW = 'Y';
const QChar CHOICE_GREEN = 'G';

void initializeCPFTResearchPreferences(TaskFactory& factory)
{
    static TaskRegistrar<CPFTResearchPreferences> registered(factory);
}

CPFTResearchPreferences::CPFTResearchPreferences(
    CamcopsApp& app, DatabaseManager& db, const int load_pk
) :
    Task(
        app, db, CPFTRESEARCHPREFERENCES_TABLENAME, false, false, false
    ),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField(FN_CONTACT_PREFERENCE, QMetaType::fromType<QChar>());
    addField(FN_CONTACT_BY_EMAIL, QMetaType::fromType<bool>());
    addField(
        FN_RESEARCH_OPT_OUT,
        QMetaType::fromType<bool>(),
        true,  // Mandatory
        false,  // Unique
        false,  // pk
        false
    );  // default

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
    return tr("CPFT patients' preferences for being contacted about research");
}

// ============================================================================
// Instance info
// ============================================================================

bool CPFTResearchPreferences::isComplete() const
{
    if (valueIsNull(FN_CONTACT_PREFERENCE)) {
        return false;
    }

    if (emailQuestionMandatory()) {
        return !valueIsNull(FN_CONTACT_BY_EMAIL);
    }

    // Opt-out defaults to false

    return true;
}

QStringList CPFTResearchPreferences::summary() const
{
    QStringList lines;

    const QString fmt = QString("%1: <b>%2</b><br>");

    lines.append(fmt.arg(
        xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE + "_short"),
        xstring(valueQChar(FN_CONTACT_PREFERENCE), "?")
    ));
    lines.append(fmt.arg(
        xstring(Q_XML_PREFIX + FN_CONTACT_BY_EMAIL + "_short"),
        uifunc::yesNoNull(value(FN_CONTACT_BY_EMAIL))
    ));
    lines.append(fmt.arg(
        xstring(Q_XML_PREFIX + FN_RESEARCH_OPT_OUT + "_short"),
        uifunc::yesNo(valueBool(FN_RESEARCH_OPT_OUT))
    ));

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

    page->addElement(
        (new QuText(xstring("decisions")))->setBold(true)->setItalic(true)
    );
    page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE))
    );
    page->addElement((new QuText(xstring("research_info")))->setOpenLinks());
    page->addElement((new QuText(xstring("database_info")))->setOpenLinks());
    page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE))
    );
    page->addElement(
        (new QuText(xstring("permission")))->setBold(true)->setItalic(true)
    );
    page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE))
    );
    page->addElement((new QuText(xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE))
    )
                         ->setBold(true));
    NameValueOptions contact_options;
    contact_options.append(NameValuePair(
        xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE + "_option_R"), CHOICE_RED
    ));
    contact_options.append(NameValuePair(
        xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE + "_option_Y"),
        CHOICE_YELLOW
    ));
    contact_options.append(NameValuePair(
        xstring(Q_XML_PREFIX + FN_CONTACT_PREFERENCE + "_option_G"),
        CHOICE_GREEN
    ));

    QStringList contact_styles
        = {"color:white; background-color:red;",
           "color:black; background-color:yellow;",
           "color:white; background-color:green;"};

    FieldRefPtr fieldref = fieldRef(FN_CONTACT_PREFERENCE);
    connect(
        fieldref.data(),
        &FieldRef::valueChanged,
        this,
        &CPFTResearchPreferences::updateEmailQuestion
    );

    page->addElement(new QuMcq(fieldref, contact_options, &contact_styles));
    page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE))
    );

    auto email_text = new QuText(xstring(Q_XML_PREFIX + FN_CONTACT_BY_EMAIL));
    email_text->setBold(true);
    email_text->addTag(FN_CONTACT_BY_EMAIL);

    page->addElement(email_text);
    NameValueOptions email_options;
    email_options.append(NameValuePair(
        xstring(Q_XML_PREFIX + FN_CONTACT_BY_EMAIL + "_option_Y"), true
    ));
    email_options.append(NameValuePair(
        xstring(Q_XML_PREFIX + FN_CONTACT_BY_EMAIL + "_option_N"), false
    ));

    auto email_mcq = new QuMcq(fieldRef(FN_CONTACT_BY_EMAIL), email_options);
    page->addElement(email_mcq);
    email_mcq->addTag(FN_CONTACT_BY_EMAIL);
    auto email_spacer
        = new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE));
    email_spacer->addTag(FN_CONTACT_BY_EMAIL);
    page->addElement(email_spacer);

    auto opt_out_text
        = new QuText(xstring(Q_XML_PREFIX + FN_RESEARCH_OPT_OUT + "_intro"));
    opt_out_text->setBold(true);
    page->addElement(opt_out_text);
    auto opt_out_checkbox = new QuBoolean(
        xstring(Q_XML_PREFIX + FN_RESEARCH_OPT_OUT),
        fieldRef(FN_RESEARCH_OPT_OUT)
    );
    opt_out_checkbox->setFalseAppearsBlank();
    page->addElement(opt_out_checkbox);
    page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE))
    );

    QVector<QuPagePtr> pages{page};

    m_questionnaire = new Questionnaire(m_app, pages);
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    updateEmailQuestion();

    return m_questionnaire;
}

// ============================================================================
// Signal handlers
// ============================================================================

void CPFTResearchPreferences::updateEmailQuestion()
{
    const bool mandatory = emailQuestionMandatory();

    if (mandatory) {
        fieldRef(FN_CONTACT_BY_EMAIL)->setMandatory(mandatory);
    }

    if (m_questionnaire) {
        m_questionnaire->setVisibleByTag(FN_CONTACT_BY_EMAIL, mandatory);
    }
}

bool CPFTResearchPreferences::emailQuestionMandatory() const
{
    return valueQChar(FN_CONTACT_PREFERENCE) != 'R';
}
