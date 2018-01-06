/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#include "phq9.h"
#include "common/textconst.h"
#include "maths/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int LAST_SCORED_Q = 9;
const int N_QUESTIONS = 10;
const int MAX_SCORE = 27;
const QString QPREFIX("q");

const QString Phq9::PHQ9_TABLENAME("phq9");


void initializePhq9(TaskFactory& factory)
{
    static TaskRegistrar<Phq9> registered(factory);
}


Phq9::Phq9(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, PHQ9_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Phq9::shortname() const
{
    return "PHQ-9";
}


QString Phq9::longname() const
{
    return tr("Patient Health Questionnaire-9");
}


QString Phq9::menusubtitle() const
{
    return tr("Self-scoring of the 9 depressive symptoms in DSM-IV.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Phq9::isComplete() const
{
    if (anyNull(values(strseq(QPREFIX, FIRST_Q, LAST_SCORED_Q)))) {
        return false;
    }
    if (value("q10").isNull()) {
        if (totalScore() == 0) {
            // You don't have to answer question 10 if the others are all
            // complete with a score of zero.
            return true;
        }
        return false;
    }
    return true;
}


QStringList Phq9::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), MAX_SCORE)};
}


QStringList Phq9::detail() const
{
    using stringfunc::bold;
    using uifunc::yesNo;

    const int totalscore = totalScore();
    const QString sev = severity(totalscore);
    const int ncore = nCoreSymptoms();
    const int nother = nOtherSymptoms();
    const int ntotal = ncore + nother;
    const bool mds = (ncore >= 1) && (ntotal >= 5);
    const bool ods = (ncore >= 1) && (ntotal >= 2) && (ntotal <= 4);
    // Scoring: ref PMID 10568646,
    // http://www.phqscreeners.com/instructions/instructions.pdf
    const QString spacer = " ";
    QStringList lines = completenessInfo();
    lines += fieldSummaries("q", "_s", spacer, QPREFIX, FIRST_Q, N_QUESTIONS);
    lines.append("");
    lines += summary();
    lines.append("");
    lines.append(xstring("mds") + spacer + bold(yesNo(mds)));
    lines.append(xstring("ods") + spacer + bold(yesNo(ods)));
    lines.append(xstring("depression_severity") + spacer + bold(sev));
    return lines;
}


OpenableWidget* Phq9::editor(const bool read_only)
{
    const NameValueOptions options_q1_9{
        {xstring("a0"), 0},
        {xstring("a1"), 1},
        {xstring("a2"), 2},
        {xstring("a3"), 3},
    };
    const NameValueOptions options_q10{
        {xstring("fa0"), 0},
        {xstring("fa1"), 1},
        {xstring("fa2"), 2},
        {xstring("fa3"), 3},
    };

    QuPagePtr page((new QuPage{
        (new QuText(xstring("stem")))->setBold(true),
        new QuMcqGrid(
            {
                QuestionWithOneField(xstring("q1"), fieldRef("q1")),
                QuestionWithOneField(xstring("q2"), fieldRef("q2")),
                QuestionWithOneField(xstring("q3"), fieldRef("q3")),
                QuestionWithOneField(xstring("q4"), fieldRef("q4")),
                QuestionWithOneField(xstring("q5"), fieldRef("q5")),
                QuestionWithOneField(xstring("q6"), fieldRef("q6")),
                QuestionWithOneField(xstring("q7"), fieldRef("q7")),
                QuestionWithOneField(xstring("q8"), fieldRef("q8")),
                QuestionWithOneField(xstring("q9"), fieldRef("q9")),
            },
            options_q1_9
        ),
        (new QuText(xstring("finalq")))->setBold(true),
        new QuMcq(fieldRef("q10"), options_q10),
    })->setTitle(xstring("title_main")));

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Phq9::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, LAST_SCORED_Q)));
}


int Phq9::nCoreSymptoms() const
{
    int n = 0;
    for (auto fieldname : strseq(QPREFIX, 1, 2)) {
        if (valueInt(fieldname) >= 2) {
            n += 1;
        }
    }
    return n;
}


int Phq9::nOtherSymptoms() const
{
    int n = 0;
    for (auto fieldname : strseq(QPREFIX, 3, 8)) {
        if (valueInt(fieldname) >= 2) {
            n += 1;
        }
    }
    if (valueInt(strnum(QPREFIX, 9)) >= 1) {
        // Suicidality: counted WHENEVER present
        n += 1;
    }
    return n;
}


QString Phq9::severity(const int score)
{
    if (score >= 20) return textconst::SEVERE;
    if (score >= 15) return textconst::MODERATELY_SEVERE;
    if (score >= 10) return textconst::MODERATE;
    if (score >=  5) return textconst::MILD;
    return textconst::NONE;
}
