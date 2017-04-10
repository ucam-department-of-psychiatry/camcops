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

#include "moca.h"
#include "lib/mathfunc.h"
#include "lib/stringfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using mathfunc::noneNull;
using mathfunc::scoreString;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 28;
const int MAX_SCORE = 30;
const QString QPREFIX("q");

const QString MOCA_TABLENAME("moca");

const QString IMAGE_PATH("moca/path.png");
const QString IMAGE_CUBE("moca/cube.png");
const QString IMAGE_CLOCK("moca/clock.png");
const QString IMAGE_ANIMALS("moca/animals.png");

const QString EDUCATION12Y_OR_LESS("education12y_or_less");
const QString TRAILPICTURE_BLOBID("trailpicture_blobid");
const QString CUBEPICTURE_BLOBID("cubepicture_blobid");
const QString CLOCKPICTURE_BLOBID("clockpicture_blobid");

const int N_REG_RECALL = 5;
const QString REGISTER_TRIAL1_PREFIX("register_trial1_");
const QString REGISTER_TRIAL2_PREFIX("register_trial2_");
const QString RECALL_CATEGORY_CUE_PREFIX("recall_category_cue_");
const QString RECALL_MC_CUE_PREFIX("recall_mc_cue_");

const QString COMMENTS("comments");


void initializeMoca(TaskFactory& factory)
{
    static TaskRegistrar<Moca> registered(factory);
}


Moca::Moca(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, MOCA_TABLENAME, false, true, false)  // ... anon, clin, resp
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Moca::shortname() const
{
    return "MoCA";
}


QString Moca::longname() const
{
    return tr("Montreal Cognitive Assessment");
}


QString Moca::menusubtitle() const
{
    return tr("30-point clinician-administered brief cognitive assessment.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Moca::isComplete() const
{
    return noneNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


QStringList Moca::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), MAX_SCORE)};
}


QStringList Moca::detail() const
{
    // *** am here
    QStringList lines = completenessInfo();
    lines += fieldSummaries("q", "_s", " ", QPREFIX, FIRST_Q, N_QUESTIONS);
    lines.append("");
    lines += summary();
    return lines;
}


OpenableWidget* Moca::editor(bool read_only)
{
    NameValuePair option0(xstring("option0"), 0);
    NameValuePair option1(xstring("option1"), 1);
    QVector<QuPagePtr> pages;

    // ***

    Questionnaire* questionnaire = new Questionnaire(m_app, pages);
    questionnaire->setType(QuPage::PageType::Clinician);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Moca::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS))) +
            valueInt(EDUCATION12Y_OR_LESS);  // extra point for this
}
