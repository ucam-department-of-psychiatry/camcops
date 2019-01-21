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

#include "gbo.h"
#include "common/textconst.h"
#include "maths/mathfunc.h"
#include "lib/datetime.h"
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
using mathfunc::anyNull;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

// Field constants
const QString SESSION_NUMBER("session_n");
const QString SESSION_DATE("session_d");
const QString GOAL_NUMBER("goal_n");
const QString GOAL_DESCRIPTION("goal_desc");
const QString GOAL_PROGRESS("goal_p");
const QString GOAL_CHOSEN_BY("chosen_by");
const QString GOAL_CHOSEN_BY_OTHER("chosen_by_other");

const QStringList REQUIRED_FIELDS = {
    SESSION_NUMBER,
    SESSION_DATE,
    GOAL_NUMBER,
    GOAL_DESCRIPTION,
    GOAL_PROGRESS,
    GOAL_CHOSEN_BY,
};

const int CHOSEN_BY_CHILD   = 0;
const int CHOSEN_BY_PARENT  = 1;
const int CHOSEN_BY_OTHER   = 2;

const int MAX_GOALS = 1000;
const int MAX_SESSIONS = 1000;

const QString Gbo::GBO_TABLENAME("gbo");

void initializeGbo(TaskFactory& factory)
{
    static TaskRegistrar<Gbo> registered(factory);
}

Gbo::Gbo(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, GBO_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    m_goal_chosen_by = NameValueOptions{
        { xstring("choice_o1"), CHOSEN_BY_CHILD },
        { xstring("choice_o2"), CHOSEN_BY_PARENT },
        { xstring("choice_o3") + " " + xstring("choice_o3_specify"),
            CHOSEN_BY_OTHER },
    };

    addField(SESSION_NUMBER, QVariant::Int);
    addField(SESSION_DATE, QVariant::Date);

    addField(GOAL_NUMBER, QVariant::Int);
    addField(GOAL_DESCRIPTION, QVariant::String);
    addField(GOAL_PROGRESS, QVariant::Int);

    addField(GOAL_CHOSEN_BY, QVariant::Int);
    addField(GOAL_CHOSEN_BY_OTHER, QVariant::String);

    // Extra initialization:m_goal_chosen_by
    if (load_pk == dbconst::NONEXISTENT_PK) {
        setValue(SESSION_DATE, datetime::nowDate(), false);
    }

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Gbo::shortname() const
{
    return "GBO";
}


QString Gbo::longname() const
{
    return tr("Goal-based Outcomes");
}


QString Gbo::menusubtitle() const
{
    return tr("Goal progress tracking measurement");
}


// ============================================================================
// Instance info
// ============================================================================

OpenableWidget* Gbo::editor(const bool read_only)
{
    NameValueOptions options_progress{
        {"1", 1},
        {"2", 2},
        {"3", 3},
        {"4", 4},
        {"5", 5},
        {"6", 6},
        {"7", 7},
        {"8", 8},
        {"9", 9},
        {"10", 10}
    };

    QuPagePtr page((new QuPage{
        (new QuText(xstring(SESSION_NUMBER)))->setBold(),
        new QuLineEditInteger(fieldRef(SESSION_NUMBER), 1, MAX_SESSIONS),
        (new QuText(xstring(SESSION_DATE)))->setBold(),
        (new QuDateTime(fieldRef(SESSION_DATE)))
            ->setMode(QuDateTime::Mode::DefaultDate)
            ->setOfferNowButton(true),
        (new QuText(xstring(GOAL_NUMBER)))->setBold(),
        new QuLineEditInteger(fieldRef(GOAL_NUMBER), 1, MAX_GOALS),
        (new QuText(xstring(GOAL_DESCRIPTION)))->setBold(),
        new QuTextEdit(fieldRef(GOAL_DESCRIPTION)),
        (new QuText(xstring(GOAL_PROGRESS)))->setBold(),
        (new QuMcq(fieldRef(GOAL_PROGRESS), options_progress))
                           ->setHorizontal(true)
                           ->setAsTextButton(true),
        (new QuMcq(fieldRef(GOAL_CHOSEN_BY), m_goal_chosen_by))
                        ->setHorizontal(true)
                        ->setAsTextButton(true),
        new QuTextEdit(fieldRef(GOAL_CHOSEN_BY_OTHER, false)),
        })->setTitle(longname()));

    bool required = value(GOAL_CHOSEN_BY) == CHOSEN_BY_OTHER;
    fieldRef(GOAL_CHOSEN_BY_OTHER)->setMandatory(required);

    connect(fieldRef(GOAL_CHOSEN_BY).data(), &FieldRef::valueChanged,
            this, &Gbo::updateMandatory);

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}

void Gbo::updateMandatory() {
   const bool required = valueInt(GOAL_CHOSEN_BY)
           == CHOSEN_BY_OTHER;
    fieldRef(GOAL_CHOSEN_BY_OTHER)->setMandatory(required);
    if (!required) {
        fieldRef(GOAL_CHOSEN_BY_OTHER)->setValue("");
    }
}

bool Gbo::isComplete() const
{
    if (anyNull(values(REQUIRED_FIELDS))) {
        return false;
    }
    return ((value(GOAL_CHOSEN_BY) != CHOSEN_BY_OTHER) ||
            !value(GOAL_CHOSEN_BY_OTHER).isNull());

}

QStringList Gbo::summary() const
{   
    return QStringList{
        QString("<b>Goal %1</b>: %2").arg(
                value(GOAL_NUMBER).toString(),
                value(GOAL_DESCRIPTION).toString()
        )
    };
}

QStringList Gbo::detail() const
{
    QStringList summary;

    for (auto xfield : REQUIRED_FIELDS) {
        auto field = xstring(xfield);
        auto val   = value(xfield);

        QString sVal = (field == GOAL_CHOSEN_BY) ?
                        m_goal_chosen_by.nameFromValue(val.toInt()) : val.toString();

        summary.append(QString("%1: %2").arg(field, sVal));
    }

    return summary;
}
