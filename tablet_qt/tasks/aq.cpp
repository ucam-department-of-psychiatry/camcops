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

#include "aq.h"
#include "db/databaseobject.h"
#include "lib/convert.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcqgrid.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using mathfunc::anyNull;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int LAST_Q = 50;
const int FIRST_OPTION = 0;
const int LAST_OPTION = 3;
const int MIN_SCORE = 0;
const int MAX_SCORE = 50;

const QString Q_PREFIX("q");
const QString Aq::AQ_TABLENAME("aq");


void initializeAq(TaskFactory& factory)
{
    static TaskRegistrar<Aq> registered(factory);
}

Aq::Aq(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, AQ_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(Q_PREFIX, FIRST_Q, LAST_Q), QMetaType::fromType<int>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Aq::shortname() const
{
    return "AQ";
}


QString Aq::longname() const
{
    return tr("The Adult Autism Spectrum Quotient");
}


QString Aq::description() const
{
    return tr(
        "A 50 item self-report measure used to assess traits of autism in "
        "adults and adolescents aged 16 years and over."
    );
}


QStringList Aq::fieldNames() const
{
    auto field_names = strseq(Q_PREFIX, FIRST_Q, LAST_Q);

    return field_names;
}

// ============================================================================
// Instance info
// ============================================================================


bool Aq::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}


QVariant Aq::score() const
{
    if (!isComplete()) {
        return QVariant();
    }

    const QVector<int> agree_options = {0, 1};
    const QVector<int> agree_scoring_questions = {
        2,
        4,
        5,
        6,
        7,
        9,
        12,
        13,
        16,
        18,
        19,
        20,
        21,
        22,
        23,
        26,
        33,
        35,
        39,
        41,
        42,
        43,
        45,
        46,
    };

    int total = 0;

    for (int qnum = FIRST_Q; qnum < LAST_Q; ++qnum) {
        const QString& fieldname = Q_PREFIX + QString::number(qnum);
        const int answer = valueInt(fieldname);
        const bool agree_scored = agree_scoring_questions.contains(qnum) &&
            agree_options.contains(answer);
        const bool disagree_scored = !agree_scoring_questions.contains(qnum) &&
            !agree_options.contains(answer);

        if (agree_scored or disagree_scored) {
            total++;
        }
    }

    return total;
}


QStringList Aq::summary() const
{
    auto rangeScore = [](const QString& description, const QVariant score,
                         const int min, const int max) {
        return QString("%1: <b>%2</b> [%3–%4].").arg(
                    description,
                    convert::prettyValue(score),
                    QString::number(min),
                    QString::number(max));
    };
    return QStringList{
        rangeScore(xstring("score"), score(), MIN_SCORE, MAX_SCORE),
    };
}


QStringList Aq::detail() const
{
    QStringList lines = completenessInfo();

    const QString altname = "";
    const QString spacer = " ";
    const QString suffix = "";

    const QStringList fieldnames = fieldNames();

    NameValueOptions* options = buildOptions();

    for (int i = 0; i < fieldnames.length(); ++i) {
        const QString& fieldname = fieldnames.at(i);
        lines.append(fieldSummaryNameValueOptions(
                         fieldname, *options,
                         altname, spacer, suffix)
        );
    }


    lines.append("");
    lines += summary();

    return lines;
}


OpenableWidget* Aq::editor(const bool read_only)
{
    auto options = buildOptions();

    const int min_width_px = 100;
    const QVector<int> min_option_widths_px = {50, 50, 50, 50};

    auto instructions = new QuHeading(xstring("instructions"));
    auto grid = buildGrid(FIRST_Q, LAST_Q, options);
    grid->setMinimumWidthInPixels(min_width_px,
                                  min_option_widths_px);

    QVector<QuElement*> elements{
        instructions,
        grid,
    };

    QuPagePtr page((new QuPage(elements))->setTitle(xstring("title")));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);

    return questionnaire;
}


NameValueOptions* Aq::buildOptions() const
{
    NameValueOptions* options = new NameValueOptions();

    for (int i = FIRST_OPTION; i <= LAST_OPTION; ++i) {
        auto name = QString("option_%1").arg(i);

        options->append({xstring(name), i});
    }

    return options;
}

QuMcqGrid* Aq::buildGrid(int first_qnum,
                         int last_qnum,
                         NameValueOptions* options)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
        const QString& fieldname = Q_PREFIX + QString::number(qnum);
        const QString& description = xstring(fieldname);

        q_field_pairs.append(QuestionWithOneField(description,
                                                  fieldRef(fieldname)));
    }

    auto grid = new QuMcqGrid(q_field_pairs, *options);
    // Repeat options every five lines
    QVector<McqGridSubtitle> subtitles{
        {5, ""},
        {10, ""},
        {15, ""},
        {20, ""},
        {25, ""},
        {30, ""},
        {35, ""},
        {40, ""},
        {45, ""},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);
    grid->setQuestionsBold(false);

    return grid;
}
