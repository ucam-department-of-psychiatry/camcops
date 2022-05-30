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

#include "edeq.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 28;
const QString QPREFIX("q");


const QString Edeq::EDEQ_TABLENAME("edeq");


void initializeEdeq(TaskFactory& factory)
{
    static TaskRegistrar<Edeq> registered(factory);
}

Edeq::Edeq(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, EDEQ_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}
// ============================================================================
// Class info
// ============================================================================

QString Edeq::shortname() const
{
    return "EDE-Q";
}


QString Edeq::longname() const
{
    return tr("Eating Disorder Examination Questionnaire");
}


QString Edeq::description() const
{
    return tr("A self-report version of the Eating Disorder Examination (EDE)");
}


QStringList Edeq::fieldNames() const
{
    return strseq(QPREFIX, FIRST_Q, N_QUESTIONS);
}

// ============================================================================
// Instance info
// ============================================================================


bool Edeq::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}


QStringList Edeq::summary() const
{
    return QStringList{};
}


QStringList Edeq::detail() const
{
    QStringList lines;

    return lines;
}


OpenableWidget* Edeq::editor(const bool read_only)
{
    const NameValueOptions days_options{
        {xstring("days_option_0"), 0},
        {xstring("days_option_1"), 1},
        {xstring("days_option_2"), 2},
        {xstring("days_option_3"), 3},
        {xstring("days_option_4"), 4},
        {xstring("days_option_5"), 5},
        {xstring("days_option_6"), 6},
    };

    const NameValueOptions freq_options{
        {xstring("freq_option_0"), 0},
        {xstring("freq_option_1"), 1},
        {xstring("freq_option_2"), 2},
        {xstring("freq_option_3"), 3},
        {xstring("freq_option_4"), 4},
        {xstring("freq_option_5"), 5},
        {xstring("freq_option_6"), 6},
    };

    const NameValueOptions how_much_options{
        {xstring("how_much_option_0"), 0},
        {xstring("how_much_option_1"), 1},
        {xstring("how_much_option_2"), 2},
        {xstring("how_much_option_3"), 3},
        {xstring("how_much_option_4"), 4},
        {xstring("how_much_option_5"), 5},
        {xstring("how_much_option_6"), 6},
    };


    auto grid1_12 = buildGrid(1, 12, days_options);
    auto grid19 = buildGrid(19, 19, days_options);
    auto grid20 = buildGrid(20, 20, freq_options);
    auto grid21 = buildGrid(21, 21, how_much_options);
    auto grid22_28 = buildGrid(22, 28, how_much_options);


    QuPagePtr page((new QuPage{
                grid1_12,
                    grid19,
                    grid20,
                    grid21,
                    grid22_28
                    })->setTitle(xstring("title_main")));

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}


QuMcqGrid* Edeq::buildGrid(int first_qnum,
                           int last_qnum,
                           const NameValueOptions options)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
        const QString& fieldname = "q" + QString::number(qnum);
        const QString& description = xstring(fieldname);

        q_field_pairs.append(QuestionWithOneField(description,
                                                  fieldRef(fieldname)));

    }

    auto grid = new QuMcqGrid(q_field_pairs, options);

    // Repeat options every five lines
    QVector<McqGridSubtitle> subtitles{
        {5, ""},
        {10, ""},
        {15, ""},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);

    return grid;
}
