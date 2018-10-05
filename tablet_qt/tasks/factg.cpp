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

#include "factg.h"
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
const int N_QUESTIONS = 27;
const int N_SECTIONS = 4;

const int SECTION_1_START = 1;
const int SECTION_2_START = 8;
const int SECTION_3_START = 15;
const int SECTION_4_START = 21;

const QString QPREFIX("q");

const QString Factg::FACTG_TABLENAME("factg");


void initializeFactg(TaskFactory& factory)
{
    static TaskRegistrar<Factg> registered(factory);
}


Factg::Factg(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, FACTG_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Factg::shortname() const
{
    return "FACT-G";
}


QString Factg::longname() const
{
    return tr("Functional Assessment of Cancer Therapy—General");
}


QString Factg::menusubtitle() const
{
    return tr("A 27-item general cancer quality-of-life (QL) measure - version 4.");
}


Version Factg::minimumServerVersion() const
{
    return Version(2, 2, 8);
}


// ============================================================================
// Instance info
// ============================================================================

bool Factg::isComplete() const
{
    return !anyNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


QStringList Factg::summary() const
{
    return QStringList{
//        scorePhrase(tr("Clinical score"), clinicalScore(), MAX_SCORE)
    };
}


QStringList Factg::detail() const
{
    const QString spacer = " ";
    QStringList lines = completenessInfo();
    lines += fieldSummaries("q", "_s", spacer, QPREFIX, FIRST_Q, N_QUESTIONS);
    lines.append("");
    lines += summary();
    return lines;
}


OpenableWidget* Factg::editor(const bool read_only)
{
    const NameValueOptions options{
        {xstring("a0"), 0},
        {xstring("a1"), 1},
        {xstring("a2"), 2},
        {xstring("a3"), 3},
        {xstring("a4"), 4}
    };

    const QVector<McqGridSubtitle> subtitles{
        {0, "Physical Well-being"},
        {7, "Social/Family Well-being"},
        {14, "Emotional Well-being"},
        {20, "Functional Well-being"},
    };

    QVector<QuestionWithOneField> qfields;
    QString xstring_section_prefix = "";

    int s_num = 0;
    int q_num = 0;

    for (int i = FIRST_Q; s_num <= N_SECTIONS && i <= N_QUESTIONS; ++i, ++q_num) {
        switch(i) {
        case SECTION_1_START:
        case SECTION_2_START:
        case SECTION_3_START:
        case SECTION_4_START:
            ++s_num;
            q_num = 1;
            xstring_section_prefix = strnum("s", s_num, "_");
        }
        QString xstringname = strnum(xstring_section_prefix + "q", q_num);
        qfields.append(QuestionWithOneField(xstring(xstringname),
                                            fieldRef(strnum(QPREFIX, i))));
    }

    QVector<QuElement*> elements = {
        (new QuText(xstring("stem")))->setBold(true),
        (new QuText(xstring("instruction")))->setBold(true),
    };

    elements.append((new QuMcqGrid(qfields, options))
                    ->setExpand(true)
                    ->showTitle(false)
                    ->setSubtitles(subtitles)
);
    QuPagePtr page((new QuPage(elements))
                   ->setTitle(xstring("title_main")));

    /*
    QuPagePtr page((new QuPage{
        (new QuMcqGrid(
            {
                QuestionWithOneField(xstring("q1"), fieldRef("q1")),
            },
            options
        ))
            ->setTitle(xstring("section_physical"))
            ->setExpand(true),
        (new QuMcqGrid(
            {
                QuestionWithOneField(xstring("q1"), fieldRef("q1")),
            },
            options
        ))
            ->setTitle(xstring("section_social"))
            ->setExpand(true),
    })->setTitle(xstring("title_main")));
*/


    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Factg::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


int Factg::nQuestionsCompleted() const
{
    return countNotNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


double Factg::clinicalScore() const
{
    return static_cast<double>(N_QUESTIONS * totalScore()) /
            static_cast<double>(nQuestionsCompleted());
}
