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

#include "phq8.h"

#include "common/textconst.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using mathfunc::anyNull;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 8;
const int MAX_QUESTION_SCORE = 24;  // 8 * 3
const QString QPREFIX(QStringLiteral("q"));

const QString Phq8::PHQ8_TABLENAME(QStringLiteral("phq8"));

void initializePhq8(TaskFactory& factory)
{
    static TaskRegistrar<Phq8> registered(factory);
}

Phq8::Phq8(
    CamcopsApp& app, DatabaseManager& db, const int load_pk, QObject* parent
) :
    Task(app, db, PHQ8_TABLENAME, false, false, false, parent),
    // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addFields(
        strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QMetaType::fromType<int>()
    );

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Phq8::shortname() const
{
    return QStringLiteral("PHQ-8");
}

QString Phq8::longname() const
{
    return tr("Patient Health Questionnaire 8-item depression scale");
}

QString Phq8::description() const
{
    return tr("Self-scoring of 8 depressive symptoms from DSM-IV.");
}

// ============================================================================
// Instance info
// ============================================================================

bool Phq8::isComplete() const
{
    if (anyNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)))) {
        return false;
    }
    return true;
}

QStringList Phq8::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), MAX_QUESTION_SCORE)};
}

QStringList Phq8::detail() const
{
    using stringfunc::bold;
    using uifunc::yesNo;

    const int totalscore = totalScore();
    const QString sev = severity(totalscore);
    const int ncore = nCoreSymptoms();
    const int nother = nOtherSymptoms();
    const int ntotal = ncore + nother;

    // Kroenke et al. (2009) PMID 18752852, p166 [annotations in square
    // brackets]:
    // 'Current depression was defined in two ways: 1) a PHQ-8 algorithm
    // diagnosis of major depression (this requires either the first or second
    // item (depressed mood or anhedonia) [CORE SYMPTOMS] to be present “more
    // than half the days” [SCORE >=2] and at least 5 of the 8 symptoms [TOTAL
    // SYMPTOMS] to be present “more than half the days” [SCORE >=2])...'

    const bool mds = (ncore >= 1) && (ntotal >= 5);

    // '... or other depression (2 to 4 [TOTAL] symptoms, including depressed
    // mood or anhedonia [AT LEAST ONE CORE], are required to be present “more
    // than half the days” [SCORE >=2])..."

    const bool ods = (ncore >= 1) && (ntotal >= 2) && (ntotal <= 4);

    const QString spacer(QStringLiteral(" "));
    QStringList lines = completenessInfo();
    lines += fieldSummaries(
        QStringLiteral("q"),
        QStringLiteral("_s"),
        spacer,
        QPREFIX,
        FIRST_Q,
        N_QUESTIONS
    );
    lines.append(QString());
    lines += summary();
    lines.append(QString());
    lines.append(xstring(QStringLiteral("mds")) + spacer + bold(yesNo(mds)));
    lines.append(xstring(QStringLiteral("ods")) + spacer + bold(yesNo(ods)));
    lines.append(
        xstring(QStringLiteral("depression_severity")) + spacer + bold(sev)
    );
    return lines;
}

OpenableWidget* Phq8::editor(const bool read_only)
{
    const NameValueOptions options_q1_9{
        {xstring(QStringLiteral("a0")), 0},
        {xstring(QStringLiteral("a1")), 1},
        {xstring(QStringLiteral("a2")), 2},
        {xstring(QStringLiteral("a3")), 3},
    };

    QuPagePtr page(
        (new QuPage{
             (new QuText(xstring(QStringLiteral("stem"))))->setBold(true),
             new QuMcqGrid(
                 {
                     QuestionWithOneField(
                         xstring(QStringLiteral("q1")),
                         fieldRef(QStringLiteral("q1"))
                     ),
                     QuestionWithOneField(
                         xstring(QStringLiteral("q2")),
                         fieldRef(QStringLiteral("q2"))
                     ),
                     QuestionWithOneField(
                         xstring(QStringLiteral("q3")),
                         fieldRef(QStringLiteral("q3"))
                     ),
                     QuestionWithOneField(
                         xstring(QStringLiteral("q4")),
                         fieldRef(QStringLiteral("q4"))
                     ),
                     QuestionWithOneField(
                         xstring(QStringLiteral("q5")),
                         fieldRef(QStringLiteral("q5"))
                     ),
                     QuestionWithOneField(
                         xstring(QStringLiteral("q6")),
                         fieldRef(QStringLiteral("q6"))
                     ),
                     QuestionWithOneField(
                         xstring(QStringLiteral("q7")),
                         fieldRef(QStringLiteral("q7"))
                     ),
                     QuestionWithOneField(
                         xstring(QStringLiteral("q8")),
                         fieldRef(QStringLiteral("q8"))
                     ),
                 },
                 options_q1_9
             ),
         })
            ->setTitle(xstring(QStringLiteral("title_main")))
    );

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

int Phq8::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}

int Phq8::nCoreSymptoms() const
{
    int n = 0;
    const QStringList fieldnames = strseq(QPREFIX, 1, 2);
    for (const QString& fieldname : fieldnames) {
        if (valueInt(fieldname) >= 2) {
            n += 1;
        }
    }
    return n;
}

int Phq8::nOtherSymptoms() const
{
    int n = 0;
    const QStringList fieldnames = strseq(QPREFIX, 3, 8);
    for (const QString& fieldname : fieldnames) {
        if (valueInt(fieldname) >= 2) {
            n += 1;
        }
    }
    return n;
}

QString Phq8::severity(const int score)
{
    // Kroenke et al. (2009) PMID 18752852, p166:
    // "The frequency distribution of major depression and other depression by
    // standard PHQ-8 severity intervals (0–4, 5–9, 10–14, 15–19, and
    // 20–24)..."

    if (score >= 20) {
        return TextConst::severe();
    }
    if (score >= 15) {
        return TextConst::moderatelySevere();
    }
    if (score >= 10) {
        return TextConst::moderate();
    }
    if (score >= 5) {
        return TextConst::mild();
    }
    return TextConst::none();
}
