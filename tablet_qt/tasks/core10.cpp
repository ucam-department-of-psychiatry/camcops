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

#include "core10.h"
#include "common/textconst.h"
#include "maths/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using mathfunc::countNotNull;
using mathfunc::sumInt;
using mathfunc::scorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 10;
const int MAX_SCORE = 40;
const QString QPREFIX("q");

const QString Core10::CORE10_TABLENAME("core10");


void initializeCore10(TaskFactory& factory)
{
    static TaskRegistrar<Core10> registered(factory);
}


Core10::Core10(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, CORE10_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Core10::shortname() const
{
    return "CORE-10";
}


QString Core10::longname() const
{
    return tr("Clinical Outcomes in Routine Evaluation, 10-item measure");
}


QString Core10::menusubtitle() const
{
    return tr("Self-rating of distress (wellbeing, symptoms, functioning, "
              "risk)");
}


Version Core10::minimumServerVersion() const
{
    return Version(2, 2, 8);
}


// ============================================================================
// Instance info
// ============================================================================

bool Core10::isComplete() const
{
    return !anyNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


QStringList Core10::summary() const
{
    return QStringList{
        scorePhrase(tr("Clinical score"), clinicalScore(), MAX_SCORE)
    };
}


QStringList Core10::detail() const
{
    const QString spacer = " ";
    QStringList lines = completenessInfo();
    lines += fieldSummaries("q", "_s", spacer, QPREFIX, FIRST_Q, N_QUESTIONS);
    lines.append("");
    lines += summary();
    return lines;
}


OpenableWidget* Core10::editor(const bool read_only)
{
    const NameValueOptions options_normal{
        {xstring("a0"), 0},
        {xstring("a1"), 1},
        {xstring("a2"), 2},
        {xstring("a3"), 3},
        {xstring("a4"), 4},
    };
    const NameValueOptions options_reversed{
        {xstring("a0"), 4},
        {xstring("a1"), 3},
        {xstring("a2"), 2},
        {xstring("a3"), 1},
        {xstring("a4"), 0},
    };

    // The problem here: two questions (Q2, Q3) are reverse-scored, but
    // we want that to be invisible to the user, while keeping an aligned
    // grid and not repeating titles.
    const int question_width = 50;
    const QVector<int> option_widths{10, 10, 10, 10, 10};

    QuPagePtr page((new QuPage{
        (new QuText(xstring("instruction_1")))->setBold(true),
        new QuText(xstring("instruction_2")),
        (new QuMcqGrid(
            {
                QuestionWithOneField(xstring("q1"), fieldRef("q1")),
            },
            options_normal
        ))
            ->setTitle(xstring("stem"))
            ->setWidth(question_width, option_widths)
            ->setExpand(true)
            ->setQuestionsBold(false),
        (new QuMcqGrid(
            {
                QuestionWithOneField(xstring("q2"), fieldRef("q2")),
                QuestionWithOneField(xstring("q3"), fieldRef("q3")),
            },
            options_reversed
        ))
            ->showTitle(false)
            ->setWidth(question_width, option_widths)
            ->setExpand(true)
            ->setQuestionsBold(false),
        (new QuMcqGrid(
            {
                QuestionWithOneField(xstring("q4"), fieldRef("q4")),
                QuestionWithOneField(xstring("q5"), fieldRef("q5")),
                QuestionWithOneField(xstring("q6"), fieldRef("q6")),
                QuestionWithOneField(xstring("q7"), fieldRef("q7")),
                QuestionWithOneField(xstring("q8"), fieldRef("q8")),
                QuestionWithOneField(xstring("q9"), fieldRef("q9")),
                QuestionWithOneField(xstring("q10"), fieldRef("q10")),
            },
            options_normal
        ))
            ->showTitle(false)
            ->setWidth(question_width, option_widths)
            ->setExpand(true)
            ->setQuestionsBold(false),
        (new QuText(xstring("thanks")))->setBold(true),
    })->setTitle(xstring("title")));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Core10::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


int Core10::nQuestionsCompleted() const
{
    return countNotNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


double Core10::clinicalScore() const
{
    return static_cast<double>(N_QUESTIONS * totalScore()) /
            static_cast<double>(nQuestionsCompleted());
}
