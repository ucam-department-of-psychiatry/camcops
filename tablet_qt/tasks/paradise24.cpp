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

#include "paradise24.h"

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
using mathfunc::meanOrNull;
using mathfunc::sumInt;
using stringfunc::strnumlist;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int LAST_Q = 24;
const int MIN_QUESTION_SCORE = 0;
const int MAX_QUESTION_SCORE = 2;
const int MIN_RAW_TOTAL_SCORE = 0;
const int MAX_RAW_TOTAL_SCORE = 48;
const int MIN_METRIC_SCORE = 0;
const int MAX_METRIC_SCORE = 100;

const QString Q_PREFIX("q");
const QString Paradise24::PARADISE24_TABLENAME("paradise24");

void initializeParadise24(TaskFactory& factory)
{
    static TaskRegistrar<Paradise24> registered(factory);
}

Paradise24::Paradise24(
    CamcopsApp& app, DatabaseManager& db, const int load_pk
) :
    Task(app, db, PARADISE24_TABLENAME, false, false, false)
// ... anon, clin, resp
{
    addFields(strseq(Q_PREFIX, FIRST_Q, LAST_Q), QMetaType::fromType<int>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Paradise24::shortname() const
{
    return "PARADISE 24";
}

QString Paradise24::longname() const
{
    return tr("Psychosocial fActors Relevant to BrAin DISorders in Europe–24");
}

QString Paradise24::description() const
{
    return tr(
        "A measure to assess the the impact of brain disorders on people’s "
        "lives, based on psychosocial difficulties that are experienced in "
        "common across brain disorders."
    );
}

QStringList Paradise24::fieldNames() const
{
    auto field_names = strseq(Q_PREFIX, FIRST_Q, LAST_Q);

    return field_names;
}

// ============================================================================
// Instance info
// ============================================================================


bool Paradise24::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}

QVariant Paradise24::rawTotalScore() const
{
    if (!isComplete()) {
        return QVariant();
    }

    return sumInt(values(fieldNames()));
}

QVariant Paradise24::metricScore() const
{
    auto total_score = rawTotalScore();
    if (total_score.isNull()) {
        return QVariant();
    }

    // Table 3 of Cieza et al. (2015); see help.
    // - doi:10.1371/journal.pone.0132410.t003
    // - Indexes are raw scores.
    // - Values are transformed scores.
    const QVector<int> score_lookup = {
        0,  // 0
        10,  19, 25, 29, 33, 36, 38, 41, 43,
        45,  // 10
        46,  48, 50, 51, 53, 54, 55, 57, 58,
        59,  // 20
        60,  61, 63, 64, 65, 66, 67, 68, 69,
        71,  // 30
        72,  73, 74, 76, 77, 78, 80, 81, 83,
        85,  // 40
        87,  89, 91, 92, 94, 96, 98,
        100,  // 48
    };

    return score_lookup[total_score.toInt()];
}

QStringList Paradise24::summary() const
{
    auto rangeScore = [](const QString& description,
                         const QVariant score,
                         const int min,
                         const int max) {
        return QString("%1: <b>%2</b> [%3–%4].")
            .arg(
                description,
                convert::prettyValue(score),
                QString::number(min),
                QString::number(max)
            );
    };
    return QStringList{
        rangeScore(
            xstring("raw_score"),
            rawTotalScore(),
            MIN_RAW_TOTAL_SCORE,
            MAX_RAW_TOTAL_SCORE
        ),
        rangeScore(
            xstring("metric_score"),
            metricScore(),
            MIN_METRIC_SCORE,
            MAX_METRIC_SCORE
        ),
    };
}

QStringList Paradise24::detail() const
{
    QStringList lines = completenessInfo();

    const QString spacer = " ";
    const QString suffix = "";

    const QStringList fieldnames = fieldNames();

    for (int i = 0; i < fieldnames.length(); ++i) {
        const QString& fieldname = fieldnames.at(i);
        lines.append(
            fieldSummary(fieldname, xstring(fieldname), spacer, suffix)
        );
    }


    lines.append("");
    lines += summary();

    return lines;
}

OpenableWidget* Paradise24::editor(const bool read_only)
{
    NameValueOptions options;

    for (int i = MIN_QUESTION_SCORE; i <= MAX_QUESTION_SCORE; ++i) {
        auto name = QString("option_%1").arg(i);

        options.append({xstring(name), i});
    }

    const int min_width_px = 100;
    const QVector<int> min_option_widths_px = {50, 50, 50};

    auto instructions = new QuHeading(xstring("instructions"));
    auto grid = buildGrid(FIRST_Q, LAST_Q, options);
    grid->setMinimumWidthInPixels(min_width_px, min_option_widths_px);

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

QuMcqGrid* Paradise24::buildGrid(
    int first_qnum, int last_qnum, const NameValueOptions options
)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
        const QString& fieldname = Q_PREFIX + QString::number(qnum);
        const QString& description = xstring(fieldname);

        q_field_pairs.append(
            QuestionWithOneField(description, fieldRef(fieldname))
        );
    }

    auto grid = new QuMcqGrid(q_field_pairs, options);
    // Repeat options every six lines
    QVector<McqGridSubtitle> subtitles{
        {6, ""},
        {12, ""},
        {18, ""},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1};
    grid->setWidth(question_width, option_widths);
    grid->setQuestionsBold(false);

    return grid;
}
