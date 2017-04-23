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

#include "phq15.h"
#include "common/textconst.h"
#include "lib/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using mathfunc::noneNull;
using mathfunc::sumInt;
using mathfunc::scorePhrase;
using mathfunc::totalScorePhrase;
using stringfunc::standardResult;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 15;
const int MAX_SCORE = 30;
const QString QPREFIX("q");

const QString PHQ15_TABLENAME("phq15");


void initializePhq15(TaskFactory& factory)
{
    static TaskRegistrar<Phq15> registered(factory);
}


Phq15::Phq15(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, PHQ15_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Phq15::shortname() const
{
    return "PHQ-15";
}


QString Phq15::longname() const
{
    return tr("Patient Health Questionnaire-15");
}


QString Phq15::menusubtitle() const
{
    return tr("Self-scoring of 15 common somatic symptoms (relevant to "
              "somatoform disorders).");
}


// ============================================================================
// Instance info
// ============================================================================

bool Phq15::isComplete() const
{
    QStringList relevant_fields;
    for (int i = FIRST_Q; i <= N_QUESTIONS; ++i) {
        if (i == 4 && !isFemale()) {
            continue;  // Q4 is for women only
        }
        relevant_fields.append(strnum(QPREFIX, i));
    }
    return noneNull(values(relevant_fields));
}


QStringList Phq15::summary() const
{
    return QStringList{
        totalScorePhrase(totalScore(), MAX_SCORE),
        scorePhrase(xstring("n_severe_symptoms"),
                    nSevereSymptoms(), N_QUESTIONS),
    };
}


QStringList Phq15::detail() const
{
    using stringfunc::bold;
    using uifunc::yesNo;
    QString spacer = " ";
    int n_severe = nSevereSymptoms();
    bool somatoform_likely = n_severe >= 3;
    int total_score = totalScore();
    QString severity = total_score >= 15
            ? textconst::SEVERE
            : (total_score >= 10 ? textconst::MODERATE
                                 : (total_score >= 5 ? textconst::MILD
                                                     : textconst::NONE));

    QStringList lines = completenessInfo();
    lines += fieldSummaries("q", "_s", spacer, QPREFIX, FIRST_Q, N_QUESTIONS);
    lines.append("");
    lines += summary();
    lines.append("");
    lines.append(xstring("exceeds_somatoform_cutoff") + spacer +
                 bold(yesNo(somatoform_likely)));
    lines.append(xstring("symptom_severity") + spacer + bold(severity));
    return lines;
}


OpenableWidget* Phq15::editor(bool read_only)
{
    NameValueOptions options{
        {xstring("a0"), 0},
        {xstring("a1"), 1},
        {xstring("a2"), 2},
    };
    QVector<QuestionWithOneField> qfields;
    for (int i = FIRST_Q; i <= N_QUESTIONS; ++i) {
        if (i == 4 && !isFemale()) {
            continue;  // Q4 is for women only
        }
        qfields.append(QuestionWithOneField(xstring(strnum("q", i)),
                                            fieldRef(strnum(QPREFIX, i))));
    }

    QuPagePtr page((new QuPage{
        (new QuText(xstring("stem")))->setBold(true),
        new QuMcqGrid(qfields, options),
    })->setTitle(xstring("title")));

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Phq15::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


int Phq15::nSevereSymptoms() const
{
    int n = 0;
    for (int i = FIRST_Q; i <= N_QUESTIONS; ++i) {
        n += valueInt(strnum(QPREFIX, i)) >= 2;
    }
    return n;
}
