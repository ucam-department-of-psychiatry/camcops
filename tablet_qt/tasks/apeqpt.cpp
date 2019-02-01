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

const QString Apeqpt::APEQPT_TABLENAME("apeqpt");

const QString FN_DATETIME("q_datetime");
const QString FN_CHOICE("q_choice");
const QString FN_SATISFACTION("q_satisfaction");
const QString FN_EXPERIENCE("q_experience");

void initializeApeqpt(TaskFactory& factory)
{
    static TaskRegistrar<Apeqpt> registered(factory);
}

Apeqpt::Apeqpt(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, APEQPT_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField(FN_DATETIME, QVariant::DateTime);
    addField(FN_CHOICE, QVariant::Int);
    addField(FN_SATISFACTION, QVariant::Int);
    addField(FN_EXPERIENCE, QVariant::String);

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
    const QStringList required_always{
        FN_DATETIME,
        FN_CHOICE,
        FN_SATISFACTION,
    };

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

    QuPagePtr page(new QuPage{
    });

    page->setTitle(longname());

    m_questionnaire = new Questionnaire(m_app, {page});

    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================
