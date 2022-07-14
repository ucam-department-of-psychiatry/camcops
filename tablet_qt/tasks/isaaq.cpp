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

#include "isaaq.h"
#include "common/textconst.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcqgrid.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_A_QUESTIONS = 15;
const int N_B_QUESTIONS = 10;
const int MIN_SCORE = 0;
const int MAX_SCORE = 5;
const QString A_PREFIX("a");
const QString B_PREFIX("b");


const QString Isaaq::ISAAQ_TABLENAME("isaaq");


void initializeIsaaq(TaskFactory& factory)
{
    static TaskRegistrar<Isaaq> registered(factory);
}

Isaaq::Isaaq(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, ISAAQ_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addFields(strseq(A_PREFIX, FIRST_Q, N_A_QUESTIONS), QVariant::Int);
    addFields(strseq(B_PREFIX, FIRST_Q, N_B_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}
// ============================================================================
// Class info
// ============================================================================

QString Isaaq::shortname() const
{
    return "ISAAQ";
}


QString Isaaq::longname() const
{
    return tr("Internet Severity and Activities Addiction Questionnaire (ISAAQ)");
}


QString Isaaq::description() const
{
    return tr("Internet Severity and Activities Addiction Questionnaire (ISAAQ)");
}


QStringList Isaaq::fieldNames() const
{
    auto field_names = strseq(A_PREFIX, FIRST_Q, N_A_QUESTIONS) + strseq(
        B_PREFIX, FIRST_Q, N_B_QUESTIONS);

    return field_names;
}

// ============================================================================
// Instance info
// ============================================================================


bool Isaaq::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}


QStringList Isaaq::summary() const
{
    // There are no scores or scales
    return QStringList{TextConst::noSummarySeeFacsimile()};
}


QStringList Isaaq::detail() const
{
    QStringList lines = completenessInfo();

    const QString spacer = " ";
    const QString suffix = "";

    const QStringList fieldnames = fieldNames();

    for (int i = 0; i < fieldnames.length(); ++i) {
        const QString& fieldname = fieldnames.at(i);
        lines.append(fieldSummary(fieldname, xstring(fieldname),
                                  spacer, suffix));
    }

    return lines;
}


OpenableWidget* Isaaq::editor(const bool read_only)
{
    NameValueOptions freq_options;

    for (int i = 0; i <= MAX_SCORE; i++) {
        auto freq_name = QString("freq_option_%1").arg(i);

        freq_options.append({xstring(freq_name), i});
    }

    const int freq_min_width_px = 100;
    const QVector<int> freq_min_option_widths_px = {100, 100, 100, 100, 100, 100};

    auto instructions = new QuHeading(xstring("instructions"));
    auto grid_a = buildGrid(A_PREFIX, FIRST_Q, N_A_QUESTIONS, freq_options,
                            xstring("a_title"));
    grid_a->setMinimumWidthInPixels(freq_min_width_px, freq_min_option_widths_px);
    auto grid_b_heading = new QuHeading(xstring("b_heading"));
    auto grid_b = buildGrid(B_PREFIX, FIRST_Q, N_B_QUESTIONS, freq_options,
                            xstring("b_title"));
    grid_b->setMinimumWidthInPixels(freq_min_width_px, freq_min_option_widths_px);

    QVector<QuElement*> elements{
                    instructions,
                    grid_a,
                    grid_b_heading,
                    grid_b
    };

    QuPagePtr page((new QuPage(elements))->setTitle(xstring("title")));

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}


QuMcqGrid* Isaaq::buildGrid(const QString prefix,
                            int first_qnum,
                            int last_qnum,
                            const NameValueOptions options,
                            const QString title)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
        const QString& fieldname = prefix + QString::number(qnum);
        const QString& description = xstring(fieldname);

        q_field_pairs.append(QuestionWithOneField(description,
                                                  fieldRef(fieldname)));

    }

    auto grid = new QuMcqGrid(q_field_pairs, options);
    grid->setTitle(title);
    // Repeat options every five lines
    QVector<McqGridSubtitle> subtitles{
        {5, title},
        {10, title},
        {15, title},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);
    grid->setQuestionsBold(false);

    return grid;
}
