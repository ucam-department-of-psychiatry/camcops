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

#include "rapid3.h"

#include "lib/convert.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionwithonefield.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/quslider.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"

using mathfunc::anyNull;
using mathfunc::sumInt;

const int N_Q1_QUESTIONS = 13;
const int N_Q1_SCORING_QUESTIONS = 10;
const QString QPREFIX("q");
const QString Q2("q2");
const QString Q3("q3");

const int DP = 1;

const QString Rapid3::RAPID3_TABLENAME("rapid3");

void initializeRapid3(TaskFactory& factory)
{
    static TaskRegistrar<Rapid3> registered(factory);
}

Rapid3::Rapid3(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, RAPID3_TABLENAME, false, false, false),
    // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addFields(q1Fieldnames(), QMetaType::fromType<int>());
    addField(Q2, QMetaType::fromType<double>());
    addField(Q3, QMetaType::fromType<double>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

QStringList Rapid3::q1Fieldnames() const
{
    QStringList fieldnames;

    for (int i = 0; i < N_Q1_QUESTIONS; i++) {
        fieldnames.append(QPREFIX + "1" + QChar(i + 'a'));
    }

    return fieldnames;
}

QStringList Rapid3::q1ScoringFieldnames() const
{
    QStringList fieldnames;

    for (int i = 0; i < N_Q1_SCORING_QUESTIONS; i++) {
        fieldnames.append(QPREFIX + "1" + QChar(i + 'a'));
    }

    return fieldnames;
}

QStringList Rapid3::allFieldnames() const
{
    QStringList fieldnames = q1Fieldnames();

    fieldnames.append(Q2);
    fieldnames.append(Q3);

    return fieldnames;
}

// ============================================================================
// Class info
// ============================================================================

QString Rapid3::shortname() const
{
    return "RAPID3";
}

QString Rapid3::longname() const
{
    return tr("Routine Assessment of Patient Index Data");
}

QString Rapid3::description() const
{
    return tr(
        "A pooled index of patient-reported function, pain, and global "
        "estimate of status."
    );
}

// ============================================================================
// Instance info
// ============================================================================

bool Rapid3::isComplete() const
{
    if (anyNull(values(allFieldnames()))) {
        return false;
    }

    return true;
}

QVariant Rapid3::rapid3() const
{
    if (!isComplete()) {
        return QVariant();
    }

    return functionalStatus() + painTolerance() + globalEstimate();
}

double Rapid3::functionalStatus() const
{
    const int q1_sum = sumInt(values(q1ScoringFieldnames()));
    const double raw_formal_score = q1_sum / 3.0;
    const double rounded_score_1dp = qRound(raw_formal_score * 10.0) / 10.0;

    return rounded_score_1dp;
}

double Rapid3::painTolerance() const
{
    return value(Q2).toDouble();
}

double Rapid3::globalEstimate() const
{
    return value(Q3).toDouble();
}

QString Rapid3::diseaseSeverity() const
{
    const QVariant rapid3_variant = this->rapid3();

    if (rapid3_variant.isNull()) {
        return xstring("n_a");
    }

    const double rapid3 = rapid3_variant.toDouble();

    if (rapid3 <= 3.0) {
        return xstring("near_remission");
    }

    if (rapid3 <= 6.0) {
        return xstring("low_severity");
    }

    if (rapid3 <= 12.0) {
        return xstring("moderate_severity");
    }

    return xstring("high_severity");
}

QStringList Rapid3::summary() const
{
    using stringfunc::bold;

    return QStringList{QString("%1 [0–30]: %2 (%3)")
                           .arg(
                               xstring("rapid3"),
                               convert::prettyValue(rapid3(), DP),
                               bold(diseaseSeverity())
                           )};
}

QStringList Rapid3::detail() const
{
    QStringList lines = completenessInfo();
    const QString spacer = " ";
    const QString suffix = "";

    const QStringList fieldnames = allFieldnames();
    for (int i = 0; i < fieldnames.length(); i++) {
        const QString fieldname = fieldnames.at(i);
        lines.append(
            fieldSummary(fieldname, xstring(fieldname), spacer, suffix)
        );
    }
    lines.append("");
    lines += summary();

    return lines;
}

OpenableWidget* Rapid3::editor(const bool read_only)
{
    QuPagePtr page((new QuPage{
                        new QuText(xstring("q1")),
                        (new QuText(xstring("q1sub")))->setBold()})
                       ->setTitle(xstring("title_main")));

    const NameValueOptions difficulty_options{
        {xstring("q1_option0"), 0},
        {xstring("q1_option1"), 1},
        {xstring("q1_option2"), 2},
        {xstring("q1_option3"), 3},
    };

    QVector<QuestionWithOneField> q_field_pairs;

    const auto q1fieldnames = q1Fieldnames();
    for (const QString& fieldname : q1fieldnames) {
        const QString& description = xstring(fieldname);
        q_field_pairs.append(
            QuestionWithOneField(description, fieldRef(fieldname))
        );
    }
    auto q1_grid = new QuMcqGrid(q_field_pairs, difficulty_options);
    page->addElement(q1_grid);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1};
    q1_grid->setWidth(question_width, option_widths);

    // Repeat options every five lines
    const QVector<McqGridSubtitle> subtitles{
        {5, ""},
        {10, ""},
    };
    q1_grid->setSubtitles(subtitles);

    auto slider_grid = new QuGridContainer();
    slider_grid->setExpandHorizontally(false);
    slider_grid->setFixedGrid(false);

    page->addElement(slider_grid);

    const int QUESTION_ROW_SPAN = 1;
    const int QUESTION_COLUMN_SPAN = 3;

    int row = 0;

    const QStringList sliderFieldnames = {Q2, Q3};

    QMap<int, QString> tick_labels;

    for (int i = 0; i <= 20; i++) {
        tick_labels[i] = QString::number(i / 2.0);
    }

    for (const QString& fieldname : sliderFieldnames) {
        QuSlider* slider = new QuSlider(fieldRef(fieldname), 0, 20, 1);
        slider->setHorizontal(true);
        slider->setBigStep(1);
        slider->setConvertForRealField(true, 0, 10);

        const bool can_shrink = true;
        slider->setAbsoluteLengthCm(20, can_shrink);

        slider->setTickInterval(1);

        slider->setTickLabels(tick_labels);
        slider->setTickLabelPosition(QSlider::TicksAbove);

        slider->setShowValue(false);
        slider->setSymmetric(true);

        const auto question_text = (new QuText(xstring(fieldname)))->setBold();
        slider_grid->addCell(QuGridCell(
            question_text, row, 0, QUESTION_ROW_SPAN, QUESTION_COLUMN_SPAN
        ));
        row++;

        const auto min_label = new QuText(xstring(fieldname + "_min"));
        min_label->setTextAlignment(Qt::AlignRight | Qt::AlignVCenter);
        const auto max_label = new QuText(xstring(fieldname + "_max"));
        slider_grid->addCell(QuGridCell(min_label, row, 0));
        slider_grid->addCell(QuGridCell(slider, row, 1));
        slider_grid->addCell(QuGridCell(max_label, row, 2));

        row++;

        slider_grid->addCell(QuGridCell(
            new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE)), row, 0
        ));

        row++;
    }

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}
