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

#include "bdi.h"
#include "lib/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionwithonefield.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using mathfunc::noneNull;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 21;
const int MAX_SCORE = N_QUESTIONS * 3;
const QString QPREFIX("q");

const QString BDI_TABLENAME("bdi");
const QString FN_BDI_SCALE("bdi_scale");

const QString SCALE_BDI_I("BDI-I");
const QString SCALE_BDI_IA("BDI-IA");
const QString SCALE_BDI_II("BDI-II");


void initializeBdi(TaskFactory& factory)
{
    static TaskRegistrar<Bdi> registered(factory);
}


Bdi::Bdi(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, BDI_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addField(FN_BDI_SCALE, QVariant::String);
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Bdi::shortname() const
{
    return "BDI";
}


QString Bdi::longname() const
{
    return tr("Beck Depression Inventory (¶)");
}


QString Bdi::menusubtitle() const
{
    return tr("21-item self-report scale. Data collection tool ONLY "
              "(for BDI, BDI-1A, BDI-II).");
}


// ============================================================================
// Instance info
// ============================================================================

bool Bdi::isComplete() const
{
    return noneNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


QStringList Bdi::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), MAX_SCORE)};
}


QStringList Bdi::detail() const
{
    return summary() + completenessInfo();
}


OpenableWidget* Bdi::editor(bool read_only)
{
    NameValueOptions options{
        {"0", 0},
        {"1", 1},
        {"2", 2},
        {"3", 3},
    };
    NameValueOptions scale_options{
        {"BDI (1961; BDI-I)", SCALE_BDI_I},
        {"BDI-IA (1978)", SCALE_BDI_IA},
        {"BDI-II (1996)", SCALE_BDI_II},
    };
    QList<QuestionWithOneField> fields;
    QString question_prefix = tr("Question");
    for (int n = FIRST_Q; n <= N_QUESTIONS; ++n) {
        QString qstrnum = QString::number(n);
        QString fieldname = QPREFIX + qstrnum;
        QString question = question_prefix + " " + qstrnum;
        fields.append(QuestionWithOneField(fieldRef(fieldname), question));
    }

    if (valueIsNullOrEmpty(FN_BDI_SCALE)) {
        // first edit; set default
        setValue(FN_BDI_SCALE, SCALE_BDI_II);
    }

    QuPagePtr page((new QuPage({
        (new QuText(appstring("data_collection_only")))->setBold(),
        new QuText(appstring("bdi_which_scale")),
        (new QuMcq(fieldRef(FN_BDI_SCALE), scale_options))
            ->setHorizontal(true)
            ->setAsTextButton(true),
        new QuText(appstring("enter_the_answers")),
        new QuMcqGrid(fields, options),
    }))->setTitle(shortname()));

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Bdi::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}
