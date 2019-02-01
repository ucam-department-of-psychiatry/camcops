#include "apeqpt.h"

/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#include "apeqpt.h"
#include "common/textconst.h"
#include "maths/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quhorizontalcontainer.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/quslider.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "questionnairelib/quverticalcontainer.h"
#include "tasklib/taskfactory.h"

using mathfunc::anyNullOrEmpty;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strseq;

const QString Apeqpt::APEQPT_TABLENAME("apeqpt");

const QString FN_DATETIME("q_datetime");

const QString CHOICE_SUFFIX("_choice");
const QString SAT_SUFFIX("_satisfaction");

void initializeApeqpt(TaskFactory& factory)
{
    static TaskRegistrar<Apeqpt> registered(factory);
}

Apeqpt::Apeqpt(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, APEQPT_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField(FN_DATETIME, QVariant::DateTime);

    for (const QString& field : strseq("q", 1, 3, CHOICE_SUFFIX)) {
        addField(field, QVariant::Int);
    }

    for (const QString& field : strseq("q", 1, 2, SAT_SUFFIX)) {
        addField(field, QVariant::Int);
    }

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Apeqpt::shortname() const
{
    return "APEQ-PT";
}


QString Apeqpt::longname() const
{
    return tr("Assessment Patient Experience Questionnaire: "
              "For Psychological Therapies");
}


QString Apeqpt::menusubtitle() const
{
    return tr("Patient feedback questionnaire on treatment received");
}

// ============================================================================
// Instance info
// ============================================================================

bool Apeqpt::isComplete() const
{
    QStringList required_always;

    for (const QString& field : strseq("q", 1, 2, SAT_SUFFIX)) {
        required_always.append(field);
    }

    for (const QString& field : strseq("q", 1, 3, CHOICE_SUFFIX)) {
        required_always.append(field);
    }

    required_always.append(FN_DATETIME);

    return !anyNullOrEmpty(values(required_always));
}


QStringList Apeqpt::summary() const
{
    return QStringList{};
}


QStringList Apeqpt::detail() const
{
    QStringList lines;

    lines.append(summary());
    return lines;
}


OpenableWidget* Apeqpt::editor(const bool read_only)
{
    const NameValueOptions options {
        {xstring("a0"), 0}, // Yes
        {xstring("a1"), 1}, // No
    };

    const NameValueOptions options_na {
        {xstring("a0"), 0}, // Yes
        {xstring("a1"), 1}, // No
        {xstring("a2"), 2}, // No
    };

    QuPagePtr page(new QuPage{
        (new QuText(xstring("instructions_to_subject_1")))->setItalic(),
        (new QuText(xstring("instructions_to_subject_2")))->setItalic(),
        (new QuGridContainer {
            QuGridCell(new QuText(xstring("q_date")), 0, 0),
            QuGridCell((new QuDateTime(fieldRef(FN_DATETIME)))
                ->setMode(QuDateTime::DefaultDate)
                ->setOfferNowButton(true), 0, 1)
        }),
        (new QuText(xstring("h1")))->setBig()->setBold(),
        new QuMcqGrid(
            {
                QuestionWithOneField(xstring("q1_choice"), fieldRef("q1_choice")),
                QuestionWithOneField(xstring("q2_choice"), fieldRef("q2_choice")),
                QuestionWithOneField(xstring("q3_choice"), fieldRef("q3_choice")),
            }, options
        ),
        (new QuText(xstring("h2")))->setBig()->setBold(),
        new QuMcqGrid(
            {
                QuestionWithOneField(xstring("q1_satisfaction"), fieldRef("q1_satisfaction"))
            }, options_na
        ),
        new QuText(xstring("q2_satisfaction")),
        (new QuText(xstring("thanks")))->setItalic(),
    });

    page->setTitle(longname());

    m_questionnaire = new Questionnaire(m_app, {page});

    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================
