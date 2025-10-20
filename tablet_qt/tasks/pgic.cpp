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

#include "pgic.h"

#include "common/uiconst.h"
#include "lib/convert.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
#include "db/fieldref.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/qumcq.h"
using mathfunc::anyNull;
using mathfunc::meanOrNull;
using stringfunc::strseq;

const QString FN_QUESTION("question");
const QString Pgic::PGIC_TABLENAME("pgic");

void initializePgic(TaskFactory& factory)
{
    static TaskRegistrar<Pgic> registered(factory);
}

Pgic::Pgic(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, PGIC_TABLENAME, false, false, false)
// ... anon, clin, resp
{
    addField(FN_QUESTION, QMetaType::fromType<int>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Pgic::shortname() const
{
    return "PGIC";
}

QString Pgic::longname() const
{
    return tr("Patient Global Impression of Change");
}

QString Pgic::description() const
{
    return tr(
        "A 1 item self-report assessment tool designed to measure if there "
        "has been an improvement or decline in clinical status."
    );
}

// ============================================================================
// Instance info
// ============================================================================


bool Pgic::isComplete() const
{
    if (valueIsNull(FN_QUESTION)) {
        return false;
    }

    return true;
}

QStringList Pgic::detail() const
{
    QStringList lines = completenessInfo();

    lines.append("");
    lines += summary();

    return lines;
}

QStringList Pgic::summary() const

{
    QStringList lines;

    const QString fmt = QString("%1: <b>%2</b> %3<br>");
    const int answer = valueInt(FN_QUESTION);
    const QString answer_str = answer ? QString::number(valueInt(FN_QUESTION)) : "?";
    const QString answer_def = answer ? xstring("a" + answer_str) : "";

    lines.append(fmt.arg(
        xstring(FN_QUESTION),
        answer_str,
        answer_def
    ));

    return lines;

}

OpenableWidget* Pgic::editor(const bool read_only)
{
    // Question text at top
    auto question_text = new QuText(xstring("question"));

    // Show the labels (1..7) as readable text rows
    QVector<QuElement*> elements;
    elements.append(question_text);

    const NameValueOptions options = {
        {xstring("a1"), 1},
        {xstring("a2"), 2},
        {xstring("a3"), 3},
        {xstring("a4"), 4},
        {xstring("a5"), 5},
        {xstring("a6"), 6},
        {xstring("a7"), 7},
    };

    // Numeric entry (constrained) shown below the labels
    elements.append(new QuMcq(fieldRef(FN_QUESTION), options));

    QuPagePtr page((new QuPage(elements))->setTitle(xstring("title")));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);

    return questionnaire;
}
