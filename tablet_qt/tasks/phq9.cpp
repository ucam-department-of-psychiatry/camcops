/*
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
#include "common/uiconstants.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using StringFunc::strseq;

const int FIRST_Q = 1;
const int LAST_SCORED_Q = 9;
const int N_QUESTIONS = 10;
const int MAX_SCORE = 27;
const QString QPREFIX("q");


void initializePhq9(TaskFactory& factory)
{
    static TaskRegistrar<Phq9> registered(factory);
}


Phq9::Phq9(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, "phq9", false, false, false)
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
    if (anyNull(strseq(QPREFIX, FIRST_Q, LAST_SCORED_Q))) {
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


QString Phq9::summary() const
{
    return totalScorePhrase(totalScore(), MAX_SCORE);
}


QString Phq9::detail() const
{
    using StringFunc::bold;
    using UiFunc::yesNo;

    int totalscore = totalScore();
    QString sev = severity(totalscore);
    int ncore = nCoreSymptoms();
    int nother = nOtherSymptoms();
    int ntotal = ncore + nother;
    bool mds = (ncore >= 1) && (ntotal >= 5);
    bool ods = (ncore >= 1) && (ntotal >= 2) && (ntotal <= 4);
    // Scoring: ref PMID 10568646,
    // http://www.phqscreeners.com/instructions/instructions.pdf
    QString spacer = ": ";
    QStringList lines = fieldSummaries("phq9_q", "_s", spacer,
                                       QPREFIX, FIRST_Q, N_QUESTIONS);
    lines.append("");
    lines.append(summary());
    lines.append("");
    lines.append(xstring("phq9_mds") + spacer + bold(yesNo(mds)));
    lines.append(xstring("phq9_ods") + spacer + bold(yesNo(ods)));
    lines.append(xstring("phq9_depression_severity") + spacer + bold(sev));
    return StringFunc::joinHtmlLines(lines);
}


OpenableWidget* Phq9::editor(bool read_only)
{
    NameValueOptions options_q1_9{
        {xstring("phq9_a0"), 0},
        {xstring("phq9_a1"), 1},
        {xstring("phq9_a2"), 2},
        {xstring("phq9_a3"), 3},
    };
    NameValueOptions options_q10{
        {xstring("phq9_fa0"), 0},
        {xstring("phq9_fa1"), 1},
        {xstring("phq9_fa2"), 2},
        {xstring("phq9_fa3"), 3},
    };

    QuPagePtr page((new QuPage{
        (new QuText(xstring("phq9_stem")))->bold(true),
        new QuMCQGrid(
            {
                QuestionWithOneField(xstring("phq9_q1"), fieldRef("q1")),
                QuestionWithOneField(xstring("phq9_q2"), fieldRef("q2")),
                QuestionWithOneField(xstring("phq9_q3"), fieldRef("q3")),
                QuestionWithOneField(xstring("phq9_q4"), fieldRef("q4")),
                QuestionWithOneField(xstring("phq9_q5"), fieldRef("q5")),
                QuestionWithOneField(xstring("phq9_q6"), fieldRef("q6")),
                QuestionWithOneField(xstring("phq9_q7"), fieldRef("q7")),
                QuestionWithOneField(xstring("phq9_q8"), fieldRef("q8")),
                QuestionWithOneField(xstring("phq9_q9"), fieldRef("q9")),
            },
            options_q1_9
        ),
        (new QuText(xstring("phq9_finalq")))->bold(true),
        new QuMCQ(fieldRef("q10"), options_q10),
    })->setTitle(xstring("phq9_title_main")));

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Phq9::totalScore() const
{
    return sumInt(strseq(QPREFIX, FIRST_Q, LAST_SCORED_Q));
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
    if (valueInt(StringFunc::strnum(QPREFIX, 9)) >= 1) {
        // Suicidality: counted WHENEVER present
        n += 1;
    }
    return n;
}


QString Phq9::severity(int score)
{
    if (score >= 20) return UiConst::SEVERE;
    if (score >= 15) return UiConst::MODERATELY_SEVERE;
    if (score >= 10) return UiConst::MODERATE;
    if (score >=  5) return UiConst::MILD;
    return UiConst::NONE;
}
