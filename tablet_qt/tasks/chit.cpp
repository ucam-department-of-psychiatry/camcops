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

#include "chit.h"

#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using mathfunc::anyNull;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int LAST_Q = 15;
const int MIN_SCORE = 0;
const int MAX_SCORE = 4;
const int MAX_TOTAL_SCORE = MAX_SCORE * LAST_Q;
const QString QPREFIX("q");

const QString Chit::CHIT_TABLENAME("chit");

void initializeChit(TaskFactory& factory)
{
    static TaskRegistrar<Chit> registered(factory);
}

Chit::Chit(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, CHIT_TABLENAME, false, false, false),
    // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addFields(strseq(QPREFIX, FIRST_Q, LAST_Q), QMetaType::fromType<int>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Chit::shortname() const
{
    return "CHI-T";
}

QString Chit::longname() const
{
    return tr("Cambridge–Chicago Compulsivity Trait Scale");
}

QString Chit::description() const
{
    return tr("A scale designed to measure transdiagnostic compulsivity.");
}

QStringList Chit::scoredFieldNames() const
{
    return strseq(QPREFIX, FIRST_Q, LAST_Q);
}

Version Chit::minimumServerVersion() const
{
    return Version(2, 4, 15);
}

// ============================================================================
// Instance info
// ============================================================================


bool Chit::isComplete() const
{
    if (anyNull(values(scoredFieldNames()))) {
        return false;
    }

    return true;
}

int Chit::totalScore() const
{
    return sumInt(values(scoredFieldNames()));
}

QStringList Chit::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), MAX_TOTAL_SCORE)};
}

QStringList Chit::detail() const
{
    QStringList lines = completenessInfo();
    const QString spacer = " ";
    const QString suffix = QLatin1String("");
    lines += fieldSummaries("q", suffix, spacer, QPREFIX, FIRST_Q, LAST_Q);
    lines.append("");
    lines += summary();

    return lines;
}

OpenableWidget* Chit::editor(const bool read_only)
{
    NameValueOptions agreement_options;

    for (int i = MIN_SCORE; i <= MAX_SCORE; i++) {
        auto name = QString("a%1").arg(i);

        agreement_options.append({xstring(name), i});
    }

    QVector<QuestionWithOneField> q_field_pairs;

    for (const QString& fieldname : scoredFieldNames()) {
        const QString& description = xstring(fieldname);
        q_field_pairs.append(
            QuestionWithOneField(description, fieldRef(fieldname))
        );
    }
    auto grid = new QuMcqGrid(q_field_pairs, agreement_options);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);
    const int min_width_px = 100;
    const QVector<int> min_option_widths_px = {100, 100, 100, 100, 100};
    grid->setMinimumWidthInPixels(min_width_px, min_option_widths_px);

    QuPagePtr page((new QuPage{grid})->setTitle(xstring("title_main")));

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}
