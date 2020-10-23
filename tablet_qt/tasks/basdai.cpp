/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include "basdai.h"
#include "common/textconst.h"
#include "common/uiconst.h"
#include "maths/mathfunc.h"
#include "lib/convert.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quslider.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_SCORE_A_QUESTIONS = 4;
const int N_QUESTIONS = 6;
const QString QPREFIX("q");

const int DP = 1;

const QString Basdai::BASDAI_TABLENAME("basdai");


void initializeBasdai(TaskFactory& factory)
{
    static TaskRegistrar<Basdai> registered(factory);
}


Basdai::Basdai(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, BASDAI_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Basdai::shortname() const
{
    return "BASDAI";
}


QString Basdai::longname() const
{
    return tr("Bath Ankylosing Spondylitis Disease Activity Index");
}


QString Basdai::description() const
{
    return tr(
        "A self-administered instrument for assessing disease activity in "
        "Ankylosing Spondylitis"
     );
}


QStringList Basdai::fieldNames() const
{
    return strseq(QPREFIX, FIRST_Q, N_QUESTIONS);
}


QStringList Basdai::scoreAFieldNames() const
{
    return strseq(QPREFIX, FIRST_Q, N_SCORE_A_QUESTIONS);
}


// ============================================================================
// Instance info
// ============================================================================

bool Basdai::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}


QVariant Basdai::basdai() const
{
    // Calculating the BASDAI:
    // A. Add scores for questions 1 – 4
    // B. Calculate the mean for questions 5 and 6
    // C. Add A and B and divide by 5

    // The higher the BASDAI score, the more severe the patient’s disability
    // due to their AS.

    const double a = mathfunc::sumDouble(values(scoreAFieldNames()));
    const double b = mathfunc::mean(
        value("q5").toDouble(),
        value("q6").toDouble()
    );

    return (a + b) / 5;
}


QStringList Basdai::summary() const
{
    return QStringList{
        QString("%1: %2").arg(xstring("basdai"),
                              convert::prettyValue(basdai(), DP))
    };
}


QStringList Basdai::detail() const
{
    QStringList lines = completenessInfo();
    const QString spacer = " ";
    const QString suffix = "";
    lines += fieldSummaries("q", suffix, spacer, QPREFIX, FIRST_Q, N_QUESTIONS);
    lines.append("");
    lines += summary();

    return lines;
}


OpenableWidget* Basdai::editor(const bool read_only)
{
    QuPagePtr page((new QuPage{
                new QuText(xstring("instructions"))
            })->setTitle(xstring("title_main")));

    auto slider_grid = new QuGridContainer();
    slider_grid->setExpandHorizontally(false);
    slider_grid->setFixedGrid(false);

    page->addElement(slider_grid);

    const int QUESTION_ROW_SPAN = 1;
    const int QUESTION_COLUMN_SPAN = 3;

    int row = 0;

    for (const QString& fieldname : fieldNames()) {
        QuSlider* slider = new QuSlider(fieldRef(fieldname), 0, 10, 1);
        slider->setUseDefaultTickLabels(true);
        slider->setHorizontal(true);
        slider->setBigStep(1);

        const bool can_shrink = true;
        slider->setAbsoluteLengthCm(10, can_shrink);

        slider->setTickInterval(1);
        slider->setTickLabelPosition(QSlider::TicksAbove);

        slider->setShowValue(false);
        slider->setSymmetric(true);

        const auto question_text = new QuText(xstring(fieldname));
        slider_grid->addCell(QuGridCell(question_text, row, 0,
                                        QUESTION_ROW_SPAN, QUESTION_COLUMN_SPAN));
        row++;

        const auto min_label = new QuText(xstring(fieldname + "_min"));
        min_label->setTextAlignment(Qt::AlignRight | Qt::AlignVCenter);
        const auto max_label = new QuText(xstring(fieldname + "_max"));
        slider_grid->addCell(QuGridCell(min_label, row, 0));
        slider_grid->addCell(QuGridCell(slider, row, 1));
        slider_grid->addCell(QuGridCell(max_label, row, 2));

        row++;

        slider_grid->addCell(QuGridCell(new QuSpacer(QSize(uiconst::BIGSPACE,
                                                           uiconst::BIGSPACE)), row, 0));

        row++;

    }

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}
