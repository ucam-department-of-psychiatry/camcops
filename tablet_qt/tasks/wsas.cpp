/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "wsas.h"
#include "common/textconst.h"
#include "lib/mathfunc.h"
#include "lib/stringfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using mathfunc::noneNull;
using mathfunc::scoreString;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 5;
const int MAX_SCORE = 40;
const QString QPREFIX("q");

const QString WSAS_TABLENAME("wsas");

const QString RETIRED_ETC("retired_etc");


void initializeWsas(TaskFactory& factory)
{
    static TaskRegistrar<Wsas> registered(factory);
}


Wsas::Wsas(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, WSAS_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addField(RETIRED_ETC, QVariant::Bool);
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Wsas::shortname() const
{
    return "WSAS";
}


QString Wsas::longname() const
{
    return tr("Work and Social Adjustment Scale (¶+)");
}


QString Wsas::menusubtitle() const
{
    return tr("5-item self-report scale. Data collection tool ONLY unless "
              "host institution adds scale text.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Wsas::isComplete() const
{
    return noneNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


QStringList Wsas::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), MAX_SCORE)};
}


QStringList Wsas::detail() const
{
    return completenessInfo() + summary();
}


OpenableWidget* Wsas::editor(bool read_only)
{
    NameValueOptions options{
        {appstring("wsas_a0"), 0},
        {appstring("wsas_a1"), 1},
        {appstring("wsas_a2"), 2},
        {appstring("wsas_a3"), 3},
        {appstring("wsas_a4"), 4},
        {appstring("wsas_a5"), 5},
        {appstring("wsas_a6"), 6},
        {appstring("wsas_a7"), 7},
        {appstring("wsas_a8"), 8},
    };

    QVector<QuestionWithOneField> qfields;
    for (int i = FIRST_Q; i <= N_QUESTIONS; ++i) {
        qfields.append(QuestionWithOneField(
                           xstring(strnum("q", i), strnum("Q", i)),
                           fieldRef(strnum(QPREFIX, i))));
    }

    QuPagePtr page((new QuPage{
        (new QuText(xstring("instruction")))->setBold(),
        new QuBoolean(xstring("q_retired_etc"), fieldRef(RETIRED_ETC)),
        new QuMcqGrid(qfields, options),
    })->setTitle(longname()));

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Wsas::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}
