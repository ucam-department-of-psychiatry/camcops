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

#include "cpftcovidmedical.h"

#include <QPointer>
#include <QString>
#include <QStringList>
#include <QVector>

#include "core/camcopsapp.h"
#include "db/databasemanager.h"
#include "db/databaseobject.h"
#include "lib/convert.h"
#include "lib/uifunc.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"

const QString CPFTCovidMedical::CPFTCOVIDMEDICAL_TABLENAME("cpft_covid_medical"
);

// Field names
const QString FN_HOW_AND_WHEN_SYMPTOMS("how_and_when_symptoms");

const QString Q_XML_PREFIX = "q_";

void initializeCPFTCovidMedical(TaskFactory& factory)
{
    static TaskRegistrar<CPFTCovidMedical> registered(factory);
}

CPFTCovidMedical::CPFTCovidMedical(
    CamcopsApp& app, DatabaseManager& db, const int load_pk
) :
    Task(
        app, db, CPFTCOVIDMEDICAL_TABLENAME, false, false, false
    ),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField(FN_HOW_AND_WHEN_SYMPTOMS, QMetaType::fromType<int>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString CPFTCovidMedical::shortname() const
{
    return "CPFT_Covid_Medical";
}

QString CPFTCovidMedical::longname() const
{
    return tr("CPFT Post-COVID-19 Clinic Medical Questionnaire");
}

QString CPFTCovidMedical::description() const
{
    return tr("CPFT post-COVID-19 clinic medical questionnaire");
}

// ============================================================================
// Instance info
// ============================================================================

bool CPFTCovidMedical::isComplete() const
{
    if (valueIsNull(FN_HOW_AND_WHEN_SYMPTOMS)) {
        return false;
    }

    return true;
}

QStringList CPFTCovidMedical::summary() const
{
    QStringList lines;

    const QString fmt = QString("%1: <b>%2</b><br>");

    lines.append(fmt.arg(
        xstring(Q_XML_PREFIX + FN_HOW_AND_WHEN_SYMPTOMS),
        getHowAndWhenSymptomsAnswerText()
    ));

    return lines;
}

QString CPFTCovidMedical::getHowAndWhenSymptomsAnswerText() const
{
    if (valueIsNull(FN_HOW_AND_WHEN_SYMPTOMS)) {
        return convert::NULL_STR;
    }

    const int answer_int = valueInt(FN_HOW_AND_WHEN_SYMPTOMS);

    const QString fmt = QString("%1_option%2");
    const QString answer_text
        = xstring(fmt.arg(FN_HOW_AND_WHEN_SYMPTOMS).arg(answer_int));

    return answer_text;
}

QStringList CPFTCovidMedical::detail() const
{
    return completenessInfo() + summary();
}

OpenableWidget* CPFTCovidMedical::editor(const bool read_only)
{
    QuPagePtr page(new QuPage);
    page->setTitle(description());
    page->addElement(
        (new QuText(xstring(Q_XML_PREFIX + FN_HOW_AND_WHEN_SYMPTOMS)))
            ->setBold(true)
    );
    NameValueOptions options;
    for (int i = 0; i < 4; ++i) {
        const QString fmt = QString("%1_option%2");
        const QString name = xstring(fmt.arg(FN_HOW_AND_WHEN_SYMPTOMS).arg(i));
        options.append(NameValuePair(name, i));
    }

    FieldRefPtr fieldref = fieldRef(FN_HOW_AND_WHEN_SYMPTOMS);

    page->addElement(new QuMcq(fieldref, options));
    QVector<QuPagePtr> pages{page};

    m_questionnaire = new Questionnaire(m_app, pages);
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}
