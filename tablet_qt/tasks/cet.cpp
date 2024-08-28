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

#include "cet.h"

#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 24;
const int MIN_ANSWER = 0;
const int MAX_ANSWER = 5;
const int MAX_SUBSCALE_SCORE = MAX_ANSWER;
const int N_SUBSCALES = 5;
const int MAX_TOTAL_SCORE = MAX_SUBSCALE_SCORE * N_SUBSCALES;
const QVector<int> Q_REVERSE_SCORED{8, 12};
const QVector<int> Q_SUBSCALE_1_AVOID_RULE{9, 10, 11, 15, 16, 20, 22, 23};
const QVector<int> Q_SUBSCALE_2_WT_CONTROL{2, 6, 8, 13, 18};
const QVector<int> Q_SUBSCALE_3_MOOD{1, 4, 14, 17, 24};
const QVector<int> Q_SUBSCALE_4_LACK_EX_ENJOY{5, 12, 21};
const QVector<int> Q_SUBSCALE_5_EX_RIGIDITY{3, 7, 19};

const QString APREFIX("a");
const QString QPREFIX("q");
const QString SPREFIX("subscale");

const QString Cet::CET_TABLENAME("cet");

void initializeCet(TaskFactory& factory)
{
    static TaskRegistrar<Cet> registered(factory);
}

Cet::Cet(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, CET_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(
        strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QMetaType::fromType<int>()
    );

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Cet::shortname() const
{
    return "CET";
}

QString Cet::longname() const
{
    return tr("Compulsive Exercise Test");
}

QString Cet::description() const
{
    return tr("Self-rated 24-item questionnaire about compulsive exercise.");
}

// ============================================================================
// Instance info
// ============================================================================

bool Cet::isComplete() const
{
    using mathfunc::noneNull;
    return noneNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}

QStringList Cet::summary() const
{
    using mathfunc::scorePhrase;
    using mathfunc::totalScorePhrase;
    QStringList lines;
    const QVariant total = totalScore();
    if (total.isNull()) {
        lines.append("?");
    } else {
        lines.append(totalScorePhrase(total.toDouble(), MAX_TOTAL_SCORE));
        const QVector<double> subscales{
            subscale1AvoidanceRuleBased().toDouble(),
            subscale2WeightControl().toDouble(),
            subscale3MoodImprovement().toDouble(),
            subscale4LackEnjoyment().toDouble(),
            subscale5Rigidity().toDouble()};
        for (int i = 0; i < N_SUBSCALES; ++i) {
            const int s = i + 1;
            lines.append(scorePhrase(
                xstring(strnum(SPREFIX, s)),
                subscales.at(i),
                MAX_SUBSCALE_SCORE
            ));
        }
    }
    return lines;
}

OpenableWidget* Cet::editor(const bool read_only)
{
    NameValueOptions options;
    for (int a = MIN_ANSWER; a <= MAX_ANSWER; ++a) {
        options.append(NameValuePair(xstring(strnum(APREFIX, a)), a));
    }
    QVector<QuestionWithOneField> qfp;
    QVector<McqGridSubtitle> subtitles;
    for (int qnum = FIRST_Q; qnum <= N_QUESTIONS; ++qnum) {
        const QString qname = strnum(QPREFIX, qnum);
        const QString qtext = xstring(qname);
        qfp.append(QuestionWithOneField(qtext, fieldRef(qname)));
        const int qindex = qnum - 1;
        if (qindex > 0 && qindex % 6 == 0) {  // every 6
            subtitles.append(McqGridSubtitle(qindex));
        }
    }
    QuMcqGrid* grid = new QuMcqGrid(qfp, options);
    grid->setSubtitles(subtitles);

    QuPagePtr page(
        (new QuPage{
             (new QuText(xstring("instruction_title")))->setBold(true),
             new QuText(xstring("instruction_contents")),
             grid})
            ->setTitle(longname())
    );

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

QVariant Cet::score(const int question) const
{
    const QVariant v = value(strnum(QPREFIX, question));
    if (v.isNull()) {
        return v;  // to avoid silly scoring of incomplete tasks
    }
    const int raw = v.toInt();
    if (Q_REVERSE_SCORED.contains(question)) {
        // The range is from 0 to 5, so 5 - raw inverts the scoring.
        return MAX_ANSWER - raw;
    }
    return raw;
}

QVariant Cet::meanScore(const QVector<int>& questions) const
{
    QVector<QVariant> values;
    for (const int q : questions) {
        values.append(score(q));
    }
    return mathfunc::meanOrNull(values);
}

QVariant Cet::subscale1AvoidanceRuleBased() const
{
    return meanScore(Q_SUBSCALE_1_AVOID_RULE);
}

QVariant Cet::subscale2WeightControl() const
{
    return meanScore(Q_SUBSCALE_2_WT_CONTROL);
}

QVariant Cet::subscale3MoodImprovement() const
{
    return meanScore(Q_SUBSCALE_3_MOOD);
}

QVariant Cet::subscale4LackEnjoyment() const
{
    return meanScore(Q_SUBSCALE_4_LACK_EX_ENJOY);
}

QVariant Cet::subscale5Rigidity() const
{
    return meanScore(Q_SUBSCALE_5_EX_RIGIDITY);
}

QVariant Cet::totalScore() const
{
    const QVector<QVariant> subscale_totals{
        subscale1AvoidanceRuleBased(),
        subscale2WeightControl(),
        subscale3MoodImprovement(),
        subscale4LackEnjoyment(),
        subscale5Rigidity(),
    };
    return mathfunc::sumOrNull(subscale_totals);
}
